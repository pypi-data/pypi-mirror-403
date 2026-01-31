"""LangGraph adapter helpers for integrating Baguette into graph runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    Iterator,
    Optional,
    Protocol,
)
import asyncio
import threading
import time
import uuid

from .sdk import AdapterContext, AdapterHooks, AdapterPipeline
from ..api import validate_with_pipeline
from ..audit import DecisionTrace
from ..memory import (
    MemoryEntry,
    TX_COMMITTED,
    TX_ROLLED_BACK,
    TX_SCOPE_RUN,
    TX_SCOPE_SUBGRAPH,
    ValidationPipeline,
    ValidationRecord,
)
from ..storage.base import StorageBackend


class LangGraphAdapterError(RuntimeError):
    pass


LANGGRAPH_CONTEXT_KEY = "_baguette"
LANGGRAPH_CONTEXT_TOKEN_KEY = "_baguette_tx_id"
LANGGRAPH_EDGE_PATH_KEY = "_baguette_edge_path"
LANGGRAPH_CORRELATION_ID_KEY = "correlation_id"
LANGGRAPH_NODE_TRACE_DECISION = "graph.node"
LANGGRAPH_GRAPH_TRACE_DECISION = "graph.run"
LANGGRAPH_ERROR_TRACE_DECISION = "graph.error"
LANGGRAPH_METRIC_MEMORY_STAGED = "baguette.memory.staged"
LANGGRAPH_METRIC_TX_COMMITTED = "baguette.tx.committed"
LANGGRAPH_METRIC_TX_ROLLED_BACK = "baguette.tx.rolled_back"


def _default_correlation_id() -> str:
    return str(uuid.uuid4())


class MetricsHook(Protocol):
    def increment(
        self,
        name: str,
        value: int = 1,
        *,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        ...

NodeFn = Callable[[Dict[str, Any], "LangGraphContext"], Optional[Dict[str, Any]]]
AsyncNodeFn = Callable[
    [Dict[str, Any], "LangGraphContext"], Awaitable[Optional[Dict[str, Any]]]
]


@dataclass
class LangGraphContext:
    storage: StorageBackend
    tx_id: str
    actor: str
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    lineage: Dict[str, Any] = field(default_factory=dict)

    def adapter_context(self) -> AdapterContext:
        return AdapterContext(
            storage=self.storage,
            tx_id=self.tx_id,
            actor=self.actor,
            metadata=self.metadata,
        )


@dataclass
class _RunState:
    active_nodes: int = 0
    lock: threading.RLock = field(default_factory=threading.RLock)
    quiescent: threading.Condition = field(init=False)

    def __post_init__(self) -> None:
        self.quiescent = threading.Condition(self.lock)

    def enter(self) -> None:
        with self.lock:
            self.active_nodes += 1

    def exit(self) -> None:
        with self.lock:
            self.active_nodes = max(0, self.active_nodes - 1)
            self.quiescent.notify_all()


def merge_context(
    left: Optional[LangGraphContext],
    right: Optional[LangGraphContext],
) -> Optional[LangGraphContext]:
    if left is None:
        return right
    if right is None:
        return left
    if not isinstance(left, LangGraphContext) or not isinstance(right, LangGraphContext):
        raise LangGraphAdapterError("LangGraph merge received invalid context objects.")
    if left.tx_id != right.tx_id:
        raise LangGraphAdapterError(
            "LangGraph branch merge detected mismatched transaction contexts."
        )
    return left


def merge_context_token(left: Optional[str], right: Optional[str]) -> Optional[str]:
    if not left:
        return right
    if not right:
        return left
    if not isinstance(left, str) or not isinstance(right, str):
        raise LangGraphAdapterError("LangGraph merge received invalid context tokens.")
    if left != right:
        raise LangGraphAdapterError(
            "LangGraph branch merge detected mismatched transaction tokens."
        )
    return left


class LangGraphAdapter:
    """Baguette adapter for LangGraph nodes using a shared run context."""

    def __init__(
        self,
        storage: StorageBackend,
        *,
        context_key: str = LANGGRAPH_CONTEXT_KEY,
        context_token_key: str = LANGGRAPH_CONTEXT_TOKEN_KEY,
        edge_path_key: str = LANGGRAPH_EDGE_PATH_KEY,
        pipeline: Optional[AdapterPipeline] = None,
        default_validation: Optional[ValidationPipeline] = None,
        memory_injection: Optional["AdapterHooks"] = None,
        trace_nodes: bool = False,
        trace_graph: bool = False,
        trace_errors: bool = True,
        trace_edge_path: bool = True,
        node_trace_decision: str = LANGGRAPH_NODE_TRACE_DECISION,
        graph_trace_decision: str = LANGGRAPH_GRAPH_TRACE_DECISION,
        serialize_storage: bool = True,
        enforce_quiescent_finalize: bool = True,
        tx_scope: str = TX_SCOPE_RUN,
        metrics_hook: Optional[MetricsHook] = None,
        correlation_id_factory: Optional[Callable[[], str]] = None,
    ) -> None:
        self.storage = storage
        self.context_key = context_key
        self.context_token_key = context_token_key
        self.edge_path_key = edge_path_key
        self.pipeline = pipeline or AdapterPipeline()
        if memory_injection is not None:
            self.pipeline.register(memory_injection)
        self.default_validation = default_validation
        self.trace_nodes = trace_nodes
        self.trace_graph = trace_graph
        self.trace_errors = trace_errors
        self.trace_edge_path = trace_edge_path
        self.node_trace_decision = node_trace_decision
        self.graph_trace_decision = graph_trace_decision
        self.serialize_storage = serialize_storage
        self.enforce_quiescent_finalize = enforce_quiescent_finalize
        self.tx_scope = self._validate_tx_scope(tx_scope)
        self.metrics_hook = metrics_hook
        self._correlation_id_factory = correlation_id_factory or _default_correlation_id
        self._context_registry: Dict[str, LangGraphContext] = {}
        self._registry_lock = threading.RLock()
        self._storage_lock = threading.RLock()
        self._run_states: Dict[str, _RunState] = {}
        self._run_state_lock = threading.RLock()

    def start_context(
        self,
        *,
        actor: str,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
        lineage: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        tx_scope: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> LangGraphContext:
        resolved_lineage = dict(lineage or {})
        if "tx_scope" not in resolved_lineage:
            resolved_lineage["tx_scope"] = self._validate_tx_scope(tx_scope or self.tx_scope)
        if correlation_id:
            resolved_lineage[LANGGRAPH_CORRELATION_ID_KEY] = correlation_id
        elif LANGGRAPH_CORRELATION_ID_KEY not in resolved_lineage:
            resolved_lineage[LANGGRAPH_CORRELATION_ID_KEY] = self._correlation_id_factory()
        tx_id = self.storage.begin_transaction(
            actor=actor,
            reason=reason,
            metadata=metadata,
            idempotency_key=idempotency_key,
            lineage=resolved_lineage,
        )
        context = LangGraphContext(
            storage=self.storage,
            tx_id=tx_id,
            actor=actor,
            reason=reason,
            metadata=metadata or {},
            lineage=resolved_lineage,
        )
        self._register_context(context)
        return context

    def attach_context(self, state: Dict[str, Any], context: LangGraphContext) -> None:
        self._register_context(context)
        state[self.context_key] = context
        state[self.context_token_key] = context.tx_id

    def get_context(self, state: Dict[str, Any]) -> LangGraphContext:
        context = state.get(self.context_key)
        token = state.get(self.context_token_key)

        if context is not None:
            if not isinstance(context, LangGraphContext):
                raise LangGraphAdapterError(
                    f"LangGraph state has invalid LangGraphContext at key '{self.context_key}'."
                )
            if token is not None and token != context.tx_id:
                raise LangGraphAdapterError(
                    "LangGraph state context token does not match context tx_id."
                )
            self._register_context(context)
            return context

        if token is None:
            raise LangGraphAdapterError(
                f"LangGraph state missing LangGraphContext at key '{self.context_key}'."
            )
        if not isinstance(token, str) or not token.strip():
            raise LangGraphAdapterError(
                f"LangGraph state has invalid context token at key '{self.context_token_key}'."
            )
        context = self._lookup_context(token)
        if context is None:
            context = self._rehydrate_context(token)
        if context is None:
            raise LangGraphAdapterError(
                f"LangGraph context registry missing tx_id '{token}'."
            )
        state[self.context_key] = context
        return context

    def wrap_node(
        self,
        fn: NodeFn,
        *,
        name: Optional[str] = None,
        trace: Optional[bool] = None,
    ) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
        node_name = name or getattr(fn, "__name__", "node")
        trace_nodes = self.trace_nodes if trace is None else trace

        def _wrapped(state: Dict[str, Any]) -> Dict[str, Any]:
            context = self.get_context(state)
            self._enter_node(context)
            started = time.perf_counter()
            edge_path = self._resolve_edge_path(state, node_name)
            try:
                result = fn(state, context)
            except Exception as exc:
                if trace_nodes and self.trace_errors:
                    self._trace_node(
                        context,
                        node_name,
                        "error",
                        started,
                        exc,
                        state,
                        edge_path=edge_path,
                    )
                raise
            finally:
                self._exit_node(context)

            payload = self._prepare_node_update(
                result,
                context,
                include_context=True,
                include_token=True,
                drop_context=False,
                drop_token=False,
            )
            if edge_path is not None and self.edge_path_key:
                payload[self.edge_path_key] = edge_path
            if trace_nodes:
                self._trace_node(
                    context,
                    node_name,
                    "success",
                    started,
                    None,
                    state,
                    edge_path=edge_path,
                )
            return payload

        return _wrapped

    def wrap_node_async(
        self,
        fn: AsyncNodeFn,
        *,
        name: Optional[str] = None,
        trace: Optional[bool] = None,
    ) -> Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]:
        node_name = name or getattr(fn, "__name__", "node")
        trace_nodes = self.trace_nodes if trace is None else trace

        async def _wrapped(state: Dict[str, Any]) -> Dict[str, Any]:
            context = self.get_context(state)
            self._enter_node(context)
            started = time.perf_counter()
            edge_path = self._resolve_edge_path(state, node_name)
            try:
                result = await fn(state, context)
            except Exception as exc:
                if trace_nodes and self.trace_errors:
                    self._trace_node(
                        context,
                        node_name,
                        "error",
                        started,
                        exc,
                        state,
                        edge_path=edge_path,
                    )
                raise
            finally:
                self._exit_node(context)

            payload = self._prepare_node_update(
                result,
                context,
                include_context=True,
                include_token=True,
                drop_context=False,
                drop_token=False,
            )
            if edge_path is not None and self.edge_path_key:
                payload[self.edge_path_key] = edge_path
            if trace_nodes:
                self._trace_node(
                    context,
                    node_name,
                    "success",
                    started,
                    None,
                    state,
                    edge_path=edge_path,
                )
            return payload

        return _wrapped

    def _prepare_node_update(
        self,
        result: Optional[Dict[str, Any]],
        context: LangGraphContext,
        *,
        include_context: bool,
        include_token: bool,
        drop_context: bool,
        drop_token: bool,
    ) -> Dict[str, Any]:
        return self._normalize_payload(
            result,
            context,
            include_context=include_context,
            include_token=include_token,
            drop_context=drop_context,
            drop_token=drop_token,
        )

    def _normalize_payload(
        self,
        payload: Optional[Dict[str, Any]],
        context: LangGraphContext,
        *,
        include_context: bool,
        include_token: bool,
        drop_context: bool,
        drop_token: bool,
    ) -> Dict[str, Any]:
        data = {} if payload is None else payload
        if not isinstance(data, dict):
            raise LangGraphAdapterError("LangGraph node must return a dict or None.")
        merged = dict(data)

        existing_context = merged.get(self.context_key)
        existing_token = merged.get(self.context_token_key)

        if existing_context is not None and not isinstance(existing_context, LangGraphContext):
            raise LangGraphAdapterError("LangGraph state contains invalid context object.")

        if existing_token is not None and not isinstance(existing_token, str):
            raise LangGraphAdapterError("LangGraph state contains invalid context token.")

        if existing_context is not None and existing_context.tx_id != context.tx_id:
            raise LangGraphAdapterError(
                "LangGraph node returned a different transaction context than the active context."
            )
        if existing_token is not None and existing_token != context.tx_id:
            raise LangGraphAdapterError(
                "LangGraph state token does not match the active transaction context."
            )

        if drop_context:
            merged.pop(self.context_key, None)
        if drop_token:
            merged.pop(self.context_token_key, None)

        if include_context:
            merged[self.context_key] = context
        if include_token:
            merged[self.context_token_key] = context.tx_id

        self._register_context(context)
        return merged

    def _trace_node(
        self,
        context: LangGraphContext,
        node_name: str,
        status: str,
        started: float,
        error: Optional[Exception],
        state: Optional[Dict[str, Any]],
        *,
        edge_path: Optional[list[str]] = None,
    ) -> None:
        duration_ms = int((time.perf_counter() - started) * 1000)
        metadata: Dict[str, Any] = {
            "node": node_name,
            "status": status,
            "duration_ms": duration_ms,
        }
        if state is not None:
            metadata["state_keys"] = self._trace_state_keys(state)
        if edge_path:
            metadata["edge_path"] = edge_path
            metadata["edge_to"] = edge_path[-1]
            if len(edge_path) > 1:
                metadata["edge_from"] = edge_path[-2]
        if error:
            metadata["error"] = str(error)
            metadata["exception"] = repr(error)
        confidence = 1.0 if status == "success" else 0.0
        self.trace(
            context,
            decision=self.node_trace_decision,
            skill_ref=None,
            reason=f"LangGraph node {node_name}",
            confidence=confidence,
            result=status,
            metadata=metadata,
        )

    def stage_entries(self, context: LangGraphContext, entries: Iterable[MemoryEntry]) -> None:
        entry_list = list(entries)
        if not entry_list:
            return
        self.pipeline.on_write(entry_list, context.adapter_context())
        def _stage() -> None:
            for entry in entry_list:
                self.storage.stage_memory(context.tx_id, entry)

        self._with_storage_lock(_stage)
        self._emit_metric(
            LANGGRAPH_METRIC_MEMORY_STAGED,
            len(entry_list),
            context,
        )

    def stage(
        self,
        context: LangGraphContext,
        *,
        key: str,
        value: Any,
        entry_type: str,
        source: str,
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None,
        lineage: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> MemoryEntry:
        entry = MemoryEntry.new(
            key=key,
            value=value,
            type=entry_type,
            source=source,
            confidence=confidence,
            metadata=metadata,
            lineage=lineage,
            idempotency_key=idempotency_key,
            tx_id=context.tx_id,
        )
        self.stage_entries(context, [entry])
        return entry

    def validate(
        self,
        context: LangGraphContext,
        *,
        pipeline: Optional[ValidationPipeline] = None,
        context_metadata: Optional[Dict[str, Any]] = None,
        memory_limit: int = 50,
    ) -> ValidationRecord:
        active_pipeline = pipeline or self.default_validation
        if not active_pipeline:
            raise LangGraphAdapterError("Validation pipeline is required to validate staged memory.")
        return self._with_storage_lock(
            lambda: validate_with_pipeline(
                self.storage,
                tx_id=context.tx_id,
                pipeline=active_pipeline,
                context_metadata=context_metadata,
                memory_limit=memory_limit,
            )
        )

    def commit(self, context: LangGraphContext, validation: Optional[ValidationRecord] = None) -> None:
        self._assert_quiescent(context, "Commit")
        self._with_storage_lock(
            lambda: self.storage.commit_transaction(context.tx_id, validation)
        )
        self._emit_metric(LANGGRAPH_METRIC_TX_COMMITTED, 1, context)

    def rollback(self, context: LangGraphContext, reason: str) -> None:
        self._assert_quiescent(context, "Rollback")
        self._with_storage_lock(lambda: self.storage.rollback_transaction(context.tx_id, reason))
        self._emit_metric(LANGGRAPH_METRIC_TX_ROLLED_BACK, 1, context, extra_tags={"reason": reason})

    def finalize(
        self,
        context: LangGraphContext,
        validation: ValidationRecord,
        *,
        approved_status: str = "approved",
        rollback_reason: str = "validation not approved",
    ) -> str:
        if validation.status == approved_status:
            self.commit(context)
            return "committed"
        self.rollback(context, rollback_reason)
        return "rolled_back"

    def validate_and_finalize(
        self,
        context: LangGraphContext,
        *,
        pipeline: Optional[ValidationPipeline] = None,
        context_metadata: Optional[Dict[str, Any]] = None,
        memory_limit: int = 50,
        approved_status: str = "approved",
        rollback_reason: str = "validation not approved",
    ) -> tuple[ValidationRecord, str]:
        record = self.validate(
            context,
            pipeline=pipeline,
            context_metadata=context_metadata,
            memory_limit=memory_limit,
        )
        status = self.finalize(
            context,
            record,
            approved_status=approved_status,
            rollback_reason=rollback_reason,
        )
        return record, status

    def trace(
        self,
        context: LangGraphContext,
        *,
        decision: str,
        skill_ref: Optional[str],
        reason: str,
        confidence: float,
        result: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DecisionTrace:
        metadata = self._augment_trace_metadata(context, metadata)
        trace = DecisionTrace.new(
            decision=decision,
            skill_ref=skill_ref,
            reason=reason,
            confidence=confidence,
            result=result,
            metadata=metadata,
            tx_id=context.tx_id,
            lineage=context.lineage,
        )
        self._with_storage_lock(lambda: self.storage.record_trace(trace))
        self.pipeline.after_action(decision, {"result": result}, context.adapter_context())
        return trace

    def prepare_prompt(self, prompt: str, context: LangGraphContext) -> str:
        return self.pipeline.before_prompt(prompt, context.adapter_context())

    def invoke(
        self,
        app: Any,
        state: Dict[str, Any],
        *,
        actor: Optional[str] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        lineage: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        context: Optional[LangGraphContext] = None,
        rollback_on_error: bool = True,
        trace_on_error: bool = True,
        trace_graph: Optional[bool] = None,
        tx_scope: Optional[str] = None,
        correlation_id: Optional[str] = None,
        finalize: bool = False,
        finalize_pipeline: Optional[ValidationPipeline] = None,
        finalize_context_metadata: Optional[Dict[str, Any]] = None,
        finalize_memory_limit: int = 50,
        finalize_approved_status: str = "approved",
        finalize_rollback_reason: str = "validation not approved",
    ) -> tuple[Dict[str, Any], LangGraphContext]:
        scope = self._validate_tx_scope(tx_scope or self.tx_scope)
        existing_context = self._extract_context(state)
        parent_context: Optional[LangGraphContext] = None
        requested_correlation = correlation_id

        if context is not None:
            existing_corr = self._get_correlation_id(context)
            if (
                requested_correlation
                and existing_corr
                and requested_correlation != existing_corr
            ):
                raise LangGraphAdapterError(
                    "correlation_id does not match the supplied LangGraphContext."
                )
            if requested_correlation and not existing_corr:
                context.lineage[LANGGRAPH_CORRELATION_ID_KEY] = requested_correlation
            if (
                existing_context
                and existing_context.tx_id != context.tx_id
                and scope == TX_SCOPE_RUN
            ):
                raise LangGraphAdapterError(
                    "LangGraph state context does not match supplied LangGraphContext."
                )
            if scope == TX_SCOPE_SUBGRAPH:
                parent_context = existing_context
            self._register_context(context)
        elif scope == TX_SCOPE_RUN:
            if existing_context is not None:
                existing_corr = self._get_correlation_id(existing_context)
                if (
                    requested_correlation
                    and existing_corr
                    and requested_correlation != existing_corr
                ):
                    raise LangGraphAdapterError(
                        "correlation_id does not match the LangGraphContext in state."
                    )
                if requested_correlation and not existing_corr:
                    existing_context.lineage[LANGGRAPH_CORRELATION_ID_KEY] = requested_correlation
                context = existing_context
            else:
                if not actor or not reason:
                    raise LangGraphAdapterError(
                        "actor and reason are required when no LangGraphContext is supplied."
                    )
                context = self._start_context_with_scope(
                    actor=actor,
                    reason=reason,
                    metadata=metadata,
                    lineage=lineage,
                    idempotency_key=idempotency_key,
                    scope=scope,
                    parent=None,
                    correlation_id=requested_correlation,
                )
        else:
            if existing_context is not None:
                parent_context = existing_context
                resolved_actor = actor or existing_context.actor
                resolved_reason = reason or existing_context.reason
                if not resolved_actor or not resolved_reason:
                    raise LangGraphAdapterError(
                        "actor and reason are required when no LangGraphContext is supplied."
                    )
                context = self._start_context_with_scope(
                    actor=resolved_actor,
                    reason=resolved_reason,
                    metadata=metadata,
                    lineage=lineage,
                    idempotency_key=idempotency_key,
                    scope=scope,
                    parent=parent_context,
                    correlation_id=requested_correlation or self._get_correlation_id(parent_context),
                )
            else:
                if not actor or not reason:
                    raise LangGraphAdapterError(
                        "actor and reason are required when no LangGraphContext is supplied."
                    )
                context = self._start_context_with_scope(
                    actor=actor,
                    reason=reason,
                    metadata=metadata,
                    lineage=lineage,
                    idempotency_key=idempotency_key,
                    scope=scope,
                    parent=None,
                    correlation_id=requested_correlation,
                )

        self._ensure_correlation_id(context, requested_correlation)
        payload = dict(state)
        self.attach_context(payload, context)

        started = time.perf_counter()
        use_trace_graph = self.trace_graph if trace_graph is None else trace_graph

        try:
            result = app.invoke(payload)
        except Exception as exc:
            if rollback_on_error:
                self._safe_rollback(context, str(exc))
            if trace_on_error or use_trace_graph:
                decision = self.graph_trace_decision if use_trace_graph else LANGGRAPH_ERROR_TRACE_DECISION
                self.trace(
                    context,
                    decision=decision,
                    skill_ref=None,
                    reason="LangGraph execution failed.",
                    confidence=0.0,
                    result="error",
                    metadata={
                        "exception": repr(exc),
                        "duration_ms": int((time.perf_counter() - started) * 1000),
                    },
                )
            raise

        if not isinstance(result, dict):
            raise LangGraphAdapterError("LangGraph invoke must return a dict state.")
        result = self._normalize_payload(
            result,
            context,
            include_context=True,
            include_token=True,
            drop_context=False,
            drop_token=False,
        )
        finalize_status = self._finalize_if_requested(
            context,
            enabled=finalize,
            pipeline=finalize_pipeline,
            context_metadata=finalize_context_metadata,
            memory_limit=finalize_memory_limit,
            approved_status=finalize_approved_status,
            rollback_reason=finalize_rollback_reason,
        )
        if scope == TX_SCOPE_SUBGRAPH and parent_context is not None:
            stripped = dict(result)
            stripped.pop(self.context_key, None)
            stripped.pop(self.context_token_key, None)
            result = self._normalize_payload(
                stripped,
                parent_context,
                include_context=True,
                include_token=True,
                drop_context=False,
                drop_token=False,
            )
            context = parent_context
        if use_trace_graph:
            trace_metadata = {"duration_ms": int((time.perf_counter() - started) * 1000)}
            if finalize_status:
                trace_metadata["finalize_status"] = finalize_status
            self.trace(
                context,
                decision=self.graph_trace_decision,
                skill_ref=None,
                reason="LangGraph execution completed.",
                confidence=1.0,
                result="success",
                metadata=trace_metadata,
            )
        return result, context

    def stream(
        self,
        app: Any,
        state: Dict[str, Any],
        *,
        actor: Optional[str] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        lineage: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        context: Optional[LangGraphContext] = None,
        rollback_on_error: bool = True,
        trace_on_error: bool = True,
        trace_graph: Optional[bool] = None,
        tx_scope: Optional[str] = None,
        correlation_id: Optional[str] = None,
        finalize: bool = False,
        finalize_pipeline: Optional[ValidationPipeline] = None,
        finalize_context_metadata: Optional[Dict[str, Any]] = None,
        finalize_memory_limit: int = 50,
        finalize_approved_status: str = "approved",
        finalize_rollback_reason: str = "validation not approved",
        finalize_on_cancel: bool = True,
        cancel_rollback_reason: str = "stream cancelled before completion",
        allow_non_dict_events: bool = True,
    ) -> Iterator[Any]:
        scope = self._validate_tx_scope(tx_scope or self.tx_scope)
        existing_context = self._extract_context(state)
        parent_context: Optional[LangGraphContext] = None
        requested_correlation = correlation_id

        if context is not None:
            existing_corr = self._get_correlation_id(context)
            if (
                requested_correlation
                and existing_corr
                and requested_correlation != existing_corr
            ):
                raise LangGraphAdapterError(
                    "correlation_id does not match the supplied LangGraphContext."
                )
            if requested_correlation and not existing_corr:
                context.lineage[LANGGRAPH_CORRELATION_ID_KEY] = requested_correlation
            if (
                existing_context
                and existing_context.tx_id != context.tx_id
                and scope == TX_SCOPE_RUN
            ):
                raise LangGraphAdapterError(
                    "LangGraph state context does not match supplied LangGraphContext."
                )
            if scope == TX_SCOPE_SUBGRAPH:
                parent_context = existing_context
            self._register_context(context)
        elif scope == TX_SCOPE_RUN:
            if existing_context is not None:
                existing_corr = self._get_correlation_id(existing_context)
                if (
                    requested_correlation
                    and existing_corr
                    and requested_correlation != existing_corr
                ):
                    raise LangGraphAdapterError(
                        "correlation_id does not match the LangGraphContext in state."
                    )
                if requested_correlation and not existing_corr:
                    existing_context.lineage[LANGGRAPH_CORRELATION_ID_KEY] = requested_correlation
                context = existing_context
            else:
                if not actor or not reason:
                    raise LangGraphAdapterError(
                        "actor and reason are required when no LangGraphContext is supplied."
                    )
                context = self._start_context_with_scope(
                    actor=actor,
                    reason=reason,
                    metadata=metadata,
                    lineage=lineage,
                    idempotency_key=idempotency_key,
                    scope=scope,
                    parent=None,
                    correlation_id=requested_correlation,
                )
        else:
            if existing_context is not None:
                parent_context = existing_context
                resolved_actor = actor or existing_context.actor
                resolved_reason = reason or existing_context.reason
                if not resolved_actor or not resolved_reason:
                    raise LangGraphAdapterError(
                        "actor and reason are required when no LangGraphContext is supplied."
                    )
                context = self._start_context_with_scope(
                    actor=resolved_actor,
                    reason=resolved_reason,
                    metadata=metadata,
                    lineage=lineage,
                    idempotency_key=idempotency_key,
                    scope=scope,
                    parent=parent_context,
                    correlation_id=requested_correlation or self._get_correlation_id(parent_context),
                )
            else:
                if not actor or not reason:
                    raise LangGraphAdapterError(
                        "actor and reason are required when no LangGraphContext is supplied."
                    )
                context = self._start_context_with_scope(
                    actor=actor,
                    reason=reason,
                    metadata=metadata,
                    lineage=lineage,
                    idempotency_key=idempotency_key,
                    scope=scope,
                    parent=None,
                    correlation_id=requested_correlation,
                )

        self._ensure_correlation_id(context, requested_correlation)
        payload = dict(state)
        self.attach_context(payload, context)

        started = time.perf_counter()
        use_trace_graph = self.trace_graph if trace_graph is None else trace_graph
        run_context = context
        trace_context = parent_context if scope == TX_SCOPE_SUBGRAPH and parent_context else context
        stream_iter = self._stream_from_app(app, payload)

        def _generator() -> Iterator[Any]:
            completed = False
            errored = False
            try:
                for item in stream_iter:
                    if isinstance(item, dict):
                        normalized = self._normalize_payload(
                            item,
                            run_context,
                            include_context=True,
                            include_token=True,
                            drop_context=False,
                            drop_token=False,
                        )
                        if scope == TX_SCOPE_SUBGRAPH and parent_context is not None:
                            stripped = dict(normalized)
                            stripped.pop(self.context_key, None)
                            stripped.pop(self.context_token_key, None)
                            normalized = self._normalize_payload(
                                stripped,
                                parent_context,
                                include_context=True,
                                include_token=True,
                                drop_context=False,
                                drop_token=False,
                            )
                        yield normalized
                    elif allow_non_dict_events:
                        yield item
                    else:
                        raise LangGraphAdapterError(
                            "LangGraph stream yielded non-dict event; set allow_non_dict_events=True to pass through."
                        )
                completed = True
            except Exception as exc:
                errored = True
                if rollback_on_error:
                    self._safe_rollback(run_context, str(exc))
                if trace_on_error or use_trace_graph:
                    decision = (
                        self.graph_trace_decision
                        if use_trace_graph
                        else LANGGRAPH_ERROR_TRACE_DECISION
                    )
                    self.trace(
                        run_context,
                        decision=decision,
                        skill_ref=None,
                        reason="LangGraph execution failed.",
                        confidence=0.0,
                        result="error",
                        metadata={
                            "exception": repr(exc),
                            "duration_ms": int((time.perf_counter() - started) * 1000),
                        },
                    )
                raise
            finally:
                if not completed and not errored and finalize and finalize_on_cancel:
                    self._safe_rollback(run_context, cancel_rollback_reason)
                    if use_trace_graph:
                        self.trace(
                            trace_context,
                            decision=self.graph_trace_decision,
                            skill_ref=None,
                            reason="LangGraph execution cancelled.",
                            confidence=0.0,
                            result="cancelled",
                            metadata={
                                "duration_ms": int((time.perf_counter() - started) * 1000),
                                "rollback_reason": cancel_rollback_reason,
                            },
                        )
                if completed:
                    finalize_status = self._finalize_if_requested(
                        run_context,
                        enabled=finalize,
                        pipeline=finalize_pipeline,
                        context_metadata=finalize_context_metadata,
                        memory_limit=finalize_memory_limit,
                        approved_status=finalize_approved_status,
                        rollback_reason=finalize_rollback_reason,
                    )
                    if use_trace_graph:
                        trace_metadata = {
                            "duration_ms": int((time.perf_counter() - started) * 1000)
                        }
                        if finalize_status:
                            trace_metadata["finalize_status"] = finalize_status
                        self.trace(
                            trace_context,
                            decision=self.graph_trace_decision,
                            skill_ref=None,
                            reason="LangGraph execution completed.",
                            confidence=1.0,
                            result="success",
                            metadata=trace_metadata,
                        )

        return _generator()

    def astream(
        self,
        app: Any,
        state: Dict[str, Any],
        *,
        actor: Optional[str] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        lineage: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        context: Optional[LangGraphContext] = None,
        rollback_on_error: bool = True,
        trace_on_error: bool = True,
        trace_graph: Optional[bool] = None,
        tx_scope: Optional[str] = None,
        correlation_id: Optional[str] = None,
        finalize: bool = False,
        finalize_pipeline: Optional[ValidationPipeline] = None,
        finalize_context_metadata: Optional[Dict[str, Any]] = None,
        finalize_memory_limit: int = 50,
        finalize_approved_status: str = "approved",
        finalize_rollback_reason: str = "validation not approved",
        finalize_on_cancel: bool = True,
        cancel_rollback_reason: str = "stream cancelled before completion",
        allow_non_dict_events: bool = True,
    ) -> AsyncIterator[Any]:
        scope = self._validate_tx_scope(tx_scope or self.tx_scope)
        existing_context = self._extract_context(state)
        parent_context: Optional[LangGraphContext] = None
        requested_correlation = correlation_id

        if context is not None:
            existing_corr = self._get_correlation_id(context)
            if (
                requested_correlation
                and existing_corr
                and requested_correlation != existing_corr
            ):
                raise LangGraphAdapterError(
                    "correlation_id does not match the supplied LangGraphContext."
                )
            if requested_correlation and not existing_corr:
                context.lineage[LANGGRAPH_CORRELATION_ID_KEY] = requested_correlation
            if (
                existing_context
                and existing_context.tx_id != context.tx_id
                and scope == TX_SCOPE_RUN
            ):
                raise LangGraphAdapterError(
                    "LangGraph state context does not match supplied LangGraphContext."
                )
            if scope == TX_SCOPE_SUBGRAPH:
                parent_context = existing_context
            self._register_context(context)
        elif scope == TX_SCOPE_RUN:
            if existing_context is not None:
                existing_corr = self._get_correlation_id(existing_context)
                if (
                    requested_correlation
                    and existing_corr
                    and requested_correlation != existing_corr
                ):
                    raise LangGraphAdapterError(
                        "correlation_id does not match the LangGraphContext in state."
                    )
                if requested_correlation and not existing_corr:
                    existing_context.lineage[LANGGRAPH_CORRELATION_ID_KEY] = requested_correlation
                context = existing_context
            else:
                if not actor or not reason:
                    raise LangGraphAdapterError(
                        "actor and reason are required when no LangGraphContext is supplied."
                    )
                context = self._start_context_with_scope(
                    actor=actor,
                    reason=reason,
                    metadata=metadata,
                    lineage=lineage,
                    idempotency_key=idempotency_key,
                    scope=scope,
                    parent=None,
                    correlation_id=requested_correlation,
                )
        else:
            if existing_context is not None:
                parent_context = existing_context
                resolved_actor = actor or existing_context.actor
                resolved_reason = reason or existing_context.reason
                if not resolved_actor or not resolved_reason:
                    raise LangGraphAdapterError(
                        "actor and reason are required when no LangGraphContext is supplied."
                    )
                context = self._start_context_with_scope(
                    actor=resolved_actor,
                    reason=resolved_reason,
                    metadata=metadata,
                    lineage=lineage,
                    idempotency_key=idempotency_key,
                    scope=scope,
                    parent=parent_context,
                    correlation_id=requested_correlation or self._get_correlation_id(parent_context),
                )
            else:
                if not actor or not reason:
                    raise LangGraphAdapterError(
                        "actor and reason are required when no LangGraphContext is supplied."
                    )
                context = self._start_context_with_scope(
                    actor=actor,
                    reason=reason,
                    metadata=metadata,
                    lineage=lineage,
                    idempotency_key=idempotency_key,
                    scope=scope,
                    parent=None,
                    correlation_id=requested_correlation,
                )

        self._ensure_correlation_id(context, requested_correlation)
        payload = dict(state)
        self.attach_context(payload, context)

        started = time.perf_counter()
        use_trace_graph = self.trace_graph if trace_graph is None else trace_graph
        run_context = context
        trace_context = parent_context if scope == TX_SCOPE_SUBGRAPH and parent_context else context

        async def _generator() -> AsyncIterator[Any]:
            completed = False
            errored = False
            try:
                stream_iter = await self._astream_from_app(app, payload)
                async for item in stream_iter:
                    if isinstance(item, dict):
                        normalized = self._normalize_payload(
                            item,
                            run_context,
                            include_context=True,
                            include_token=True,
                            drop_context=False,
                            drop_token=False,
                        )
                        if scope == TX_SCOPE_SUBGRAPH and parent_context is not None:
                            stripped = dict(normalized)
                            stripped.pop(self.context_key, None)
                            stripped.pop(self.context_token_key, None)
                            normalized = self._normalize_payload(
                                stripped,
                                parent_context,
                                include_context=True,
                                include_token=True,
                                drop_context=False,
                                drop_token=False,
                            )
                        yield normalized
                    elif allow_non_dict_events:
                        yield item
                    else:
                        raise LangGraphAdapterError(
                            "LangGraph stream yielded non-dict event; set allow_non_dict_events=True to pass through."
                        )
                completed = True
            except Exception as exc:
                errored = True
                if rollback_on_error:
                    self._safe_rollback(run_context, str(exc))
                if trace_on_error or use_trace_graph:
                    decision = (
                        self.graph_trace_decision
                        if use_trace_graph
                        else LANGGRAPH_ERROR_TRACE_DECISION
                    )
                    self.trace(
                        run_context,
                        decision=decision,
                        skill_ref=None,
                        reason="LangGraph execution failed.",
                        confidence=0.0,
                        result="error",
                        metadata={
                            "exception": repr(exc),
                            "duration_ms": int((time.perf_counter() - started) * 1000),
                        },
                    )
                raise
            finally:
                if not completed and not errored and finalize and finalize_on_cancel:
                    self._safe_rollback(run_context, cancel_rollback_reason)
                    if use_trace_graph:
                        self.trace(
                            trace_context,
                            decision=self.graph_trace_decision,
                            skill_ref=None,
                            reason="LangGraph execution cancelled.",
                            confidence=0.0,
                            result="cancelled",
                            metadata={
                                "duration_ms": int((time.perf_counter() - started) * 1000),
                                "rollback_reason": cancel_rollback_reason,
                            },
                        )
                if completed:
                    finalize_status = self._finalize_if_requested(
                        run_context,
                        enabled=finalize,
                        pipeline=finalize_pipeline,
                        context_metadata=finalize_context_metadata,
                        memory_limit=finalize_memory_limit,
                        approved_status=finalize_approved_status,
                        rollback_reason=finalize_rollback_reason,
                    )
                    if use_trace_graph:
                        trace_metadata = {
                            "duration_ms": int((time.perf_counter() - started) * 1000)
                        }
                        if finalize_status:
                            trace_metadata["finalize_status"] = finalize_status
                        self.trace(
                            trace_context,
                            decision=self.graph_trace_decision,
                            skill_ref=None,
                            reason="LangGraph execution completed.",
                            confidence=1.0,
                            result="success",
                            metadata=trace_metadata,
                        )

        return _generator()

    async def ainvoke(
        self,
        app: Any,
        state: Dict[str, Any],
        *,
        actor: Optional[str] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        lineage: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        context: Optional[LangGraphContext] = None,
        rollback_on_error: bool = True,
        trace_on_error: bool = True,
        trace_graph: Optional[bool] = None,
        tx_scope: Optional[str] = None,
        correlation_id: Optional[str] = None,
        finalize: bool = False,
        finalize_pipeline: Optional[ValidationPipeline] = None,
        finalize_context_metadata: Optional[Dict[str, Any]] = None,
        finalize_memory_limit: int = 50,
        finalize_approved_status: str = "approved",
        finalize_rollback_reason: str = "validation not approved",
    ) -> tuple[Dict[str, Any], LangGraphContext]:
        scope = self._validate_tx_scope(tx_scope or self.tx_scope)
        existing_context = self._extract_context(state)
        parent_context: Optional[LangGraphContext] = None
        requested_correlation = correlation_id

        if context is not None:
            existing_corr = self._get_correlation_id(context)
            if (
                requested_correlation
                and existing_corr
                and requested_correlation != existing_corr
            ):
                raise LangGraphAdapterError(
                    "correlation_id does not match the supplied LangGraphContext."
                )
            if requested_correlation and not existing_corr:
                context.lineage[LANGGRAPH_CORRELATION_ID_KEY] = requested_correlation
            if (
                existing_context
                and existing_context.tx_id != context.tx_id
                and scope == TX_SCOPE_RUN
            ):
                raise LangGraphAdapterError(
                    "LangGraph state context does not match supplied LangGraphContext."
                )
            if scope == TX_SCOPE_SUBGRAPH:
                parent_context = existing_context
            self._register_context(context)
        elif scope == TX_SCOPE_RUN:
            if existing_context is not None:
                existing_corr = self._get_correlation_id(existing_context)
                if (
                    requested_correlation
                    and existing_corr
                    and requested_correlation != existing_corr
                ):
                    raise LangGraphAdapterError(
                        "correlation_id does not match the LangGraphContext in state."
                    )
                if requested_correlation and not existing_corr:
                    existing_context.lineage[LANGGRAPH_CORRELATION_ID_KEY] = requested_correlation
                context = existing_context
            else:
                if not actor or not reason:
                    raise LangGraphAdapterError(
                        "actor and reason are required when no LangGraphContext is supplied."
                    )
                context = self._start_context_with_scope(
                    actor=actor,
                    reason=reason,
                    metadata=metadata,
                    lineage=lineage,
                    idempotency_key=idempotency_key,
                    scope=scope,
                    parent=None,
                    correlation_id=requested_correlation,
                )
        else:
            if existing_context is not None:
                parent_context = existing_context
                resolved_actor = actor or existing_context.actor
                resolved_reason = reason or existing_context.reason
                if not resolved_actor or not resolved_reason:
                    raise LangGraphAdapterError(
                        "actor and reason are required when no LangGraphContext is supplied."
                    )
                context = self._start_context_with_scope(
                    actor=resolved_actor,
                    reason=resolved_reason,
                    metadata=metadata,
                    lineage=lineage,
                    idempotency_key=idempotency_key,
                    scope=scope,
                    parent=parent_context,
                    correlation_id=requested_correlation or self._get_correlation_id(parent_context),
                )
            else:
                if not actor or not reason:
                    raise LangGraphAdapterError(
                        "actor and reason are required when no LangGraphContext is supplied."
                    )
                context = self._start_context_with_scope(
                    actor=actor,
                    reason=reason,
                    metadata=metadata,
                    lineage=lineage,
                    idempotency_key=idempotency_key,
                    scope=scope,
                    parent=None,
                    correlation_id=requested_correlation,
                )

        self._ensure_correlation_id(context, requested_correlation)
        payload = dict(state)
        self.attach_context(payload, context)

        started = time.perf_counter()
        use_trace_graph = self.trace_graph if trace_graph is None else trace_graph

        try:
            result = await self._invoke_async_app(app, payload)
        except Exception as exc:
            if rollback_on_error:
                self._safe_rollback(context, str(exc))
            if trace_on_error or use_trace_graph:
                decision = (
                    self.graph_trace_decision
                    if use_trace_graph
                    else LANGGRAPH_ERROR_TRACE_DECISION
                )
                self.trace(
                    context,
                    decision=decision,
                    skill_ref=None,
                    reason="LangGraph execution failed.",
                    confidence=0.0,
                    result="error",
                    metadata={
                        "exception": repr(exc),
                        "duration_ms": int((time.perf_counter() - started) * 1000),
                    },
                )
            raise

        if not isinstance(result, dict):
            raise LangGraphAdapterError("LangGraph invoke must return a dict state.")
        result = self._normalize_payload(
            result,
            context,
            include_context=True,
            include_token=True,
            drop_context=False,
            drop_token=False,
        )
        finalize_status = self._finalize_if_requested(
            context,
            enabled=finalize,
            pipeline=finalize_pipeline,
            context_metadata=finalize_context_metadata,
            memory_limit=finalize_memory_limit,
            approved_status=finalize_approved_status,
            rollback_reason=finalize_rollback_reason,
        )
        if scope == TX_SCOPE_SUBGRAPH and parent_context is not None:
            stripped = dict(result)
            stripped.pop(self.context_key, None)
            stripped.pop(self.context_token_key, None)
            result = self._normalize_payload(
                stripped,
                parent_context,
                include_context=True,
                include_token=True,
                drop_context=False,
                drop_token=False,
            )
            context = parent_context
        if use_trace_graph:
            trace_metadata = {"duration_ms": int((time.perf_counter() - started) * 1000)}
            if finalize_status:
                trace_metadata["finalize_status"] = finalize_status
            self.trace(
                context,
                decision=self.graph_trace_decision,
                skill_ref=None,
                reason="LangGraph execution completed.",
                confidence=1.0,
                result="success",
                metadata=trace_metadata,
            )
        return result, context

    def _extract_context(self, state: Dict[str, Any]) -> Optional[LangGraphContext]:
        if self.context_key not in state and self.context_token_key not in state:
            return None
        probe = dict(state)
        return self.get_context(probe)

    def _start_context_with_scope(
        self,
        *,
        actor: str,
        reason: str,
        metadata: Optional[Dict[str, Any]],
        lineage: Optional[Dict[str, Any]],
        idempotency_key: Optional[str],
        scope: str,
        parent: Optional[LangGraphContext],
        correlation_id: Optional[str],
    ) -> LangGraphContext:
        resolved_lineage = self._build_lineage(
            lineage,
            scope=scope,
            parent=parent,
            correlation_id=correlation_id,
        )
        return self.start_context(
            actor=actor,
            reason=reason,
            metadata=metadata,
            lineage=resolved_lineage,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )

    def _build_lineage(
        self,
        lineage: Optional[Dict[str, Any]],
        *,
        scope: str,
        parent: Optional[LangGraphContext],
        correlation_id: Optional[str],
    ) -> Dict[str, Any]:
        resolved = dict(parent.lineage) if parent else {}
        if lineage:
            resolved.update(lineage)
        if parent and "parent_tx_id" not in resolved:
            resolved["parent_tx_id"] = parent.tx_id
        resolved["tx_scope"] = scope
        if correlation_id:
            resolved[LANGGRAPH_CORRELATION_ID_KEY] = correlation_id
        elif LANGGRAPH_CORRELATION_ID_KEY not in resolved:
            resolved[LANGGRAPH_CORRELATION_ID_KEY] = self._correlation_id_factory()
        return resolved

    def _validate_tx_scope(self, scope: str) -> str:
        if scope not in (TX_SCOPE_RUN, TX_SCOPE_SUBGRAPH):
            raise LangGraphAdapterError(
                f"Unsupported tx_scope '{scope}'. Use '{TX_SCOPE_RUN}' or '{TX_SCOPE_SUBGRAPH}'."
            )
        return scope

    def _resolve_edge_path(
        self,
        state: Dict[str, Any],
        node_name: str,
    ) -> Optional[list[str]]:
        if not self.trace_edge_path or not self.edge_path_key:
            return None
        raw = state.get(self.edge_path_key)
        if raw is None:
            path: list[str] = []
        elif isinstance(raw, list):
            path = list(raw)
        elif isinstance(raw, tuple):
            path = list(raw)
        else:
            raise LangGraphAdapterError(
                f"LangGraph edge path at key '{self.edge_path_key}' must be a list of strings."
            )
        for item in path:
            if not isinstance(item, str):
                raise LangGraphAdapterError(
                    f"LangGraph edge path at key '{self.edge_path_key}' must contain strings."
                )
        path.append(node_name)
        return path

    def _trace_state_keys(self, state: Dict[str, Any]) -> list[str]:
        internal = {self.context_key, self.context_token_key}
        if self.edge_path_key:
            internal.add(self.edge_path_key)
        return [key for key in state.keys() if key not in internal]

    def _augment_trace_metadata(
        self,
        context: LangGraphContext,
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        payload = dict(metadata or {})
        payload.setdefault("tx_scope", context.lineage.get("tx_scope", self.tx_scope))
        correlation_id = self._ensure_correlation_id(context, None)
        if correlation_id and "correlation_id" not in payload:
            payload["correlation_id"] = correlation_id
        return payload

    def _get_correlation_id(self, context: LangGraphContext) -> Optional[str]:
        return context.lineage.get(LANGGRAPH_CORRELATION_ID_KEY)

    def _ensure_correlation_id(
        self,
        context: LangGraphContext,
        correlation_id: Optional[str],
    ) -> str:
        existing = context.lineage.get(LANGGRAPH_CORRELATION_ID_KEY)
        if correlation_id:
            if existing and existing != correlation_id:
                raise LangGraphAdapterError(
                    "correlation_id does not match the LangGraphContext lineage."
                )
            context.lineage[LANGGRAPH_CORRELATION_ID_KEY] = correlation_id
            return correlation_id
        if existing:
            return existing
        generated = self._correlation_id_factory()
        context.lineage[LANGGRAPH_CORRELATION_ID_KEY] = generated
        return generated

    def _emit_metric(
        self,
        name: str,
        value: int,
        context: LangGraphContext,
        extra_tags: Optional[Dict[str, str]] = None,
    ) -> None:
        if not self.metrics_hook:
            return
        tags = {
            "tx_id": context.tx_id,
            "tx_scope": context.lineage.get("tx_scope", self.tx_scope),
        }
        correlation_id = self._get_correlation_id(context)
        if correlation_id:
            tags["correlation_id"] = correlation_id
        if extra_tags:
            tags.update(extra_tags)
        try:
            self.metrics_hook.increment(name, value, tags=tags)
        except Exception:
            return

    def _get_run_state(self, context: LangGraphContext) -> _RunState:
        with self._run_state_lock:
            run_state = self._run_states.get(context.tx_id)
            if run_state is None:
                run_state = _RunState()
                self._run_states[context.tx_id] = run_state
            return run_state

    def _enter_node(self, context: LangGraphContext) -> None:
        run_state = self._get_run_state(context)
        run_state.enter()

    def _exit_node(self, context: LangGraphContext) -> None:
        run_state = self._get_run_state(context)
        run_state.exit()

    def _assert_quiescent(self, context: LangGraphContext, action: str) -> None:
        if not self.enforce_quiescent_finalize:
            return
        run_state = self._get_run_state(context)
        with run_state.lock:
            active = run_state.active_nodes
        if active > 1:
            raise LangGraphAdapterError(
                f"{action} requested while {active} LangGraph nodes are active. "
                "Finalize after branch merges or disable enforce_quiescent_finalize."
            )

    def _safe_rollback(self, context: LangGraphContext, reason: str) -> None:
        def _rollback() -> None:
            record = self.storage.get_transaction(context.tx_id)
            if record.status in (TX_COMMITTED, TX_ROLLED_BACK):
                return
            self.storage.rollback_transaction(context.tx_id, reason)

        try:
            self._with_storage_lock(_rollback)
        except Exception:
            return

    def _register_context(self, context: LangGraphContext) -> None:
        with self._registry_lock:
            self._context_registry[context.tx_id] = context

    def _lookup_context(self, tx_id: str) -> Optional[LangGraphContext]:
        with self._registry_lock:
            return self._context_registry.get(tx_id)

    def _rehydrate_context(self, tx_id: str) -> Optional[LangGraphContext]:
        try:
            record = self.storage.get_transaction(tx_id)
        except Exception:
            return None

        context = LangGraphContext(
            storage=self.storage,
            tx_id=record.tx_id,
            actor=record.actor,
            reason=record.reason,
            metadata=record.metadata or {},
            lineage=record.lineage or {},
        )
        self._register_context(context)
        return context

    def _finalize_if_requested(
        self,
        context: LangGraphContext,
        *,
        enabled: bool,
        pipeline: Optional[ValidationPipeline],
        context_metadata: Optional[Dict[str, Any]],
        memory_limit: int,
        approved_status: str,
        rollback_reason: str,
    ) -> Optional[str]:
        if not enabled:
            return None
        record = self.validate(
            context,
            pipeline=pipeline,
            context_metadata=context_metadata,
            memory_limit=memory_limit,
        )
        return self.finalize(
            context,
            record,
            approved_status=approved_status,
            rollback_reason=rollback_reason,
        )

    async def _invoke_async_app(self, app: Any, payload: Dict[str, Any]) -> Any:
        ainvoke = getattr(app, "ainvoke", None)
        if callable(ainvoke):
            return await ainvoke(payload)
        invoke = getattr(app, "invoke", None)
        if callable(invoke):
            return await asyncio.to_thread(invoke, payload)
        raise LangGraphAdapterError("LangGraph app does not support invoke or ainvoke.")

    def _stream_from_app(self, app: Any, payload: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        stream = getattr(app, "stream", None)
        if callable(stream):
            return stream(payload)
        invoke = getattr(app, "invoke", None)
        if callable(invoke):
            def _single() -> Iterator[Dict[str, Any]]:
                yield invoke(payload)

            return _single()
        raise LangGraphAdapterError("LangGraph app does not support stream or invoke.")

    async def _astream_from_app(
        self, app: Any, payload: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        astream = getattr(app, "astream", None)
        if callable(astream):
            return astream(payload)
        ainvoke = getattr(app, "ainvoke", None)
        if callable(ainvoke):
            result = await ainvoke(payload)
            return self._single_item_async_iter(result)
        invoke = getattr(app, "invoke", None)
        if callable(invoke):
            result = await asyncio.to_thread(invoke, payload)
            return self._single_item_async_iter(result)
        raise LangGraphAdapterError("LangGraph app does not support astream or invoke.")

    async def _single_item_async_iter(self, item: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        yield item

    def _with_storage_lock(self, func: Callable[[], Any]) -> Any:
        if not self.serialize_storage:
            return func()
        with self._storage_lock:
            return func()

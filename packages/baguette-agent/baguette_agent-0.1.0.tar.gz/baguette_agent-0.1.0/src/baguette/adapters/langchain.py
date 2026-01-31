"""LangChain adapter helpers for integrating Baguette into callback flows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, Optional
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

try:  # pragma: no cover - optional dependency
    from langchain.callbacks.base import BaseCallbackHandler
except Exception:  # pragma: no cover - optional dependency
    try:  # pragma: no cover - optional dependency
        from langchain_core.callbacks.base import BaseCallbackHandler
    except Exception:  # pragma: no cover - optional dependency
        BaseCallbackHandler = object  # type: ignore[assignment]


class LangChainAdapterError(RuntimeError):
    pass


LANGCHAIN_CONTEXT_KEY = "_baguette"
LANGCHAIN_CONTEXT_TOKEN_KEY = "_baguette_tx_id"
LANGCHAIN_CORRELATION_ID_KEY = "correlation_id"
LANGCHAIN_CHAIN_TRACE_DECISION = "chain.run"
LANGCHAIN_LLM_TRACE_DECISION = "llm.run"
LANGCHAIN_TOOL_TRACE_DECISION = "tool.run"
LANGCHAIN_ERROR_TRACE_DECISION = "chain.error"


def _default_correlation_id() -> str:
    return str(uuid.uuid4())


def _normalize_run_id(run_id: Any) -> str:
    if isinstance(run_id, uuid.UUID):
        return str(run_id)
    return str(run_id)


@dataclass
class LangChainContext:
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


class LangChainAdapter:
    """Baguette adapter for LangChain callback events."""

    def __init__(
        self,
        storage: StorageBackend,
        *,
        pipeline: Optional[AdapterPipeline] = None,
        default_validation: Optional[ValidationPipeline] = None,
        memory_injection: Optional["AdapterHooks"] = None,
        trace_chains: bool = False,
        trace_llm: bool = False,
        trace_tools: bool = False,
        trace_errors: bool = True,
        serialize_storage: bool = True,
        tx_scope: str = TX_SCOPE_RUN,
        correlation_id_factory: Optional[Callable[[], str]] = None,
    ) -> None:
        self.storage = storage
        self.pipeline = pipeline or AdapterPipeline()
        if memory_injection is not None:
            self.pipeline.register(memory_injection)
        self.default_validation = default_validation
        self.trace_chains = trace_chains
        self.trace_llm = trace_llm
        self.trace_tools = trace_tools
        self.trace_errors = trace_errors
        self.serialize_storage = serialize_storage
        self.tx_scope = self._validate_tx_scope(tx_scope)
        self._correlation_id_factory = correlation_id_factory or _default_correlation_id
        self._context_registry: Dict[str, LangChainContext] = {}
        self._run_registry: Dict[str, LangChainContext] = {}
        self._registry_lock = threading.RLock()
        self._storage_lock = threading.RLock()

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
    ) -> LangChainContext:
        resolved_lineage = dict(lineage or {})
        if "tx_scope" not in resolved_lineage:
            resolved_lineage["tx_scope"] = self._validate_tx_scope(tx_scope or self.tx_scope)
        if correlation_id:
            resolved_lineage[LANGCHAIN_CORRELATION_ID_KEY] = correlation_id
        elif LANGCHAIN_CORRELATION_ID_KEY not in resolved_lineage:
            resolved_lineage[LANGCHAIN_CORRELATION_ID_KEY] = self._correlation_id_factory()

        tx_id = self.storage.begin_transaction(
            actor=actor,
            reason=reason,
            metadata=metadata,
            idempotency_key=idempotency_key,
            lineage=resolved_lineage,
        )
        context = LangChainContext(
            storage=self.storage,
            tx_id=tx_id,
            actor=actor,
            reason=reason,
            metadata=metadata or {},
            lineage=resolved_lineage,
        )
        self._register_context(context)
        return context

    def attach_context(self, metadata: Dict[str, Any], context: LangChainContext) -> None:
        self._register_context(context)
        metadata[LANGCHAIN_CONTEXT_KEY] = context
        metadata[LANGCHAIN_CONTEXT_TOKEN_KEY] = context.tx_id

    def get_context(self, tx_id: str) -> Optional[LangChainContext]:
        with self._registry_lock:
            return self._context_registry.get(tx_id)

    def get_context_for_run(self, run_id: Any) -> Optional[LangChainContext]:
        normalized = _normalize_run_id(run_id)
        with self._registry_lock:
            return self._run_registry.get(normalized)

    def clear_contexts(self, run_ids: Optional[Iterable[str]] = None) -> None:
        with self._registry_lock:
            if run_ids is None:
                self._run_registry.clear()
                return
            for run_id in run_ids:
                self._run_registry.pop(run_id, None)

    def stage_entries(self, context: LangChainContext, entries: list[MemoryEntry]) -> None:
        if not entries:
            return
        self.pipeline.on_write(entries, context.adapter_context())

        def _stage() -> None:
            for entry in entries:
                self.storage.stage_memory(context.tx_id, entry)

        self._with_storage_lock(_stage)

    def stage(
        self,
        context: LangChainContext,
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
        context: LangChainContext,
        *,
        pipeline: Optional[ValidationPipeline] = None,
        context_metadata: Optional[Dict[str, Any]] = None,
        memory_limit: int = 50,
    ) -> ValidationRecord:
        active_pipeline = pipeline or self.default_validation
        if not active_pipeline:
            raise LangChainAdapterError("Validation pipeline is required to validate staged memory.")
        return self._with_storage_lock(
            lambda: validate_with_pipeline(
                self.storage,
                tx_id=context.tx_id,
                pipeline=active_pipeline,
                context_metadata=context_metadata,
                memory_limit=memory_limit,
            )
        )

    def commit(self, context: LangChainContext, validation: Optional[ValidationRecord] = None) -> None:
        self._with_storage_lock(
            lambda: self.storage.commit_transaction(context.tx_id, validation)
        )

    def rollback(self, context: LangChainContext, reason: str) -> None:
        self._with_storage_lock(lambda: self.storage.rollback_transaction(context.tx_id, reason))

    def finalize(
        self,
        context: LangChainContext,
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
        context: LangChainContext,
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
        context: LangChainContext,
        *,
        decision: str,
        skill_ref: Optional[str],
        reason: str,
        confidence: float,
        result: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DecisionTrace:
        trace = DecisionTrace.new(
            decision=decision,
            skill_ref=skill_ref,
            reason=reason,
            confidence=confidence,
            result=result,
            metadata=self._augment_trace_metadata(context, metadata),
            tx_id=context.tx_id,
            lineage=context.lineage,
        )
        self._with_storage_lock(lambda: self.storage.record_trace(trace))
        self.pipeline.after_action(decision, {"result": result}, context.adapter_context())
        return trace

    def prepare_prompt(self, prompt: str, context: LangChainContext) -> str:
        return self.pipeline.before_prompt(prompt, context.adapter_context())

    def callback_handler(
        self,
        *,
        actor: Optional[str] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        lineage: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        context: Optional[LangChainContext] = None,
        tx_scope: Optional[str] = None,
        correlation_id: Optional[str] = None,
        rollback_on_error: bool = True,
        finalize: bool = False,
        finalize_pipeline: Optional[ValidationPipeline] = None,
        finalize_context_metadata: Optional[Dict[str, Any]] = None,
        finalize_memory_limit: int = 50,
        finalize_approved_status: str = "approved",
        finalize_rollback_reason: str = "validation not approved",
        trace_chains: Optional[bool] = None,
        trace_llm: Optional[bool] = None,
        trace_tools: Optional[bool] = None,
        trace_errors: Optional[bool] = None,
    ) -> "LangChainCallbackHandler":
        return LangChainCallbackHandler(
            adapter=self,
            actor=actor,
            reason=reason,
            metadata=metadata,
            lineage=lineage,
            idempotency_key=idempotency_key,
            context=context,
            tx_scope=tx_scope,
            correlation_id=correlation_id,
            rollback_on_error=rollback_on_error,
            finalize=finalize,
            finalize_pipeline=finalize_pipeline,
            finalize_context_metadata=finalize_context_metadata,
            finalize_memory_limit=finalize_memory_limit,
            finalize_approved_status=finalize_approved_status,
            finalize_rollback_reason=finalize_rollback_reason,
            trace_chains=trace_chains,
            trace_llm=trace_llm,
            trace_tools=trace_tools,
            trace_errors=trace_errors,
        )

    def _augment_trace_metadata(
        self,
        context: LangChainContext,
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        payload = dict(metadata or {})
        payload.setdefault("tx_scope", context.lineage.get("tx_scope", self.tx_scope))
        correlation_id = self._ensure_correlation_id(context, None)
        if correlation_id and "correlation_id" not in payload:
            payload["correlation_id"] = correlation_id
        return payload

    def _ensure_correlation_id(
        self,
        context: LangChainContext,
        correlation_id: Optional[str],
    ) -> str:
        existing = context.lineage.get(LANGCHAIN_CORRELATION_ID_KEY)
        if correlation_id:
            if existing and existing != correlation_id:
                raise LangChainAdapterError(
                    "correlation_id does not match the LangChainContext lineage."
                )
            context.lineage[LANGCHAIN_CORRELATION_ID_KEY] = correlation_id
            return correlation_id
        if existing:
            return existing
        generated = self._correlation_id_factory()
        context.lineage[LANGCHAIN_CORRELATION_ID_KEY] = generated
        return generated

    def _register_context(self, context: LangChainContext) -> None:
        with self._registry_lock:
            self._context_registry[context.tx_id] = context

    def _register_run(self, run_id: str, context: LangChainContext) -> None:
        with self._registry_lock:
            self._run_registry[run_id] = context

    def _extract_context_from_metadata(self, metadata: Optional[Dict[str, Any]]) -> Optional[LangChainContext]:
        if not isinstance(metadata, dict):
            return None
        raw_context = metadata.get(LANGCHAIN_CONTEXT_KEY)
        if isinstance(raw_context, LangChainContext):
            self._register_context(raw_context)
            return raw_context
        raw_token = metadata.get(LANGCHAIN_CONTEXT_TOKEN_KEY)
        if isinstance(raw_token, str) and raw_token.strip():
            return self._rehydrate_context(raw_token)
        return None

    def _rehydrate_context(self, tx_id: str) -> Optional[LangChainContext]:
        try:
            record = self.storage.get_transaction(tx_id)
        except Exception:
            return None
        context = LangChainContext(
            storage=self.storage,
            tx_id=record.tx_id,
            actor=record.actor,
            reason=record.reason,
            metadata=record.metadata or {},
            lineage=record.lineage or {},
        )
        self._register_context(context)
        return context

    def _resolve_context(
        self,
        *,
        run_id: Any,
        parent_run_id: Optional[Any],
        actor: Optional[str],
        reason: Optional[str],
        metadata: Optional[Dict[str, Any]],
        lineage: Optional[Dict[str, Any]],
        idempotency_key: Optional[str],
        tx_scope: str,
        correlation_id: Optional[str],
        explicit_context: Optional[LangChainContext],
    ) -> LangChainContext:
        normalized = _normalize_run_id(run_id)
        with self._registry_lock:
            existing = self._run_registry.get(normalized)
        if existing:
            return existing

        parent_context: Optional[LangChainContext] = None
        if parent_run_id is not None:
            parent_context = self.get_context_for_run(parent_run_id)

        if parent_context and tx_scope == TX_SCOPE_RUN:
            if explicit_context and explicit_context.tx_id != parent_context.tx_id:
                raise LangChainAdapterError(
                    "LangChain run context does not match supplied LangChainContext."
                )
            if correlation_id:
                self._ensure_correlation_id(parent_context, correlation_id)
            self._register_run(normalized, parent_context)
            return parent_context

        context = explicit_context
        if context is None and parent_context and tx_scope == TX_SCOPE_SUBGRAPH:
            resolved_actor = actor or parent_context.actor
            resolved_reason = reason or parent_context.reason
            if not resolved_actor or not resolved_reason:
                raise LangChainAdapterError(
                    "actor and reason are required when no LangChainContext is supplied."
                )
            context = self._start_context_with_scope(
                actor=resolved_actor,
                reason=resolved_reason,
                metadata=metadata,
                lineage=lineage,
                idempotency_key=idempotency_key,
                scope=tx_scope,
                parent=parent_context,
                correlation_id=correlation_id or self._get_correlation_id(parent_context),
            )
        elif context is None:
            if not actor or not reason:
                raise LangChainAdapterError(
                    "actor and reason are required when no LangChainContext is supplied."
                )
            context = self._start_context_with_scope(
                actor=actor,
                reason=reason,
                metadata=metadata,
                lineage=lineage,
                idempotency_key=idempotency_key,
                scope=tx_scope,
                parent=None,
                correlation_id=correlation_id,
            )

        self._register_context(context)
        self._ensure_correlation_id(context, correlation_id)
        self._register_run(normalized, context)
        return context

    def _start_context_with_scope(
        self,
        *,
        actor: str,
        reason: str,
        metadata: Optional[Dict[str, Any]],
        lineage: Optional[Dict[str, Any]],
        idempotency_key: Optional[str],
        scope: str,
        parent: Optional[LangChainContext],
        correlation_id: Optional[str],
    ) -> LangChainContext:
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
        parent: Optional[LangChainContext],
        correlation_id: Optional[str],
    ) -> Dict[str, Any]:
        resolved = dict(parent.lineage) if parent else {}
        if lineage:
            resolved.update(lineage)
        if parent and "parent_tx_id" not in resolved:
            resolved["parent_tx_id"] = parent.tx_id
        resolved["tx_scope"] = self._validate_tx_scope(scope)
        if correlation_id:
            resolved[LANGCHAIN_CORRELATION_ID_KEY] = correlation_id
        elif LANGCHAIN_CORRELATION_ID_KEY not in resolved:
            resolved[LANGCHAIN_CORRELATION_ID_KEY] = self._correlation_id_factory()
        return resolved

    def _get_correlation_id(self, context: LangChainContext) -> Optional[str]:
        return context.lineage.get(LANGCHAIN_CORRELATION_ID_KEY)

    def _validate_tx_scope(self, scope: str) -> str:
        if scope not in (TX_SCOPE_RUN, TX_SCOPE_SUBGRAPH):
            raise LangChainAdapterError(
                f"Unsupported tx_scope '{scope}'. Use '{TX_SCOPE_RUN}' or '{TX_SCOPE_SUBGRAPH}'."
            )
        return scope

    def _with_storage_lock(self, func: Callable[[], Any]) -> Any:
        if not self.serialize_storage:
            return func()
        with self._storage_lock:
            return func()


@dataclass
class _RootState:
    run_ids: set[str] = field(default_factory=set)
    run_started: Dict[str, float] = field(default_factory=dict)
    run_names: Dict[str, str] = field(default_factory=dict)
    root_tx_id: Optional[str] = None
    finalized: bool = False


class LangChainCallbackHandler(BaseCallbackHandler):
    def __init__(
        self,
        *,
        adapter: LangChainAdapter,
        actor: Optional[str] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        lineage: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        context: Optional[LangChainContext] = None,
        tx_scope: Optional[str] = None,
        correlation_id: Optional[str] = None,
        rollback_on_error: bool = True,
        finalize: bool = False,
        finalize_pipeline: Optional[ValidationPipeline] = None,
        finalize_context_metadata: Optional[Dict[str, Any]] = None,
        finalize_memory_limit: int = 50,
        finalize_approved_status: str = "approved",
        finalize_rollback_reason: str = "validation not approved",
        trace_chains: Optional[bool] = None,
        trace_llm: Optional[bool] = None,
        trace_tools: Optional[bool] = None,
        trace_errors: Optional[bool] = None,
    ) -> None:
        if BaseCallbackHandler is object:
            raise LangChainAdapterError(
                "langchain is required for LangChainCallbackHandler; install baguette[langchain]."
            )
        self._adapter = adapter
        self._actor = actor
        self._reason = reason
        self._metadata = metadata or {}
        self._lineage = lineage or {}
        self._idempotency_key = idempotency_key
        self._context = context
        self._tx_scope = adapter._validate_tx_scope(tx_scope or adapter.tx_scope)
        self._correlation_id = correlation_id
        self._rollback_on_error = rollback_on_error
        self._finalize = finalize
        self._finalize_pipeline = finalize_pipeline
        self._finalize_context_metadata = finalize_context_metadata
        self._finalize_memory_limit = finalize_memory_limit
        self._finalize_approved_status = finalize_approved_status
        self._finalize_rollback_reason = finalize_rollback_reason
        self._trace_chains = adapter.trace_chains if trace_chains is None else trace_chains
        self._trace_llm = adapter.trace_llm if trace_llm is None else trace_llm
        self._trace_tools = adapter.trace_tools if trace_tools is None else trace_tools
        self._trace_errors = adapter.trace_errors if trace_errors is None else trace_errors
        self._root_states: Dict[str, _RootState] = {}
        self._root_by_run: Dict[str, str] = {}
        self._last_root_run_id: Optional[str] = None
        self._last_root_tx_id: Optional[str] = None

    @property
    def root_tx_id(self) -> Optional[str]:
        return self._last_root_tx_id

    def get_root_tx_id(self, run_id: str) -> Optional[str]:
        normalized = _normalize_run_id(run_id)
        root_id = self._root_by_run.get(normalized)
        if not root_id:
            return None
        state = self._root_states.get(root_id)
        return state.root_tx_id if state else None

    def _resolve_root_id(self, run_id: str, parent_run_id: Optional[str]) -> str:
        if parent_run_id:
            root_id = self._root_by_run.get(parent_run_id)
            if root_id:
                return root_id
            if parent_run_id in self._root_states:
                return parent_run_id
        existing = self._root_by_run.get(run_id)
        if existing:
            return existing
        return run_id

    def _register_run_state(
        self,
        *,
        run_id: str,
        parent_run_id: Optional[str],
        serialized: Any,
        context: LangChainContext,
    ) -> str:
        root_id = self._resolve_root_id(run_id, parent_run_id)
        state = self._root_states.setdefault(root_id, _RootState())
        state.run_ids.add(run_id)
        state.run_started[run_id] = time.perf_counter()
        state.run_names[run_id] = _extract_name(serialized)
        self._root_by_run[run_id] = root_id
        if parent_run_id and parent_run_id not in self._root_by_run:
            self._root_by_run[parent_run_id] = root_id
        if run_id == root_id and state.root_tx_id is None:
            state.root_tx_id = context.tx_id
            self._last_root_run_id = root_id
            self._last_root_tx_id = context.tx_id
        return root_id

    def _cleanup_root(self, root_id: str) -> None:
        state = self._root_states.pop(root_id, None)
        if not state:
            return
        for run_id in state.run_ids:
            self._root_by_run.pop(run_id, None)
        self._adapter.clear_contexts(run_ids=state.run_ids)
        if self._last_root_run_id == root_id:
            self._last_root_run_id = None

    def on_chain_start(self, serialized, inputs, run_id, parent_run_id=None, **kwargs):
        normalized = _normalize_run_id(run_id)
        parent_id = _normalize_run_id(parent_run_id) if parent_run_id else None

        metadata = kwargs.get("metadata") or {}
        explicit = self._adapter._extract_context_from_metadata(metadata) or self._context

        context = self._adapter._resolve_context(
            run_id=normalized,
            parent_run_id=parent_id,
            actor=self._actor,
            reason=self._reason,
            metadata=self._metadata,
            lineage=self._lineage,
            idempotency_key=self._idempotency_key,
            tx_scope=self._tx_scope,
            correlation_id=self._correlation_id,
            explicit_context=explicit,
        )
        self._register_run_state(
            run_id=normalized,
            parent_run_id=parent_id,
            serialized=serialized,
            context=context,
        )

        if self._trace_chains:
            self._adapter.trace(
                context,
                decision=LANGCHAIN_CHAIN_TRACE_DECISION,
                skill_ref=None,
                reason="LangChain chain started.",
                confidence=1.0,
                result="start",
                metadata=self._build_trace_metadata(normalized, parent_id),
            )

    def on_chain_end(self, outputs, run_id, parent_run_id=None, **kwargs):
        normalized = _normalize_run_id(run_id)
        parent_id = _normalize_run_id(parent_run_id) if parent_run_id else None
        context = self._adapter.get_context_for_run(normalized)
        if context and self._trace_chains:
            self._adapter.trace(
                context,
                decision=LANGCHAIN_CHAIN_TRACE_DECISION,
                skill_ref=None,
                reason="LangChain chain completed.",
                confidence=1.0,
                result="success",
                metadata=self._build_trace_metadata(normalized, parent_id),
            )

        self._finalize_if_root(normalized, context)

    def on_chain_error(self, error, run_id, parent_run_id=None, **kwargs):
        normalized = _normalize_run_id(run_id)
        parent_id = _normalize_run_id(parent_run_id) if parent_run_id else None
        context = self._adapter.get_context_for_run(normalized)
        if context and self._trace_errors:
            self._adapter.trace(
                context,
                decision=LANGCHAIN_ERROR_TRACE_DECISION,
                skill_ref=None,
                reason="LangChain chain failed.",
                confidence=0.0,
                result="error",
                metadata=self._build_trace_metadata(normalized, parent_id, error=error),
            )
        self._rollback_if_root(normalized, context, str(error))

    def on_llm_start(self, serialized, prompts, run_id, parent_run_id=None, **kwargs):
        if not self._trace_llm:
            return
        normalized = _normalize_run_id(run_id)
        parent_id = _normalize_run_id(parent_run_id) if parent_run_id else None
        metadata = kwargs.get("metadata") or {}
        explicit = self._adapter._extract_context_from_metadata(metadata) or self._context
        context = self._adapter._resolve_context(
            run_id=normalized,
            parent_run_id=parent_id,
            actor=self._actor,
            reason=self._reason,
            metadata=self._metadata,
            lineage=self._lineage,
            idempotency_key=self._idempotency_key,
            tx_scope=self._tx_scope,
            correlation_id=self._correlation_id,
            explicit_context=explicit,
        )
        self._register_run_state(
            run_id=normalized,
            parent_run_id=parent_id,
            serialized=serialized,
            context=context,
        )
        self._adapter.trace(
            context,
            decision=LANGCHAIN_LLM_TRACE_DECISION,
            skill_ref=None,
            reason="LangChain LLM started.",
            confidence=1.0,
            result="start",
            metadata=self._build_trace_metadata(normalized, parent_id),
        )

    def on_llm_end(self, response, run_id, parent_run_id=None, **kwargs):
        if not self._trace_llm:
            return
        normalized = _normalize_run_id(run_id)
        parent_id = _normalize_run_id(parent_run_id) if parent_run_id else None
        context = self._adapter.get_context_for_run(normalized)
        if context:
            self._adapter.trace(
                context,
                decision=LANGCHAIN_LLM_TRACE_DECISION,
                skill_ref=None,
                reason="LangChain LLM completed.",
                confidence=1.0,
                result="success",
                metadata=self._build_trace_metadata(normalized, parent_id),
            )

    def on_llm_error(self, error, run_id, parent_run_id=None, **kwargs):
        if not self._trace_errors:
            return
        normalized = _normalize_run_id(run_id)
        parent_id = _normalize_run_id(parent_run_id) if parent_run_id else None
        context = self._adapter.get_context_for_run(normalized)
        if context:
            self._adapter.trace(
                context,
                decision=LANGCHAIN_LLM_TRACE_DECISION,
                skill_ref=None,
                reason="LangChain LLM failed.",
                confidence=0.0,
                result="error",
                metadata=self._build_trace_metadata(normalized, parent_id, error=error),
            )

    def on_tool_start(self, serialized, input_str, run_id, parent_run_id=None, **kwargs):
        if not self._trace_tools:
            return
        normalized = _normalize_run_id(run_id)
        parent_id = _normalize_run_id(parent_run_id) if parent_run_id else None
        metadata = kwargs.get("metadata") or {}
        explicit = self._adapter._extract_context_from_metadata(metadata) or self._context
        context = self._adapter._resolve_context(
            run_id=normalized,
            parent_run_id=parent_id,
            actor=self._actor,
            reason=self._reason,
            metadata=self._metadata,
            lineage=self._lineage,
            idempotency_key=self._idempotency_key,
            tx_scope=self._tx_scope,
            correlation_id=self._correlation_id,
            explicit_context=explicit,
        )
        self._register_run_state(
            run_id=normalized,
            parent_run_id=parent_id,
            serialized=serialized,
            context=context,
        )
        self._adapter.trace(
            context,
            decision=LANGCHAIN_TOOL_TRACE_DECISION,
            skill_ref=None,
            reason="LangChain tool started.",
            confidence=1.0,
            result="start",
            metadata=self._build_trace_metadata(normalized, parent_id),
        )

    def on_tool_end(self, output, run_id, parent_run_id=None, **kwargs):
        if not self._trace_tools:
            return
        normalized = _normalize_run_id(run_id)
        parent_id = _normalize_run_id(parent_run_id) if parent_run_id else None
        context = self._adapter.get_context_for_run(normalized)
        if context:
            self._adapter.trace(
                context,
                decision=LANGCHAIN_TOOL_TRACE_DECISION,
                skill_ref=None,
                reason="LangChain tool completed.",
                confidence=1.0,
                result="success",
                metadata=self._build_trace_metadata(normalized, parent_id),
            )

    def on_tool_error(self, error, run_id, parent_run_id=None, **kwargs):
        if not self._trace_errors:
            return
        normalized = _normalize_run_id(run_id)
        parent_id = _normalize_run_id(parent_run_id) if parent_run_id else None
        context = self._adapter.get_context_for_run(normalized)
        if context:
            self._adapter.trace(
                context,
                decision=LANGCHAIN_TOOL_TRACE_DECISION,
                skill_ref=None,
                reason="LangChain tool failed.",
                confidence=0.0,
                result="error",
                metadata=self._build_trace_metadata(normalized, parent_id, error=error),
            )

    def _build_trace_metadata(
        self,
        run_id: str,
        parent_run_id: Optional[str],
        *,
        error: Optional[BaseException] = None,
    ) -> Dict[str, Any]:
        root_id = self._root_by_run.get(run_id)
        state = self._root_states.get(root_id) if root_id else None
        metadata: Dict[str, Any] = {
            "run_id": run_id,
            "parent_run_id": parent_run_id,
            "name": state.run_names.get(run_id, "") if state else "",
        }
        started = state.run_started.get(run_id) if state else None
        if started is not None:
            metadata["duration_ms"] = int((time.perf_counter() - started) * 1000)
        if error is not None:
            metadata["error"] = str(error)
            metadata["exception"] = repr(error)
        return metadata

    def _finalize_if_root(self, run_id: str, context: Optional[LangChainContext]) -> None:
        root_id = self._root_by_run.get(run_id)
        if root_id != run_id or not self._finalize:
            return
        state = self._root_states.get(root_id)
        if not state or state.finalized:
            return
        if context is None:
            state.finalized = True
            self._cleanup_root(root_id)
            return
        try:
            self._adapter.validate_and_finalize(
                context,
                pipeline=self._finalize_pipeline,
                context_metadata=self._finalize_context_metadata,
                memory_limit=self._finalize_memory_limit,
                approved_status=self._finalize_approved_status,
                rollback_reason=self._finalize_rollback_reason,
            )
        finally:
            state.finalized = True
            self._cleanup_root(root_id)

    def _rollback_if_root(
        self,
        run_id: str,
        context: Optional[LangChainContext],
        reason: str,
    ) -> None:
        root_id = self._root_by_run.get(run_id)
        if root_id != run_id or not self._rollback_on_error:
            return
        state = self._root_states.get(root_id)
        if not state or state.finalized:
            return
        if context is None:
            state.finalized = True
            self._cleanup_root(root_id)
            return
        record = self._adapter.storage.get_transaction(context.tx_id)
        if record.status in (TX_COMMITTED, TX_ROLLED_BACK):
            state.finalized = True
            self._cleanup_root(root_id)
            return
        self._adapter.rollback(context, reason)
        state.finalized = True
        self._cleanup_root(root_id)


def _extract_name(serialized: Any) -> str:
    if isinstance(serialized, dict):
        name = serialized.get("name") or serialized.get("id") or ""
        if isinstance(name, str):
            return name
    return ""

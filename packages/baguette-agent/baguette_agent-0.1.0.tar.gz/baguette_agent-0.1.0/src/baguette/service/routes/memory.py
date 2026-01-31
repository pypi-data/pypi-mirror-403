from __future__ import annotations

from typing import Any, Dict, Optional

from ...api import (
    memory_query,
    memory_redact,
    memory_redact_with_policy,
    memory_resolve,
    memory_scan_pii,
    memory_snapshot,
)
from ...memory import (
    MemoryConflictError,
    RedactionPolicy,
    configure_memory_type_registry,
    get_memory_type_registry,
    register_memory_types,
)


def register(app, storage, _raise_http, Body, Query) -> None:
    @app.get("/memory")
    def list_memory(
        key: Optional[str] = Query(default=None),
        entry_type: Optional[str] = Query(default=None),
        source: Optional[str] = Query(default=None),
        created_after: Optional[str] = Query(default=None),
        created_before: Optional[str] = Query(default=None),
        min_confidence: Optional[float] = Query(default=None),
        max_confidence: Optional[float] = Query(default=None),
        limit: int = Query(default=100),
    ) -> Dict[str, Any]:
        try:
            entries = [
                entry.to_dict()
                for entry in memory_query(
                    storage,
                    key=key,
                    entry_type=entry_type,
                    source=source,
                    created_after=created_after,
                    created_before=created_before,
                    min_confidence=min_confidence,
                    max_confidence=max_confidence,
                    limit=limit,
                )
            ]
            return {"entries": entries}
        except Exception as exc:
            _raise_http(exc)

    @app.post("/memory/resolve")
    def resolve_memory(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        try:
            result = memory_resolve(
                storage,
                key=payload.get("key"),
                entry_type=payload.get("entry_type"),
                source=payload.get("source"),
                created_after=payload.get("created_after"),
                created_before=payload.get("created_before"),
                min_confidence=payload.get("min_confidence"),
                max_confidence=payload.get("max_confidence"),
                limit=int(payload.get("limit", 100)),
                strategy=payload.get("strategy", "latest"),
            )
            return {
                "strategy": result.strategy,
                "resolved": [entry.to_dict() for entry in result.resolved],
                "conflicts": [
                    {
                        "key": conflict.key,
                        "entry_type": conflict.entry_type,
                        "values": conflict.values,
                        "entries": [entry.to_dict() for entry in conflict.entries],
                    }
                    for conflict in result.conflicts
                ],
            }
        except MemoryConflictError as exc:
            _raise_http(ValueError(str(exc)))
        except Exception as exc:
            _raise_http(exc)

    @app.post("/memory/pii/scan")
    def scan_pii(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        try:
            matches = memory_scan_pii(
                storage,
                key=payload.get("key"),
                entry_type=payload.get("entry_type"),
                source=payload.get("source"),
                created_after=payload.get("created_after"),
                created_before=payload.get("created_before"),
                min_confidence=payload.get("min_confidence"),
                max_confidence=payload.get("max_confidence"),
                limit=int(payload.get("limit", 100)),
                patterns=payload.get("patterns"),
                allowlist_keys=payload.get("allowlist_keys"),
                allowlist_types=payload.get("allowlist_types"),
                max_matches=int(payload.get("max_matches", 50)),
            )
            return {"matches": matches}
        except Exception as exc:
            _raise_http(exc)

    @app.post("/memory/redact")
    def redact_memory(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        try:
            entry_id = payload.get("entry_id", "")
            reason = payload.get("reason", "")
            if not entry_id or not reason:
                raise ValueError("entry_id and reason are required.")
            redacted_value = payload.get("redacted_value", "[REDACTED]")
            actor = payload.get("actor")
            rule = payload.get("rule")
            extra_metadata = payload.get("metadata")
            entry = memory_redact(
                storage,
                entry_id=entry_id,
                reason=reason,
                actor=actor,
                rule=rule,
                redacted_value=redacted_value,
                extra_metadata=extra_metadata,
            )
            return entry.to_dict()
        except Exception as exc:
            _raise_http(exc)

    @app.post("/memory/redact/policy")
    def redact_memory_policy(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        try:
            policy_payload = payload.get("policy")
            if not policy_payload:
                raise ValueError("policy is required.")
            policy = RedactionPolicy.from_dict(policy_payload)
            reason = payload.get("reason", "")
            if not reason:
                raise ValueError("reason is required.")
            report = memory_redact_with_policy(
                storage,
                policy=policy,
                key=payload.get("key"),
                entry_type=payload.get("entry_type"),
                source=payload.get("source"),
                created_after=payload.get("created_after"),
                created_before=payload.get("created_before"),
                min_confidence=payload.get("min_confidence"),
                max_confidence=payload.get("max_confidence"),
                limit=int(payload.get("limit", 100)),
                reason=reason,
                actor=payload.get("actor"),
                dry_run=bool(payload.get("dry_run", False)),
            )
            return {
                "dry_run": bool(payload.get("dry_run", False)),
                "changes": report.to_dict().get("changes", []),
            }
        except Exception as exc:
            _raise_http(exc)

    @app.post("/memory/snapshot")
    def snapshot_memory(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        try:
            snapshot = memory_snapshot(
                storage,
                key=payload.get("key"),
                entry_type=payload.get("entry_type"),
                source=payload.get("source"),
                created_after=payload.get("created_after"),
                created_before=payload.get("created_before"),
                min_confidence=payload.get("min_confidence"),
                max_confidence=payload.get("max_confidence"),
                limit=int(payload.get("limit", 100)),
            )
            return snapshot
        except Exception as exc:
            _raise_http(exc)

    @app.get("/memory/types")
    def get_memory_types() -> Dict[str, Any]:
        try:
            registry = get_memory_type_registry()
            return registry.to_dict()
        except Exception as exc:
            _raise_http(exc)

    @app.post("/memory/types")
    def configure_memory_types(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        try:
            mode = payload.get("mode")
            set_types = payload.get("types")
            add_types = payload.get("add_types") or []
            prefixes = payload.get("custom_prefixes")

            if set_types is not None and not isinstance(set_types, list):
                raise ValueError("types must be a list.")
            if add_types and not isinstance(add_types, list):
                raise ValueError("add_types must be a list.")
            if prefixes is not None and not isinstance(prefixes, list):
                raise ValueError("custom_prefixes must be a list.")

            if mode or set_types is not None or prefixes is not None:
                configure_memory_type_registry(
                    mode=mode,
                    types=set_types,
                    custom_prefixes=prefixes,
                )
            if add_types:
                register_memory_types(*add_types)

            return get_memory_type_registry().to_dict()
        except Exception as exc:
            _raise_http(exc)

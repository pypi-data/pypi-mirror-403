from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from .audit import DecisionTrace, JournalEvent
from .memory import (
    MemoryEntry,
    RedactionPolicy,
    RedactionReport,
    ResolutionResult,
    TransactionRecord,
    ValidationPipeline,
    ValidationRecord,
    apply_redaction,
    build_redaction_metadata,
    resolve_conflicts,
    scan_pii_entries,
)
from .skills import SkillArtifact, load_skill_file
from .storage.base import StorageBackend
from .utils import utcnow_iso


def begin(
    storage: StorageBackend,
    *,
    actor: str,
    reason: str,
    metadata: Optional[Dict[str, Any]] = None,
    idempotency_key: Optional[str] = None,
    lineage: Optional[Dict[str, Any]] = None,
) -> str:
    return storage.begin_transaction(
        actor=actor,
        reason=reason,
        metadata=metadata,
        idempotency_key=idempotency_key,
        lineage=lineage,
    )


def stage(
    storage: StorageBackend,
    *,
    tx_id: str,
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
        tx_id=tx_id,
    )
    storage.stage_memory(tx_id, entry)
    return entry


def validate(
    storage: StorageBackend,
    *,
    tx_id: str,
    status: str,
    confidence: float,
    evidence: str,
    validator: str,
    metadata: Optional[Dict[str, Any]] = None,
    idempotency_key: Optional[str] = None,
) -> ValidationRecord:
    record = ValidationRecord(
        status=status,
        confidence=confidence,
        evidence=evidence,
        validator=validator,
        metadata=metadata or {},
        idempotency_key=idempotency_key,
    )
    storage.validate_transaction(tx_id, record)
    return record


def validate_with_pipeline(
    storage: StorageBackend,
    *,
    tx_id: str,
    pipeline: ValidationPipeline,
    context_metadata: Optional[Dict[str, Any]] = None,
    memory_limit: int = 50,
) -> ValidationRecord:
    entries = list(storage.list_staged_memory(tx_id))
    memory_lookup = lambda key: storage.list_memory(key=key, limit=memory_limit)
    record = pipeline.run(
        tx_id=tx_id,
        entries=entries,
        memory_lookup=memory_lookup,
        context_metadata=context_metadata,
    )
    storage.validate_transaction(tx_id, record)
    return record


def commit(
    storage: StorageBackend,
    *,
    tx_id: str,
    validation: Optional[ValidationRecord] = None,
    supersede: bool = False,
) -> None:
    storage.commit_transaction(tx_id, validation, supersede=supersede)


def rollback(storage: StorageBackend, *, tx_id: str, reason: str) -> None:
    storage.rollback_transaction(tx_id, reason)


def tx_status(storage: StorageBackend, *, tx_id: str) -> TransactionRecord:
    return storage.get_transaction(tx_id)


def staged_memory_query(
    storage: StorageBackend,
    *,
    tx_id: str,
    key: str | None = None,
    entry_type: str | None = None,
    source: str | None = None,
    min_confidence: float | None = None,
    max_confidence: float | None = None,
    limit: int = 100,
) -> Iterable[MemoryEntry]:
    return storage.list_staged_memory(
        tx_id,
        key=key,
        entry_type=entry_type,
        source=source,
        min_confidence=min_confidence,
        max_confidence=max_confidence,
        limit=limit,
    )


def artifact_publish(
    storage: StorageBackend,
    *,
    path: str,
    name: Optional[str] = None,
    version: Optional[str] = None,
    skill_type: Optional[str] = None,
    lineage: Optional[Dict[str, Any]] = None,
    idempotency_key: Optional[str] = None,
) -> SkillArtifact:
    artifact = load_skill_file(
        path,
        name=name,
        version=version,
        skill_type=skill_type,
        lineage=lineage,
        idempotency_key=idempotency_key,
    )
    storage.upsert_skill(artifact)
    return artifact


def artifact_get(storage: StorageBackend, *, name: str, version: Optional[str] = None) -> SkillArtifact:
    return storage.get_skill(name, version)


def trace_log(
    storage: StorageBackend,
    *,
    decision: str,
    skill_ref: Optional[str],
    reason: str,
    confidence: float,
    result: str,
    metadata: Optional[Dict[str, Any]] = None,
    tx_id: Optional[str] = None,
    lineage: Optional[Dict[str, Any]] = None,
    idempotency_key: Optional[str] = None,
) -> DecisionTrace:
    trace = DecisionTrace.new(
        decision=decision,
        skill_ref=skill_ref,
        reason=reason,
        confidence=confidence,
        result=result,
        metadata=metadata,
        tx_id=tx_id,
        lineage=lineage,
        idempotency_key=idempotency_key,
    )
    storage.record_trace(trace)
    return trace


def trace_query(
    storage: StorageBackend,
    *,
    limit: int = 100,
    tx_id: Optional[str] = None,
    decision: Optional[str] = None,
    skill_ref: Optional[str] = None,
    result: Optional[str] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> Iterable[DecisionTrace]:
    return storage.list_traces(
        limit=limit,
        tx_id=tx_id,
        decision=decision,
        skill_ref=skill_ref,
        result=result,
        created_after=created_after,
        created_before=created_before,
        correlation_id=correlation_id,
    )


def journal_query(
    storage: StorageBackend,
    *,
    limit: int = 100,
    tx_id: Optional[str] = None,
    event_type: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
) -> Iterable[JournalEvent]:
    return storage.list_journal(
        limit=limit,
        tx_id=tx_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
    )


def journal_replay(
    storage: StorageBackend,
    *,
    limit: int = 100,
    tx_id: Optional[str] = None,
    event_type: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
) -> Iterable[JournalEvent]:
    events = list(
        storage.list_journal(
            limit=limit,
            tx_id=tx_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
        )
    )
    for event in reversed(events):
        yield event


def memory_query(
    storage: StorageBackend,
    *,
    key: str | None = None,
    entry_type: str | None = None,
    source: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    min_confidence: float | None = None,
    max_confidence: float | None = None,
    limit: int = 100,
) -> Iterable[MemoryEntry]:
    return storage.list_memory(
        key=key,
        entry_type=entry_type,
        source=source,
        created_after=created_after,
        created_before=created_before,
        min_confidence=min_confidence,
        max_confidence=max_confidence,
        limit=limit,
    )


def memory_resolve(
    storage: StorageBackend,
    *,
    key: str | None = None,
    entry_type: str | None = None,
    source: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    min_confidence: float | None = None,
    max_confidence: float | None = None,
    limit: int = 100,
    strategy: str = "latest",
) -> ResolutionResult:
    entries = list(
        memory_query(
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
    )
    return resolve_conflicts(entries, strategy=strategy)


def memory_scan_pii(
    storage: StorageBackend,
    *,
    key: str | None = None,
    entry_type: str | None = None,
    source: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    min_confidence: float | None = None,
    max_confidence: float | None = None,
    limit: int = 100,
    patterns: list[str] | None = None,
    allowlist_keys: list[str] | None = None,
    allowlist_types: list[str] | None = None,
    max_matches: int = 50,
) -> list[dict[str, Any]]:
    entries = list(
        memory_query(
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
    )
    return scan_pii_entries(
        entries,
        patterns=patterns,
        allowlist_keys=allowlist_keys,
        allowlist_types=allowlist_types,
        max_matches=max_matches,
    )


def memory_redact(
    storage: StorageBackend,
    *,
    entry_id: str,
    reason: str,
    actor: str | None = None,
    rule: str | None = None,
    redacted_value: Any = "[REDACTED]",
    extra_metadata: dict[str, Any] | None = None,
) -> MemoryEntry:
    metadata = build_redaction_metadata(
        reason=reason,
        actor=actor,
        rule=rule,
        extra=extra_metadata,
    )
    return storage.redact_memory(
        entry_id,
        redacted_value=redacted_value,
        metadata=metadata,
    )


def memory_snapshot(
    storage: StorageBackend,
    *,
    key: str | None = None,
    entry_type: str | None = None,
    source: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    min_confidence: float | None = None,
    max_confidence: float | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    entries = list(
        memory_query(
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
    )
    return {
        "generated_at": utcnow_iso(),
        "filters": {
            "key": key,
            "entry_type": entry_type,
            "source": source,
            "created_after": created_after,
            "created_before": created_before,
            "min_confidence": min_confidence,
            "max_confidence": max_confidence,
            "limit": limit,
        },
        "entries": [entry.to_dict() for entry in entries],
    }


def memory_redact_with_policy(
    storage: StorageBackend,
    *,
    policy: RedactionPolicy,
    key: str | None = None,
    entry_type: str | None = None,
    source: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    min_confidence: float | None = None,
    max_confidence: float | None = None,
    limit: int = 100,
    reason: str,
    actor: str | None = None,
    dry_run: bool = False,
) -> RedactionReport:
    entries = list(
        memory_query(
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
    )
    report = apply_redaction(entries, policy=policy)
    if dry_run:
        return report

    for change in report.changes:
        metadata = build_redaction_metadata(
            reason=reason,
            actor=actor,
            rule="policy",
            extra={
                "redaction_policy_version": policy.version,
                "redaction_rules": change.rules,
                "redaction_matches": [match.to_dict() for match in change.matches],
            },
        )
        storage.redact_memory(
            change.entry_id,
            redacted_value=change.redacted_value,
            metadata=metadata,
        )

    return report

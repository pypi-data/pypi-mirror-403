from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import uuid

from ..schema import SkillSchemaError, validate_memory_entry, validate_transaction
from .types import get_memory_type_registry
from ..utils import canonical_json, derive_idempotency_key, deterministic_uuid, utcnow_iso

TX_OPEN = "OPEN"
TX_VALIDATED = "VALIDATED"
TX_COMMITTED = "COMMITTED"
TX_ROLLED_BACK = "ROLLED_BACK"

_TX_STATUSES = {TX_OPEN, TX_VALIDATED, TX_COMMITTED, TX_ROLLED_BACK}

TX_SCOPE_RUN = "run"
TX_SCOPE_SUBGRAPH = "subgraph"

_TX_SCOPES = {TX_SCOPE_RUN, TX_SCOPE_SUBGRAPH}


def _require_non_empty(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")


def _validate_confidence(confidence: float) -> None:
    if not isinstance(confidence, (float, int)):
        raise ValueError("confidence must be a number.")
    if not 0.0 <= float(confidence) <= 1.0:
        raise ValueError("confidence must be between 0.0 and 1.0.")


def _ensure_dict(value: Any, field_name: str) -> Dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a dictionary.")
    canonical_json(value)
    return value


def _derive_memory_idempotency_fields(
    *,
    key: str,
    entry_type: str,
    source: str,
    value: Any,
    metadata: Dict[str, Any],
    tx_id: Optional[str],
) -> str:
    parts = [
        key,
        entry_type,
        source,
        canonical_json(value),
        canonical_json(metadata),
    ]
    if tx_id:
        parts.append(tx_id)
    return derive_idempotency_key(*parts)


def _derive_memory_idempotency(entry: "MemoryEntry") -> str:
    return _derive_memory_idempotency_fields(
        key=entry.key,
        entry_type=entry.type,
        source=entry.source,
        value=entry.value,
        metadata=entry.metadata,
        tx_id=entry.tx_id,
    )


@dataclass
class MemoryEntry:
    entry_id: str
    idempotency_key: str
    key: str
    value: Any
    type: str
    source: str
    confidence: float
    created_at: str = field(default_factory=utcnow_iso)
    metadata: Dict[str, Any] = field(default_factory=dict)
    lineage: Dict[str, Any] = field(default_factory=dict)
    tx_id: Optional[str] = None

    def __post_init__(self) -> None:
        _require_non_empty(self.key, "key")
        _require_non_empty(self.type, "type")
        _require_non_empty(self.source, "source")
        _validate_confidence(self.confidence)
        get_memory_type_registry().validate(self.type)

        canonical_json(self.value)
        self.metadata = _ensure_dict(self.metadata, "metadata")
        self.lineage = _ensure_dict(self.lineage, "lineage")

        if not self.idempotency_key:
            self.idempotency_key = _derive_memory_idempotency(self)
        if not self.entry_id:
            self.entry_id = deterministic_uuid("memory_entry", self.idempotency_key)
        try:
            validate_memory_entry(self.to_dict())
        except SkillSchemaError as exc:
            raise ValueError(str(exc)) from exc

    @classmethod
    def new(
        cls,
        *,
        key: str,
        value: Any,
        type: str,
        source: str,
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None,
        lineage: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        tx_id: Optional[str] = None,
    ) -> "MemoryEntry":
        return cls(
            entry_id="",
            idempotency_key=idempotency_key or "",
            key=key,
            value=value,
            type=type,
            source=source,
            confidence=confidence,
            metadata=metadata or {},
            lineage=lineage or {},
            tx_id=tx_id,
        )

    def scope_to_tx(self, tx_id: str) -> "MemoryEntry":
        _require_non_empty(tx_id, "tx_id")

        if self.tx_id:
            if self.tx_id != tx_id:
                raise ValueError(
                    f"MemoryEntry already scoped to tx_id {self.tx_id}; cannot reuse for {tx_id}."
                )
            if "tx_id" not in self.lineage:
                self.lineage["tx_id"] = tx_id
            return self

        default_idempotency = _derive_memory_idempotency_fields(
            key=self.key,
            entry_type=self.type,
            source=self.source,
            value=self.value,
            metadata=self.metadata,
            tx_id=None,
        )
        self.tx_id = tx_id
        if "tx_id" not in self.lineage:
            self.lineage["tx_id"] = tx_id
        if self.idempotency_key == default_idempotency:
            self.idempotency_key = _derive_memory_idempotency_fields(
                key=self.key,
                entry_type=self.type,
                source=self.source,
                value=self.value,
                metadata=self.metadata,
                tx_id=tx_id,
            )
            self.entry_id = deterministic_uuid("memory_entry", self.idempotency_key)

        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "idempotency_key": self.idempotency_key,
            "key": self.key,
            "value": self.value,
            "type": self.type,
            "source": self.source,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "metadata": self.metadata,
            "lineage": self.lineage,
            "tx_id": self.tx_id,
        }


@dataclass
class ValidationRecord:
    status: str
    confidence: float
    evidence: str
    validator: str
    validated_at: str = field(default_factory=utcnow_iso)
    metadata: Dict[str, Any] = field(default_factory=dict)
    idempotency_key: Optional[str] = None

    def __post_init__(self) -> None:
        _require_non_empty(self.status, "status")
        _require_non_empty(self.evidence, "evidence")
        _require_non_empty(self.validator, "validator")
        _validate_confidence(self.confidence)
        self.metadata = _ensure_dict(self.metadata, "metadata")
        if not self.idempotency_key:
            self.idempotency_key = derive_idempotency_key(
                self.status,
                self.validator,
                self.evidence,
                canonical_json(self.metadata),
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "validator": self.validator,
            "validated_at": self.validated_at,
            "metadata": self.metadata,
            "idempotency_key": self.idempotency_key,
        }


@dataclass
class TransactionRecord:
    tx_id: str
    idempotency_key: str
    actor: str
    reason: str
    status: str = TX_OPEN
    created_at: str = field(default_factory=utcnow_iso)
    updated_at: str = field(default_factory=utcnow_iso)
    committed_at: Optional[str] = None
    rolled_back_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    lineage: Dict[str, Any] = field(default_factory=dict)
    validation: Optional[ValidationRecord] = None

    def __post_init__(self) -> None:
        _require_non_empty(self.tx_id, "tx_id")
        _require_non_empty(self.actor, "actor")
        _require_non_empty(self.reason, "reason")
        if self.status not in _TX_STATUSES:
            raise ValueError(f"Invalid transaction status: {self.status}")
        if not self.idempotency_key:
            self.idempotency_key = self.tx_id
        self.metadata = _ensure_dict(self.metadata, "metadata")
        self.lineage = _ensure_dict(self.lineage, "lineage")
        try:
            validate_transaction(self.to_dict())
        except SkillSchemaError as exc:
            raise ValueError(str(exc)) from exc

    @classmethod
    def new(
        cls,
        *,
        actor: str,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
        lineage: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> "TransactionRecord":
        created_at = utcnow_iso()
        tx_id = str(uuid.uuid4())
        return cls(
            tx_id=tx_id,
            idempotency_key=idempotency_key or tx_id,
            actor=actor,
            reason=reason,
            metadata=metadata or {},
            lineage=lineage or {},
            created_at=created_at,
            updated_at=created_at,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tx_id": self.tx_id,
            "idempotency_key": self.idempotency_key,
            "actor": self.actor,
            "reason": self.reason,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "committed_at": self.committed_at,
            "rolled_back_at": self.rolled_back_at,
            "metadata": self.metadata,
            "lineage": self.lineage,
            "validation": self.validation.to_dict() if self.validation else None,
        }

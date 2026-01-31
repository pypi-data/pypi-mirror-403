from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from ..utils import canonical_json


def _require_non_empty(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")


def _ensure_dict(value: Any, field_name: str) -> Dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a dictionary.")
    canonical_json(value)
    return value


@dataclass
class JournalEvent:
    event_id: str
    timestamp: str
    event_type: str
    entity_type: str
    entity_id: str
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    tx_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    seq: Optional[int] = None

    def __post_init__(self) -> None:
        _require_non_empty(self.event_id, "event_id")
        _require_non_empty(self.timestamp, "timestamp")
        _require_non_empty(self.event_type, "event_type")
        _require_non_empty(self.entity_type, "entity_type")
        _require_non_empty(self.entity_id, "entity_id")
        self.payload = _ensure_dict(self.payload, "payload")
        self.metadata = _ensure_dict(self.metadata, "metadata")
        if self.seq is not None and not isinstance(self.seq, int):
            raise ValueError("seq must be an integer when provided.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "tx_id": self.tx_id,
            "idempotency_key": self.idempotency_key,
            "payload": self.payload,
            "metadata": self.metadata,
            "seq": self.seq,
        }

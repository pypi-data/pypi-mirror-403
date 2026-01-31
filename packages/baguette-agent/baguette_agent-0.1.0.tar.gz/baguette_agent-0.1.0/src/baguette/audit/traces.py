from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import uuid

from ..schema import SkillSchemaError, validate_decision_trace
from ..utils import canonical_json, deterministic_uuid, utcnow_iso


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


@dataclass
class DecisionTrace:
    trace_id: str
    idempotency_key: str
    timestamp: str
    decision: str
    skill_ref: Optional[str]
    reason: str
    confidence: float
    result: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    tx_id: Optional[str] = None
    lineage: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty(self.trace_id, "trace_id")
        _require_non_empty(self.decision, "decision")
        _require_non_empty(self.result, "result")
        _validate_confidence(self.confidence)
        self.metadata = _ensure_dict(self.metadata, "metadata")
        self.lineage = _ensure_dict(self.lineage, "lineage")
        if not self.idempotency_key:
            self.idempotency_key = self.trace_id
        try:
            validate_decision_trace(self.to_dict())
        except SkillSchemaError as exc:
            raise ValueError(str(exc)) from exc

    @classmethod
    def new(
        cls,
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
    ) -> "DecisionTrace":
        if idempotency_key:
            trace_id = deterministic_uuid("decision_trace", idempotency_key)
            derived_idempotency = idempotency_key
        else:
            trace_id = str(uuid.uuid4())
            derived_idempotency = trace_id
        return cls(
            trace_id=trace_id,
            idempotency_key=derived_idempotency,
            timestamp=utcnow_iso(),
            decision=decision,
            skill_ref=skill_ref,
            reason=reason,
            confidence=confidence,
            result=result,
            metadata=metadata or {},
            tx_id=tx_id,
            lineage=lineage or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "idempotency_key": self.idempotency_key,
            "timestamp": self.timestamp,
            "decision": self.decision,
            "skill_ref": self.skill_ref,
            "reason": self.reason,
            "confidence": self.confidence,
            "result": self.result,
            "metadata": self.metadata,
            "tx_id": self.tx_id,
            "lineage": self.lineage,
        }

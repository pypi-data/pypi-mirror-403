from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Optional
import json

from .transactions import MemoryEntry
from ..utils import canonical_json
from .validation import ValidationContext, Verifier, VerifierResult


def build_verifier_prompt(entries: Iterable[MemoryEntry], context: ValidationContext) -> str:
    payload = {
        "tx_id": context.tx_id,
        "metadata": context.metadata,
        "entries": [
            {
                "entry_id": entry.entry_id,
                "key": entry.key,
                "type": entry.type,
                "value": entry.value,
                "source": entry.source,
                "confidence": entry.confidence,
                "lineage": entry.lineage,
            }
            for entry in entries
        ],
    }
    serialized = canonical_json(payload)
    return (
        "You are a validation verifier. Review the staged memory updates and return JSON with "
        "fields: status, confidence (0-1), evidence. Input:\n"
        f"{serialized}"
    )


@dataclass
class LLMVerifierAgent(Verifier):
    client: Callable[[str], Any]
    validator_id: str = "llm_verifier"
    default_status: str = "needs_review"

    def verify(self, entries: Iterable[MemoryEntry], context: ValidationContext) -> VerifierResult:
        prompt = build_verifier_prompt(entries, context)
        response = self.client(prompt)
        parsed = _parse_response(response)
        if parsed:
            status, confidence, evidence, metadata = parsed
            return VerifierResult(
                status=status,
                confidence=confidence,
                evidence=evidence,
                metadata=metadata,
            )

        evidence = _stringify_response(response)
        return VerifierResult(
            status=self.default_status,
            confidence=0.5,
            evidence=evidence or "Verifier response could not be parsed.",
            metadata={"raw_response": response},
        )


def _parse_response(response: Any) -> Optional[tuple[str, float, str, Dict[str, Any]]]:
    data: Optional[Dict[str, Any]] = None
    if isinstance(response, dict):
        data = response
    elif isinstance(response, str):
        try:
            parsed = json.loads(response)
            if isinstance(parsed, dict):
                data = parsed
        except json.JSONDecodeError:
            data = None

    if not data:
        return None

    status = data.get("status")
    evidence = data.get("evidence")
    confidence = data.get("confidence")
    metadata = data.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {}

    if not isinstance(status, str) or not status.strip():
        return None
    if not isinstance(evidence, str):
        return None
    if not isinstance(confidence, (float, int)):
        return None
    confidence_val = max(0.0, min(1.0, float(confidence)))
    return status, confidence_val, evidence, metadata


def _stringify_response(response: Any) -> str:
    if response is None:
        return ""
    if isinstance(response, str):
        return response
    try:
        return json.dumps(response, ensure_ascii=True)
    except TypeError:
        return str(response)

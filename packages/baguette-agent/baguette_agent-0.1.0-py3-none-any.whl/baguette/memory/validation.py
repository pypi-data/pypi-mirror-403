from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Protocol, Tuple
import re

from .transactions import MemoryEntry, ValidationRecord
from ..utils import canonical_json, sha256_text

MemoryLookup = Callable[[str], Iterable[MemoryEntry]]


@dataclass
class ValidationContext:
    tx_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    memory_lookup: Optional[MemoryLookup] = None


@dataclass
class RuleResult:
    name: str
    passed: bool
    confidence: float
    reason: str
    details: Dict[str, Any] = field(default_factory=dict)


class ValidationRule(Protocol):
    name: str

    def evaluate(self, entries: Iterable[MemoryEntry], context: ValidationContext) -> RuleResult:
        ...


class RuleEngine:
    def __init__(self, rules: Iterable[ValidationRule]) -> None:
        self._rules = list(rules)

    def evaluate(self, entries: Iterable[MemoryEntry], context: ValidationContext) -> List[RuleResult]:
        results: List[RuleResult] = []
        for rule in self._rules:
            results.append(rule.evaluate(entries, context))
        return results


class ConfidenceThresholdRule:
    name = "confidence_threshold"

    def __init__(self, threshold: float) -> None:
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Confidence threshold must be between 0.0 and 1.0.")
        self.threshold = threshold

    def evaluate(self, entries: Iterable[MemoryEntry], context: ValidationContext) -> RuleResult:
        failures = []
        for entry in entries:
            if entry.confidence < self.threshold:
                failures.append(
                    {
                        "entry_id": entry.entry_id,
                        "key": entry.key,
                        "confidence": entry.confidence,
                    }
                )

        if failures:
            min_confidence = min(item["confidence"] for item in failures)
            return RuleResult(
                name=self.name,
                passed=False,
                confidence=min_confidence,
                reason=f"Entry confidence below threshold {self.threshold:.2f}.",
                details={"threshold": self.threshold, "failures": failures},
            )

        return RuleResult(
            name=self.name,
            passed=True,
            confidence=1.0,
            reason="Confidence threshold met.",
            details={"threshold": self.threshold},
        )


class ContradictionRule:
    name = "contradiction_check"

    def evaluate(self, entries: Iterable[MemoryEntry], context: ValidationContext) -> RuleResult:
        if not context.memory_lookup:
            return RuleResult(
                name=self.name,
                passed=True,
                confidence=1.0,
                reason="Memory lookup not configured.",
                details={"skipped": True},
            )

        contradictions = []
        for entry in entries:
            existing = list(context.memory_lookup(entry.key))
            if not existing:
                continue
            entry_value = canonical_json(entry.value)
            for stored in existing:
                stored_value = canonical_json(stored.value)
                if stored.type != entry.type or stored_value != entry_value:
                    contradictions.append(
                        {
                            "entry_id": entry.entry_id,
                            "key": entry.key,
                            "incoming": {"type": entry.type, "value": entry.value},
                            "stored": {
                                "entry_id": stored.entry_id,
                                "type": stored.type,
                                "value": stored.value,
                            },
                        }
                    )

        if contradictions:
            return RuleResult(
                name=self.name,
                passed=False,
                confidence=0.0,
                reason="Contradictions detected with existing memory.",
                details={"contradictions": contradictions},
            )

        return RuleResult(
            name=self.name,
            passed=True,
            confidence=1.0,
            reason="No contradictions detected.",
        )


class StagedConflictRule:
    name = "staged_conflict_check"

    def evaluate(self, entries: Iterable[MemoryEntry], context: ValidationContext) -> RuleResult:
        seen: Dict[tuple[str, str], Dict[str, Any]] = {}
        conflicts = []

        for entry in entries:
            key = (entry.key, entry.type)
            value = canonical_json(entry.value)
            existing = seen.get(key)
            if existing and existing["value"] != value:
                conflicts.append(
                    {
                        "key": entry.key,
                        "type": entry.type,
                        "entry_id": entry.entry_id,
                        "value": entry.value,
                        "conflicts_with": {
                            "entry_id": existing["entry_id"],
                            "value": existing["raw_value"],
                        },
                    }
                )
            else:
                seen[key] = {
                    "value": value,
                    "raw_value": entry.value,
                    "entry_id": entry.entry_id,
                }

        if conflicts:
            return RuleResult(
                name=self.name,
                passed=False,
                confidence=0.0,
                reason="Conflicting staged values detected for the same key.",
                details={"conflicts": conflicts},
            )

        return RuleResult(
            name=self.name,
            passed=True,
            confidence=1.0,
            reason="No staged conflicts detected.",
        )


@dataclass
class VerifierResult:
    status: str
    confidence: float
    evidence: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class Verifier(Protocol):
    def verify(self, entries: Iterable[MemoryEntry], context: ValidationContext) -> VerifierResult:
        ...


class StaticVerifier:
    def __init__(self, result: VerifierResult) -> None:
        self._result = result

    def verify(self, entries: Iterable[MemoryEntry], context: ValidationContext) -> VerifierResult:
        return self._result


class ValidationPipeline:
    def __init__(
        self,
        *,
        rule_engine: RuleEngine,
        verifier: Optional[Verifier] = None,
        validator_id: str = "pipeline",
        rule_policies: Optional[Dict[str, Any]] = None,
        require_human_approval: bool = False,
    ) -> None:
        self.rule_engine = rule_engine
        self.verifier = verifier
        self.validator_id = validator_id
        self.rule_policies = rule_policies or {}
        self.require_human_approval = require_human_approval

    @classmethod
    def default(
        cls,
        *,
        confidence_threshold: float = 0.8,
        enable_contradiction_check: bool = True,
        enable_staged_conflict_check: bool = True,
        verifier: Optional[Verifier] = None,
    ) -> "ValidationPipeline":
        rules: List[ValidationRule] = [ConfidenceThresholdRule(confidence_threshold)]
        if enable_contradiction_check:
            rules.append(ContradictionRule())
        if enable_staged_conflict_check:
            rules.append(StagedConflictRule())
        return cls(rule_engine=RuleEngine(rules), verifier=verifier)

    def run(
        self,
        *,
        tx_id: str,
        entries: Iterable[MemoryEntry],
        memory_lookup: Optional[MemoryLookup] = None,
        context_metadata: Optional[Dict[str, Any]] = None,
    ) -> ValidationRecord:
        entry_list = list(entries)
        context = ValidationContext(
            tx_id=tx_id,
            metadata=context_metadata or {},
            memory_lookup=memory_lookup,
        )
        rule_results = self.rule_engine.evaluate(entry_list, context)
        failed_rules = [result for result in rule_results if not result.passed]

        verifier_result: Optional[VerifierResult] = None
        if not failed_rules and self.verifier:
            verifier_result = self.verifier.verify(entry_list, context)

        status = "approved"
        evidence = "All validation rules passed."
        approval_required = False
        approval_reasons: List[str] = []
        rejection_reasons: List[str] = []

        if failed_rules:
            for result in failed_rules:
                policy = self.rule_policies.get(result.name)
                on_fail = getattr(policy, "on_fail", "reject")
                if on_fail == "needs_review":
                    approval_reasons.append(result.reason)
                else:
                    rejection_reasons.append(result.reason)

            if rejection_reasons:
                status = "rejected"
                evidence = "; ".join(rejection_reasons)
            elif approval_reasons:
                status = "needs_review"
                approval_required = True
                evidence = "; ".join(approval_reasons)
        elif self.require_human_approval:
            status = "needs_review"
            approval_required = True
            evidence = "Policy requires human approval."
        elif verifier_result:
            status = verifier_result.status
            evidence = verifier_result.evidence

        confidences = [result.confidence for result in rule_results]
        if verifier_result:
            confidences.append(verifier_result.confidence)
        confidence = min(confidences) if confidences else 1.0

        metadata = {
            "rules": [result.__dict__ for result in rule_results],
            "verifier": verifier_result.__dict__ if verifier_result else None,
        }
        if status == "needs_review":
            metadata["approval_required"] = approval_required or True
            metadata["approval_reasons"] = approval_reasons or [evidence]

        return ValidationRecord(
            status=status,
            confidence=confidence,
            evidence=evidence,
            validator=self.validator_id,
            metadata=metadata,
        )


_DEFAULT_PII_PATTERNS: Dict[str, re.Pattern[str]] = {
    "email": re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE),
    "phone": re.compile(r"\+?\d[\d\s().-]{7,}\d"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
}


def _iter_values(value: Any, path: str = "") -> Iterable[Tuple[str, str]]:
    if isinstance(value, dict):
        for key, item in value.items():
            key_path = f"{path}.{key}" if path else str(key)
            yield from _iter_values(item, key_path)
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            item_path = f"{path}[{idx}]" if path else f"[{idx}]"
            yield from _iter_values(item, item_path)
    elif isinstance(value, str):
        yield path, value
    elif isinstance(value, (int, float)):
        yield path, str(value)


def _luhn_check(value: str) -> bool:
    digits = [int(ch) for ch in value if ch.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for idx, digit in enumerate(digits):
        if idx % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


class PIICheckRule:
    name = "pii_check"

    def __init__(
        self,
        *,
        patterns: Optional[List[str]] = None,
        allowlist_keys: Optional[List[str]] = None,
        allowlist_types: Optional[List[str]] = None,
        max_matches: int = 5,
    ) -> None:
        self.pattern_names = patterns or list(_DEFAULT_PII_PATTERNS.keys())
        self.allowlist_keys = set(allowlist_keys or [])
        self.allowlist_types = set(allowlist_types or [])
        self.max_matches = max(1, int(max_matches))

        self._patterns: List[Tuple[str, re.Pattern[str]]] = []
        for name in self.pattern_names:
            if name in _DEFAULT_PII_PATTERNS:
                self._patterns.append((name, _DEFAULT_PII_PATTERNS[name]))
            else:
                self._patterns.append((name, re.compile(name)))

    def evaluate(self, entries: Iterable[MemoryEntry], context: ValidationContext) -> RuleResult:
        matches = []
        for entry in entries:
            if entry.key in self.allowlist_keys or entry.type in self.allowlist_types:
                continue

            for path, value in _iter_values(entry.value):
                for name, pattern in self._patterns:
                    if not pattern.search(value):
                        continue
                    if name == "credit_card" and not _luhn_check(value):
                        continue
                    matches.append(
                        {
                            "entry_id": entry.entry_id,
                            "key": entry.key,
                            "path": path,
                            "pattern": name,
                            "value_hash": sha256_text(value),
                        }
                    )
                    if len(matches) >= self.max_matches:
                        break
                if len(matches) >= self.max_matches:
                    break
            if len(matches) >= self.max_matches:
                break

        if matches:
            return RuleResult(
                name=self.name,
                passed=False,
                confidence=0.0,
                reason="Possible PII detected in staged memory.",
                details={"matches": matches, "max_matches": self.max_matches},
            )

        return RuleResult(
            name=self.name,
            passed=True,
            confidence=1.0,
            reason="No PII detected.",
        )

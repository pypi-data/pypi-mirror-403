from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from .transactions import MemoryEntry
from .validation import PIICheckRule, ValidationContext
from ..utils import canonical_json, utcnow_iso


class MemoryConflictError(RuntimeError):
    pass


@dataclass
class MemoryConflict:
    key: str
    entry_type: str
    entries: List[MemoryEntry]
    values: List[str]


@dataclass
class ResolutionResult:
    resolved: List[MemoryEntry]
    conflicts: List[MemoryConflict]
    strategy: str


def _sort_key_latest(entry: MemoryEntry) -> tuple[str, float, str]:
    return (entry.created_at, float(entry.confidence), entry.entry_id)


def _sort_key_confidence(entry: MemoryEntry) -> tuple[float, str, str]:
    return (float(entry.confidence), entry.created_at, entry.entry_id)


def _select_entry(entries: List[MemoryEntry], strategy: str) -> MemoryEntry:
    if strategy == "highest_confidence":
        return sorted(entries, key=_sort_key_confidence, reverse=True)[0]
    return sorted(entries, key=_sort_key_latest, reverse=True)[0]


def resolve_conflicts(
    entries: Iterable[MemoryEntry],
    *,
    strategy: str = "latest",
) -> ResolutionResult:
    if strategy not in {"latest", "highest_confidence", "reject"}:
        raise ValueError(f"Unknown conflict resolution strategy: {strategy}")

    grouped: Dict[tuple[str, str], List[MemoryEntry]] = {}
    for entry in entries:
        grouped.setdefault((entry.key, entry.type), []).append(entry)

    resolved: List[MemoryEntry] = []
    conflicts: List[MemoryConflict] = []

    for (key, entry_type), items in grouped.items():
        values = [canonical_json(item.value) for item in items]
        unique_values = sorted(set(values))
        if len(unique_values) > 1:
            conflicts.append(
                MemoryConflict(
                    key=key,
                    entry_type=entry_type,
                    entries=items,
                    values=unique_values,
                )
            )
            if strategy == "reject":
                continue
        resolved.append(_select_entry(items, strategy))

    if conflicts and strategy == "reject":
        raise MemoryConflictError("Conflicts detected; resolution strategy is reject.")

    return ResolutionResult(resolved=resolved, conflicts=conflicts, strategy=strategy)


def scan_pii_entries(
    entries: Iterable[MemoryEntry],
    *,
    patterns: Optional[List[str]] = None,
    allowlist_keys: Optional[List[str]] = None,
    allowlist_types: Optional[List[str]] = None,
    max_matches: int = 50,
) -> List[Dict[str, Any]]:
    entry_list = list(entries)
    rule = PIICheckRule(
        patterns=patterns,
        allowlist_keys=allowlist_keys,
        allowlist_types=allowlist_types,
        max_matches=max_matches,
    )
    result = rule.evaluate(entry_list, ValidationContext(tx_id="pii_scan"))
    matches = list(result.details.get("matches", []))
    if not matches:
        return []

    entry_map = {entry.entry_id: entry for entry in entry_list}
    for match in matches:
        entry = entry_map.get(match.get("entry_id"))
        if not entry:
            continue
        match.setdefault("type", entry.type)
        match.setdefault("created_at", entry.created_at)
    return matches


def build_redaction_metadata(
    *,
    reason: str,
    actor: Optional[str] = None,
    rule: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload = {
        "redacted": True,
        "redacted_at": utcnow_iso(),
        "redaction_reason": reason,
    }
    if actor:
        payload["redaction_actor"] = actor
    if rule:
        payload["redaction_rule"] = rule
    if extra:
        payload.update(extra)
    return payload

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, TYPE_CHECKING
import json
import math

from .traces import DecisionTrace

if TYPE_CHECKING:
    from ..adapters.sdk import AdapterContext
    from ..storage.base import StorageBackend


class TraceInjectionError(RuntimeError):
    pass


@dataclass
class TraceQueryConfig:
    tx_id: Optional[str] = None
    decisions: Optional[List[str]] = None
    limit: int = 20


@dataclass
class TraceInjectionConfig:
    section_title: str = "Trace Context"
    placement: str = "append"  # append or prepend
    format: str = "bullets"  # bullets or json
    max_tokens: int = 150
    max_entries: int = 10
    reason_max_chars: int = 140
    include_reason: bool = True
    include_skill_ref: bool = True
    include_confidence: bool = True
    include_tx_id: bool = False
    chars_per_token: int = 4


def _estimate_tokens(text: str, *, chars_per_token: int) -> int:
    if chars_per_token <= 0:
        return len(text)
    return max(1, int(math.ceil(len(text) / chars_per_token)))


def _truncate(text: str, *, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return f"{text[: max(0, max_chars - 3)]}..."


def _normalize_decisions(decisions: Sequence[str]) -> List[str]:
    normalized = []
    for decision in decisions:
        if not isinstance(decision, str):
            continue
        stripped = decision.strip()
        if stripped and stripped not in normalized:
            normalized.append(stripped)
    return normalized


def _query_traces(storage: "StorageBackend", query: TraceQueryConfig) -> List[DecisionTrace]:
    if query.limit <= 0:
        return []

    decisions = _normalize_decisions(query.decisions or [])
    traces: List[DecisionTrace] = []
    if decisions:
        seen: set[str] = set()
        for decision in decisions:
            for trace in storage.list_traces(limit=query.limit, tx_id=query.tx_id, decision=decision):
                if trace.trace_id in seen:
                    continue
                seen.add(trace.trace_id)
                traces.append(trace)
    else:
        traces = list(storage.list_traces(limit=query.limit, tx_id=query.tx_id))

    traces.sort(key=lambda trace: trace.timestamp, reverse=True)
    return traces[: query.limit]


def _build_bullets(entries: Sequence[DecisionTrace], config: TraceInjectionConfig) -> List[str]:
    lines: List[str] = []
    for trace in entries:
        parts = [f"{trace.decision}={trace.result}", f"ts={trace.timestamp}"]
        if config.include_confidence:
            parts.append(f"conf={trace.confidence:.2f}")
        if config.include_skill_ref and trace.skill_ref:
            parts.append(f"skill={trace.skill_ref}")
        if config.include_tx_id and trace.tx_id:
            parts.append(f"tx={trace.tx_id}")
        line = "- " + ", ".join(parts)
        if config.include_reason and trace.reason:
            line += f": {_truncate(trace.reason, max_chars=config.reason_max_chars)}"
        lines.append(line)
    return lines


def _build_json(entries: Sequence[DecisionTrace], config: TraceInjectionConfig) -> List[str]:
    payload = []
    for trace in entries:
        item = {
            "decision": trace.decision,
            "result": trace.result,
            "timestamp": trace.timestamp,
        }
        if config.include_confidence:
            item["confidence"] = trace.confidence
        if config.include_skill_ref:
            item["skill_ref"] = trace.skill_ref
        if config.include_tx_id:
            item["tx_id"] = trace.tx_id
        if config.include_reason and trace.reason:
            item["reason"] = _truncate(trace.reason, max_chars=config.reason_max_chars)
        payload.append(item)
    return [json.dumps(payload, ensure_ascii=True, separators=(",", ":"))]


def _build_section(entries: Sequence[DecisionTrace], config: TraceInjectionConfig) -> str:
    if not entries:
        return ""

    header = f"## {config.section_title}"
    lines = _build_json(entries, config) if config.format == "json" else _build_bullets(entries, config)

    section_lines = [header]
    used_tokens = _estimate_tokens(header, chars_per_token=config.chars_per_token)

    for line in lines:
        if len(section_lines) - 1 >= config.max_entries:
            break
        estimate = _estimate_tokens(line, chars_per_token=config.chars_per_token)
        if used_tokens + estimate > config.max_tokens:
            break
        section_lines.append(line)
        used_tokens += estimate

    if len(section_lines) == 1:
        return ""
    return "\n".join(section_lines)


def inject_traces(
    prompt: str,
    entries: Sequence[DecisionTrace],
    config: TraceInjectionConfig,
) -> str:
    section = _build_section(entries, config)
    if not section:
        return prompt
    if config.placement == "prepend":
        return f"{section}\n\n{prompt}"
    return f"{prompt}\n\n{section}"


class TraceInjectionHook:
    def __init__(
        self,
        *,
        query: Optional[TraceQueryConfig] = None,
        config: Optional[TraceInjectionConfig] = None,
    ) -> None:
        self.query = query or TraceQueryConfig()
        self.config = config or TraceInjectionConfig()

    def before_prompt(self, prompt: str, context: "AdapterContext") -> str:
        storage = context.storage
        if storage is None:
            return prompt
        entries = _query_traces(storage, self.query)
        if not entries:
            return prompt
        return inject_traces(prompt, entries, self.config)

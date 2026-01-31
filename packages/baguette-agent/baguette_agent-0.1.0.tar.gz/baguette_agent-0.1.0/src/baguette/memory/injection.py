from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, List, Optional, Sequence, TYPE_CHECKING
import json
import math

from ..utils import canonical_json
from .governance import resolve_conflicts
from .transactions import MemoryEntry

if TYPE_CHECKING:
    from ..adapters.sdk import AdapterContext
    from ..storage.base import StorageBackend

class MemoryInjectionError(RuntimeError):
    pass


@dataclass
class MemoryQueryConfig:
    keys: Optional[List[str]] = None
    key_prefixes: Optional[List[str]] = None
    types: Optional[List[str]] = None
    created_after: Optional[str] = None
    created_before: Optional[str] = None
    min_confidence: Optional[float] = None
    limit: int = 100


@dataclass
class MemoryInjectionConfig:
    section_title: str = "Memory Context"
    placement: str = "append"  # append or prepend
    format: str = "bullets"  # bullets or json
    max_tokens: int = 500
    max_entries: int = 20
    value_max_chars: int = 200
    include_metadata: bool = True
    chars_per_token: int = 4


def _estimate_tokens(text: str, *, chars_per_token: int) -> int:
    if chars_per_token <= 0:
        return len(text)
    return max(1, int(math.ceil(len(text) / chars_per_token)))


def _format_value(value: Any, *, max_chars: int) -> str:
    try:
        rendered = value if isinstance(value, str) else canonical_json(value)
    except ValueError:
        rendered = str(value)
    if len(rendered) <= max_chars:
        return rendered
    return f"{rendered[: max(0, max_chars - 3)]}..."


def _sort_entries(entries: Sequence[MemoryEntry]) -> List[MemoryEntry]:
    return sorted(entries, key=lambda entry: (entry.created_at, entry.entry_id), reverse=True)


def _query_storage(storage: StorageBackend, query: MemoryQueryConfig) -> List[MemoryEntry]:
    entries: List[MemoryEntry] = []
    entry_type = None
    if query.types and len(query.types) == 1:
        entry_type = query.types[0]

    if query.keys:
        for key in query.keys:
            entries.extend(
                storage.list_memory(
                    key=key,
                    entry_type=entry_type,
                    created_after=query.created_after,
                    created_before=query.created_before,
                    limit=query.limit,
                )
            )
    else:
        entries = list(
            storage.list_memory(
                key=None,
                entry_type=entry_type,
                created_after=query.created_after,
                created_before=query.created_before,
                limit=query.limit,
            )
        )

    if query.key_prefixes:
        entries = [
            entry
            for entry in entries
            if any(entry.key.startswith(prefix) for prefix in query.key_prefixes)
        ]
    if query.types and entry_type is None:
        entries = [entry for entry in entries if entry.type in query.types]
    if query.min_confidence is not None:
        entries = [entry for entry in entries if entry.confidence >= query.min_confidence]

    seen: set[str] = set()
    deduped: List[MemoryEntry] = []
    for entry in entries:
        if entry.entry_id in seen:
            continue
        seen.add(entry.entry_id)
        deduped.append(entry)

    return _sort_entries(deduped)[: query.limit]


def _build_bullets(entries: Sequence[MemoryEntry], config: MemoryInjectionConfig) -> List[str]:
    lines: List[str] = []
    for entry in entries:
        value = _format_value(entry.value, max_chars=config.value_max_chars)
        if config.include_metadata:
            line = (
                f"- {entry.key}: {value} "
                f"(type={entry.type}, conf={entry.confidence:.2f}, ts={entry.created_at})"
            )
        else:
            line = f"- {entry.key}: {value}"
        lines.append(line)
    return lines


def _build_json(entries: Sequence[MemoryEntry], config: MemoryInjectionConfig) -> List[str]:
    payload = []
    for entry in entries:
        value = _format_value(entry.value, max_chars=config.value_max_chars)
        payload.append(
            {
                "key": entry.key,
                "value": value,
                "type": entry.type,
                "confidence": entry.confidence,
                "created_at": entry.created_at,
            }
        )
    return [json.dumps(payload, ensure_ascii=True, separators=(",", ":"))]


def _build_section(entries: Sequence[MemoryEntry], config: MemoryInjectionConfig) -> str:
    if not entries:
        return ""

    header = f"## {config.section_title}"
    if config.format == "json":
        lines = _build_json(entries, config)
    else:
        lines = _build_bullets(entries, config)

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


def inject_memory(
    prompt: str,
    entries: Sequence[MemoryEntry],
    config: MemoryInjectionConfig,
) -> str:
    section = _build_section(entries, config)
    if not section:
        return prompt
    if config.placement == "prepend":
        return f"{section}\n\n{prompt}"
    return f"{prompt}\n\n{section}"


class MemoryInjectionHook:
    def __init__(
        self,
        *,
        query: Optional[MemoryQueryConfig] = None,
        config: Optional[MemoryInjectionConfig] = None,
        conflict_strategy: str = "latest",
    ) -> None:
        self.query = query or MemoryQueryConfig()
        self.config = config or MemoryInjectionConfig()
        self.conflict_strategy = conflict_strategy

    def before_prompt(self, prompt: str, context: "AdapterContext") -> str:
        storage = context.storage
        if storage is None:
            return prompt
        entries = _query_storage(storage, self.query)
        if not entries:
            return prompt
        resolution = resolve_conflicts(entries, strategy=self.conflict_strategy)
        resolved = _sort_entries(resolution.resolved)
        return inject_memory(prompt, resolved, self.config)

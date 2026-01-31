from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union
import copy
import json
import re

import yaml

from ..utils import canonical_json, sha256_text
from .transactions import MemoryEntry


class RedactionPolicyError(ValueError):
    pass


PathToken = Union[str, int]


_DEFAULT_PATTERNS: Dict[str, re.Pattern[str]] = {
    "email": re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE),
    "phone": re.compile(r"\+?\d[\d\s().-]{7,}\d"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
}


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


def _parse_path(path: str) -> List[PathToken]:
    if path in {"", "."}:
        return []
    tokens: List[PathToken] = []
    pattern = re.compile(r"(?:^|\.)([A-Za-z0-9_-]+)|\[(\d+)\]")
    for match in pattern.finditer(path):
        name, index = match.groups()
        if name:
            tokens.append(name)
        elif index is not None:
            tokens.append(int(index))
    if not tokens:
        raise RedactionPolicyError(f"Invalid path expression: {path!r}")
    return tokens


def _format_path(tokens: Sequence[PathToken]) -> str:
    parts: List[str] = []
    for token in tokens:
        if isinstance(token, int):
            parts.append(f"[{token}]")
        else:
            if parts:
                parts.append(".")
            parts.append(token)
    return "".join(parts)


def _get_path(value: Any, tokens: Sequence[PathToken]) -> tuple[bool, Any]:
    current = value
    for token in tokens:
        if isinstance(token, int):
            if not isinstance(current, list) or token >= len(current):
                return False, None
            current = current[token]
        else:
            if not isinstance(current, dict) or token not in current:
                return False, None
            current = current[token]
    return True, current


def _set_path(value: Any, tokens: Sequence[PathToken], new_value: Any, *, drop: bool) -> Any:
    if not tokens:
        return None if drop else new_value
    current = value
    for token in tokens[:-1]:
        if isinstance(token, int):
            if not isinstance(current, list) or token >= len(current):
                return value
            current = current[token]
        else:
            if not isinstance(current, dict) or token not in current:
                return value
            current = current[token]
    final = tokens[-1]
    if isinstance(final, int):
        if not isinstance(current, list) or final >= len(current):
            return value
        current[final] = None if drop else new_value
        return value
    if not isinstance(current, dict):
        return value
    if drop:
        current.pop(final, None)
    else:
        current[final] = new_value
    return value


def _iter_scalar_paths(value: Any, prefix: Optional[List[PathToken]] = None) -> Iterable[Tuple[List[PathToken], Any]]:
    prefix = list(prefix or [])
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _iter_scalar_paths(item, prefix + [key])
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            yield from _iter_scalar_paths(item, prefix + [idx])
    else:
        yield prefix, value


def _mask_value(
    value: str,
    *,
    keep_first: int = 0,
    keep_last: int = 4,
    mask_char: str = "*",
) -> str:
    length = len(value)
    if length == 0:
        return value
    keep_first = max(0, min(keep_first, length))
    keep_last = max(0, min(keep_last, length - keep_first))
    masked_len = max(0, length - keep_first - keep_last)
    return f"{value[:keep_first]}{mask_char * masked_len}{value[-keep_last:] if keep_last else ''}"


def _truncate_value(value: str, *, length: int = 4, suffix: str = "...") -> str:
    if len(value) <= length:
        return value
    return value[:length] + suffix


@dataclass
class RedactionRule:
    name: str
    key: Optional[str] = None
    entry_type: Optional[str] = None
    paths: List[str] = field(default_factory=list)
    patterns: Optional[List[str]] = None
    action: str = "replace"
    config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise RedactionPolicyError("Redaction rule name must be a non-empty string.")
        if self.key is not None and (not isinstance(self.key, str) or not self.key.strip()):
            raise RedactionPolicyError("Redaction rule key must be a non-empty string.")
        if self.entry_type is not None and (
            not isinstance(self.entry_type, str) or not self.entry_type.strip()
        ):
            raise RedactionPolicyError("Redaction rule entry_type must be a non-empty string.")
        if not isinstance(self.paths, list):
            raise RedactionPolicyError("Redaction rule paths must be a list.")
        if self.patterns is not None and not isinstance(self.patterns, list):
            raise RedactionPolicyError("Redaction rule patterns must be a list.")
        if not isinstance(self.action, str) or not self.action.strip():
            raise RedactionPolicyError("Redaction rule action must be a non-empty string.")
        if not isinstance(self.config, dict):
            raise RedactionPolicyError("Redaction rule config must be a dictionary.")


@dataclass
class RedactionPolicy:
    version: str = "1.0"
    rules: List[RedactionRule] = field(default_factory=list)
    default_action: str = "replace"
    default_replacement: str = "[REDACTED]"

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "RedactionPolicy":
        if not isinstance(payload, dict):
            raise RedactionPolicyError("Redaction policy payload must be a dictionary.")
        version = payload.get("version", "1.0")
        defaults = payload.get("defaults", {})
        default_action = defaults.get("action", "replace")
        default_replacement = defaults.get("replacement", "[REDACTED]")
        raw_rules = payload.get("rules", [])
        if not isinstance(raw_rules, list):
            raise RedactionPolicyError("Redaction policy rules must be a list.")
        rules = []
        for raw in raw_rules:
            if not isinstance(raw, dict):
                raise RedactionPolicyError("Each redaction rule must be a dictionary.")
            rules.append(
                RedactionRule(
                    name=raw.get("name", ""),
                    key=raw.get("key"),
                    entry_type=raw.get("entry_type"),
                    paths=raw.get("paths") or [],
                    patterns=raw.get("patterns"),
                    action=raw.get("action", "replace"),
                    config=raw.get("config", {}) or {},
                )
            )
        return cls(
            version=version,
            rules=rules,
            default_action=default_action,
            default_replacement=default_replacement,
        )

    @classmethod
    def from_file(cls, path: str | Path) -> "RedactionPolicy":
        source = Path(path)
        if not source.exists():
            raise RedactionPolicyError(f"Redaction policy file not found: {source}")
        raw = source.read_text(encoding="utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = yaml.safe_load(raw)
        if not isinstance(data, dict):
            raise RedactionPolicyError("Redaction policy file must parse to a dictionary.")
        return cls.from_dict(data)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "defaults": {
                "action": self.default_action,
                "replacement": self.default_replacement,
            },
            "rules": [
                {
                    "name": rule.name,
                    "key": rule.key,
                    "entry_type": rule.entry_type,
                    "paths": rule.paths,
                    "patterns": rule.patterns,
                    "action": rule.action,
                    "config": rule.config,
                }
                for rule in self.rules
            ],
        }


@dataclass
class RedactionMatch:
    entry_id: str
    key: str
    path: str
    pattern: Optional[str]
    rule: str
    value_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "key": self.key,
            "path": self.path,
            "pattern": self.pattern,
            "rule": self.rule,
            "value_hash": self.value_hash,
        }


@dataclass
class RedactionChange:
    entry_id: str
    key: str
    entry_type: str
    redacted_value: Any
    rules: List[str]
    matches: List[RedactionMatch]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "key": self.key,
            "entry_type": self.entry_type,
            "redacted_value": self.redacted_value,
            "rules": self.rules,
            "matches": [match.to_dict() for match in self.matches],
        }


@dataclass
class RedactionReport:
    changes: List[RedactionChange]

    def to_dict(self) -> Dict[str, Any]:
        return {"changes": [change.to_dict() for change in self.changes]}


def _compile_patterns(patterns: Optional[List[str]]) -> List[tuple[str, re.Pattern[str]]]:
    if not patterns:
        return []
    compiled = []
    for name in patterns:
        if name in _DEFAULT_PATTERNS:
            compiled.append((name, _DEFAULT_PATTERNS[name]))
        else:
            compiled.append((name, re.compile(name)))
    return compiled


def _apply_action(
    value: Any,
    *,
    action: str,
    config: Dict[str, Any],
    default_replacement: str,
    tokenize_fn: Optional[callable],
) -> Any:
    if action in {"replace", "redact"}:
        return config.get("replacement", default_replacement)
    string_value = str(value)
    if action == "mask":
        return _mask_value(
            string_value,
            keep_first=int(config.get("keep_first", 0)),
            keep_last=int(config.get("keep_last", 4)),
            mask_char=str(config.get("mask_char", "*")),
        )
    if action == "keep_last":
        keep_last = int(config.get("keep_last", 4))
        return _mask_value(string_value, keep_first=0, keep_last=keep_last, mask_char="*")
    if action == "keep_first":
        keep_first = int(config.get("keep_first", 4))
        return _mask_value(string_value, keep_first=keep_first, keep_last=0, mask_char="*")
    if action == "truncate":
        length = int(config.get("length", 4))
        suffix = str(config.get("suffix", "..."))
        return _truncate_value(string_value, length=length, suffix=suffix)
    if action == "hash":
        return sha256_text(string_value)
    if action == "tokenize":
        if not tokenize_fn:
            raise RedactionPolicyError("Tokenize action requires a tokenize_fn.")
        return tokenize_fn(string_value, config)
    if action == "drop":
        return None
    raise RedactionPolicyError(f"Unknown redaction action: {action}")


def apply_redaction(
    entries: Iterable[MemoryEntry],
    *,
    policy: RedactionPolicy,
    tokenize_fn: Optional[callable] = None,
) -> RedactionReport:
    changes: List[RedactionChange] = []

    for entry in entries:
        value = copy.deepcopy(entry.value)
        rules_applied: List[str] = []
        matches: List[RedactionMatch] = []
        changed = False

        for rule in policy.rules:
            if rule.key and rule.key != entry.key:
                continue
            if rule.entry_type and rule.entry_type != entry.type:
                continue

            action = rule.action or policy.default_action
            action_config = rule.config or {}
            paths = rule.paths or []
            compiled_patterns = _compile_patterns(rule.patterns)

            candidate_paths: List[Tuple[List[PathToken], Any]] = []
            if paths:
                for raw_path in paths:
                    tokens = _parse_path(raw_path)
                    exists, current = _get_path(value, tokens)
                    if exists:
                        candidate_paths.append((tokens, current))
            else:
                candidate_paths = list(_iter_scalar_paths(value))

            for tokens, current in candidate_paths:
                if current is None:
                    continue
                current_str = str(current)
                matched_patterns: List[str] = []

                if compiled_patterns:
                    for name, pattern in compiled_patterns:
                        if not pattern.search(current_str):
                            continue
                        if name == "credit_card" and not _luhn_check(current_str):
                            continue
                        matched_patterns.append(name)
                else:
                    matched_patterns.append(None)  # type: ignore[list-item]

                if not matched_patterns:
                    continue

                redacted_value = _apply_action(
                    current,
                    action=action,
                    config=action_config,
                    default_replacement=policy.default_replacement,
                    tokenize_fn=tokenize_fn,
                )

                drop_field = action == "drop"
                value = _set_path(value, tokens, redacted_value, drop=drop_field)
                changed = True
                rules_applied.append(rule.name)
                for pattern_name in matched_patterns:
                    matches.append(
                        RedactionMatch(
                            entry_id=entry.entry_id,
                            key=entry.key,
                            path=_format_path(tokens),
                            pattern=pattern_name,
                            rule=rule.name,
                            value_hash=sha256_text(current_str),
                        )
                    )

        if changed:
            if canonical_json(value) == canonical_json(entry.value):
                continue
            changes.append(
                RedactionChange(
                    entry_id=entry.entry_id,
                    key=entry.key,
                    entry_type=entry.type,
                    redacted_value=value,
                    rules=sorted(set(rules_applied)),
                    matches=matches,
                )
            )

    return RedactionReport(changes=changes)

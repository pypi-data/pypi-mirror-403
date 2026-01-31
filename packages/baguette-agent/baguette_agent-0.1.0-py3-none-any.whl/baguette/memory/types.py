from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional, Sequence
import os
import warnings

from ..config import load_config


DEFAULT_MEMORY_TYPES = {
    "episodic",
    "semantic",
    "preference",
    "procedural",
    "decision_trace",
}


_MODE_VALUES = {"off", "warn", "strict"}


def _normalize_mode(mode: str) -> str:
    if not isinstance(mode, str):
        raise ValueError("Memory type mode must be a string.")
    normalized = mode.strip().lower()
    if normalized not in _MODE_VALUES:
        raise ValueError(f"Invalid memory type mode: {mode}")
    return normalized


def _normalize_prefixes(prefixes: Optional[Sequence[str]]) -> tuple[str, ...]:
    if not prefixes:
        return ()
    normalized = []
    for prefix in prefixes:
        if not isinstance(prefix, str) or not prefix.strip():
            raise ValueError("Custom prefix must be a non-empty string.")
        normalized.append(prefix)
    return tuple(normalized)


@dataclass
class MemoryTypeRegistry:
    types: set[str] = field(default_factory=lambda: set(DEFAULT_MEMORY_TYPES))
    mode: str = "off"
    custom_prefixes: tuple[str, ...] = ("custom.",)

    def __post_init__(self) -> None:
        self.mode = _normalize_mode(self.mode)
        self.custom_prefixes = _normalize_prefixes(self.custom_prefixes)
        if not isinstance(self.types, set):
            self.types = set(self.types)

    def is_allowed(self, entry_type: str) -> bool:
        if entry_type in self.types:
            return True
        if self.custom_prefixes and any(entry_type.startswith(prefix) for prefix in self.custom_prefixes):
            return True
        return False

    def validate(self, entry_type: str) -> None:
        if self.mode == "off":
            return
        if self.is_allowed(entry_type):
            return
        message = (
            f"Unknown memory type '{entry_type}'. "
            f"Allowed: {sorted(self.types)} or custom prefixes {self.custom_prefixes}."
        )
        if self.mode == "warn":
            warnings.warn(message, RuntimeWarning, stacklevel=3)
        else:
            raise ValueError(message)

    def register(self, *entry_types: str) -> None:
        for entry_type in entry_types:
            if not isinstance(entry_type, str) or not entry_type.strip():
                raise ValueError("Memory type must be a non-empty string.")
            self.types.add(entry_type)

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "types": sorted(self.types),
            "custom_prefixes": list(self.custom_prefixes),
        }


def _default_mode_from_env() -> str:
    value = os.getenv("BAGUETTE_MEMORY_TYPE_MODE", "").strip()
    if not value:
        return "off"
    return _normalize_mode(value)


def _build_registry_from_config() -> MemoryTypeRegistry:
    config = load_config()
    payload = config.get("memory_types")
    if not isinstance(payload, dict):
        payload = config
    mode = payload.get("mode")
    types = payload.get("types")
    prefixes = payload.get("custom_prefixes")
    registry = MemoryTypeRegistry(
        types=set(types) if isinstance(types, list) else set(DEFAULT_MEMORY_TYPES),
        mode=mode or "off",
        custom_prefixes=prefixes if isinstance(prefixes, list) else ("custom.",),
    )
    env_mode = os.getenv("BAGUETTE_MEMORY_TYPE_MODE", "").strip()
    if env_mode:
        registry.mode = _normalize_mode(env_mode)
    return registry


_REGISTRY = _build_registry_from_config()


def get_memory_type_registry() -> MemoryTypeRegistry:
    return _REGISTRY


def configure_memory_type_registry(
    *,
    mode: Optional[str] = None,
    types: Optional[Iterable[str]] = None,
    custom_prefixes: Optional[Sequence[str]] = None,
) -> MemoryTypeRegistry:
    global _REGISTRY
    current = _REGISTRY
    registry = MemoryTypeRegistry(
        types=set(types) if types is not None else set(current.types),
        mode=mode or current.mode,
        custom_prefixes=custom_prefixes if custom_prefixes is not None else current.custom_prefixes,
    )
    _REGISTRY = registry
    return registry


def register_memory_types(*entry_types: str) -> MemoryTypeRegistry:
    registry = get_memory_type_registry()
    registry.register(*entry_types)
    return registry

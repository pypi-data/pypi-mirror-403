"""Audit primitives for traces and journal events."""

from .journal import JournalEvent
from .traces import DecisionTrace
from .injection import (
    TraceInjectionConfig,
    TraceInjectionError,
    TraceInjectionHook,
    TraceQueryConfig,
    inject_traces,
)

__all__ = [
    "DecisionTrace",
    "JournalEvent",
    "TraceInjectionConfig",
    "TraceInjectionError",
    "TraceInjectionHook",
    "TraceQueryConfig",
    "inject_traces",
]

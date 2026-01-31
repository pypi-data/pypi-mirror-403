"""Deprecated shim for the LangGraph adapter (use baguette.adapters.langgraph)."""

from __future__ import annotations

import warnings

warnings.warn(
    "baguette.experimental.adapters.langgraph is deprecated; "
    "use baguette.adapters.langgraph instead.",
    DeprecationWarning,
    stacklevel=2,
)

from ...adapters.langgraph import (  # noqa: E402
    LANGGRAPH_CONTEXT_KEY,
    LANGGRAPH_CONTEXT_TOKEN_KEY,
    LANGGRAPH_CORRELATION_ID_KEY,
    LANGGRAPH_EDGE_PATH_KEY,
    LANGGRAPH_ERROR_TRACE_DECISION,
    LANGGRAPH_GRAPH_TRACE_DECISION,
    LANGGRAPH_METRIC_MEMORY_STAGED,
    LANGGRAPH_METRIC_TX_COMMITTED,
    LANGGRAPH_METRIC_TX_ROLLED_BACK,
    LANGGRAPH_NODE_TRACE_DECISION,
    LangGraphAdapter,
    LangGraphAdapterError,
    LangGraphContext,
    MetricsHook,
    merge_context,
    merge_context_token,
)

__all__ = [
    "LangGraphAdapter",
    "LangGraphAdapterError",
    "LangGraphContext",
    "LANGGRAPH_CONTEXT_KEY",
    "LANGGRAPH_CONTEXT_TOKEN_KEY",
    "LANGGRAPH_CORRELATION_ID_KEY",
    "LANGGRAPH_EDGE_PATH_KEY",
    "LANGGRAPH_ERROR_TRACE_DECISION",
    "LANGGRAPH_GRAPH_TRACE_DECISION",
    "LANGGRAPH_METRIC_MEMORY_STAGED",
    "LANGGRAPH_METRIC_TX_COMMITTED",
    "LANGGRAPH_METRIC_TX_ROLLED_BACK",
    "LANGGRAPH_NODE_TRACE_DECISION",
    "MetricsHook",
    "merge_context",
    "merge_context_token",
]

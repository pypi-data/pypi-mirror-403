from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
import os
import time

from ..config import get_config_section
from ..utils import canonical_json, sha256_text
from .runtime import RunResult


@dataclass
class SkillTraceConfig:
    include_inputs_hash: bool = True
    include_inputs_preview: bool = False
    include_output_preview: bool = False
    preview_max_chars: int = 200
    include_duration: bool = True
    include_attempts: bool = True


def _truncate(text: str, *, max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    return f"{text[: max(0, max_chars - 3)]}..."


def _safe_json(value: Any) -> Optional[str]:
    try:
        return canonical_json(value)
    except ValueError:
        return None


def build_skill_trace_metadata(
    *,
    tool_name: Optional[str],
    skill_ref: Optional[str],
    inputs: Any,
    run_result: RunResult,
    duration_ms: Optional[int] = None,
    attempt: int = 1,
    max_attempts: int = 1,
    idempotency_key: Optional[str] = None,
    config: Optional[SkillTraceConfig] = None,
) -> Dict[str, Any]:
    config = config or SkillTraceConfig()
    metadata: Dict[str, Any] = dict(run_result.metadata)

    if tool_name:
        metadata.setdefault("tool_name", tool_name)
    if skill_ref:
        metadata.setdefault("skill_ref", skill_ref)
    metadata.setdefault("status", run_result.status)

    if config.include_inputs_hash:
        rendered = _safe_json(inputs)
        if rendered is not None:
            metadata.setdefault("inputs_hash", sha256_text(rendered))
    if config.include_inputs_preview:
        rendered = _safe_json(inputs)
        if rendered is not None:
            metadata.setdefault("inputs_preview", _truncate(rendered, max_chars=config.preview_max_chars))
    if config.include_output_preview and run_result.output is not None:
        metadata.setdefault(
            "output_preview",
            _truncate(str(run_result.output), max_chars=config.preview_max_chars),
        )
    if config.include_duration and duration_ms is not None:
        metadata.setdefault("duration_ms", duration_ms)
    if config.include_attempts:
        metadata.setdefault("attempt", attempt)
        metadata.setdefault("max_attempts", max_attempts)
    if idempotency_key:
        metadata.setdefault("idempotency_key", idempotency_key)
    if run_result.error:
        metadata.setdefault("error", run_result.error)

    return metadata


def measure_duration_ms(start: float, end: Optional[float] = None) -> int:
    finish = end if end is not None else time.monotonic()
    return int(max(0.0, (finish - start) * 1000))


def _parse_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return None


def load_skill_trace_config() -> SkillTraceConfig:
    config = SkillTraceConfig()
    tools_cfg = get_config_section("tools")
    trace_cfg = tools_cfg.get("trace") if isinstance(tools_cfg, dict) else {}
    if isinstance(trace_cfg, dict):
        inputs_preview = _parse_bool(trace_cfg.get("inputs_preview"))
        output_preview = _parse_bool(trace_cfg.get("output_preview"))
        preview_max = trace_cfg.get("preview_max_chars")
        if inputs_preview is not None:
            config.include_inputs_preview = inputs_preview
        if output_preview is not None:
            config.include_output_preview = output_preview
        if isinstance(preview_max, int):
            config.preview_max_chars = max(0, preview_max)

    env_inputs = _parse_bool(os.getenv("BAGUETTE_TOOLS_TRACE_INPUTS_PREVIEW"))
    env_output = _parse_bool(os.getenv("BAGUETTE_TOOLS_TRACE_OUTPUT_PREVIEW"))
    env_preview = os.getenv("BAGUETTE_TOOLS_TRACE_PREVIEW_MAX_CHARS")
    if env_inputs is not None:
        config.include_inputs_preview = env_inputs
    if env_output is not None:
        config.include_output_preview = env_output
    if env_preview:
        try:
            config.preview_max_chars = max(0, int(env_preview))
        except ValueError:
            pass

    return config

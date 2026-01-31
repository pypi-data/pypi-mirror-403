"""Skill artifact models and loaders."""

from .artifacts import (
    Artifact,
    SkillArtifact,
    SkillValidationError,
    load_skill_file,
    load_skill_spec,
    validate_skill_inputs,
)
from .injection import (
    SkillInjectionConfig,
    SkillInjectionError,
    SkillInjectionHook,
    SkillQueryConfig,
    inject_skills,
)
from .resolver import SkillResolutionConfig, SkillResolutionError, resolve_skills
from .runtime import RunResult, SkillRunConfig, SkillRunResult, run_skill, run_prompt, run_workflow
from .tool_adapters import (
    to_anthropic_tools,
    to_gemini_function_declarations,
    to_gemini_tools,
    to_openai_tools,
    to_provider_tools,
)
from importlib import import_module
from .trace import (
    SkillTraceConfig,
    build_skill_trace_metadata,
    load_skill_trace_config,
    measure_duration_ms,
)
from .templating import render_template

__all__ = [
    "Artifact",
    "SkillArtifact",
    "SkillValidationError",
    "SkillInjectionConfig",
    "SkillInjectionError",
    "SkillInjectionHook",
    "SkillQueryConfig",
    "SkillResolutionConfig",
    "SkillResolutionError",
    "SkillRunConfig",
    "SkillRunResult",
    "RunResult",
    "load_skill_file",
    "load_skill_spec",
    "validate_skill_inputs",
    "inject_skills",
    "resolve_skills",
    "run_prompt",
    "run_skill",
    "run_workflow",
    "SkillToolConfig",
    "SkillToolRegistry",
    "SkillToolResult",
    "SkillToolSpec",
    "to_anthropic_tools",
    "to_gemini_function_declarations",
    "to_gemini_tools",
    "to_openai_tools",
    "to_provider_tools",
    "ToolCall",
    "auto_execute_with_model",
    "execute_tool_calls",
    "extract_anthropic_tool_calls",
    "extract_gemini_tool_calls",
    "extract_openai_tool_calls",
    "extract_tool_calls",
    "SkillTraceConfig",
    "build_skill_trace_metadata",
    "load_skill_trace_config",
    "measure_duration_ms",
    "render_template",
]

_LAZY_IMPORTS = {
    "SkillToolConfig": (".tools", "SkillToolConfig"),
    "SkillToolRegistry": (".tools", "SkillToolRegistry"),
    "SkillToolResult": (".tools", "SkillToolResult"),
    "SkillToolSpec": (".tools", "SkillToolSpec"),
    "build_tool_spec": (".tools", "build_tool_spec"),
    "execute_tool_call": (".tools", "execute_tool_call"),
    "ToolCall": (".auto", "ToolCall"),
    "auto_execute_with_model": (".auto", "auto_execute_with_model"),
    "execute_tool_calls": (".auto", "execute_tool_calls"),
    "extract_anthropic_tool_calls": (".auto", "extract_anthropic_tool_calls"),
    "extract_gemini_tool_calls": (".auto", "extract_gemini_tool_calls"),
    "extract_openai_tool_calls": (".auto", "extract_openai_tool_calls"),
    "extract_tool_calls": (".auto", "extract_tool_calls"),
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        module_name, attr = _LAZY_IMPORTS[name]
        module = import_module(module_name, __name__)
        value = getattr(module, attr)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, List, Mapping, Optional, Sequence

from ..errors import ExecutionError
from .tool_adapters import to_provider_tools
from .tools import SkillToolRegistry, SkillToolResult, execute_tool_call
from .runtime import SkillRunConfig
from .trace import SkillTraceConfig


@dataclass
class ToolCall:
    name: str
    arguments: Any
    provider: Optional[str] = None


ModelCall = Callable[[str, Sequence[Mapping[str, Any]]], Any]


def extract_tool_calls(response: Mapping[str, Any], provider: str) -> List[ToolCall]:
    normalized = provider.strip().lower()
    if normalized in {"openai", "oai"}:
        return extract_openai_tool_calls(response)
    if normalized in {"anthropic", "claude"}:
        return extract_anthropic_tool_calls(response)
    if normalized in {"gemini", "google"}:
        return extract_gemini_tool_calls(response)
    raise ValueError(f"Unknown provider: {provider}")


def extract_openai_tool_calls(response: Mapping[str, Any]) -> List[ToolCall]:
    calls: List[ToolCall] = []

    output = response.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "function_call":
                continue
            name = item.get("name")
            arguments = item.get("arguments")
            if name:
                calls.append(ToolCall(name=str(name), arguments=arguments, provider="openai"))

    choices = response.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
        tool_calls = message.get("tool_calls") if isinstance(message, dict) else None
        if isinstance(tool_calls, list):
            for call in tool_calls:
                if not isinstance(call, dict):
                    continue
                function = call.get("function") or {}
                name = function.get("name")
                arguments = function.get("arguments")
                if name:
                    calls.append(ToolCall(name=str(name), arguments=arguments, provider="openai"))

    return calls


def extract_anthropic_tool_calls(response: Mapping[str, Any]) -> List[ToolCall]:
    calls: List[ToolCall] = []
    content = response.get("content")
    if not isinstance(content, list):
        return calls
    for item in content:
        if not isinstance(item, dict):
            continue
        if item.get("type") != "tool_use":
            continue
        name = item.get("name")
        arguments = item.get("input")
        if name:
            calls.append(ToolCall(name=str(name), arguments=arguments, provider="anthropic"))
    return calls


def extract_gemini_tool_calls(response: Mapping[str, Any]) -> List[ToolCall]:
    calls: List[ToolCall] = []
    candidates = response.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        return calls
    content = candidates[0].get("content", {}) if isinstance(candidates[0], dict) else {}
    parts = content.get("parts") if isinstance(content, dict) else None
    if not isinstance(parts, list):
        return calls
    for part in parts:
        if not isinstance(part, dict):
            continue
        function_call = part.get("function_call") or part.get("functionCall")
        if not isinstance(function_call, dict):
            continue
        name = function_call.get("name")
        arguments = function_call.get("args") or function_call.get("arguments")
        if name:
            calls.append(ToolCall(name=str(name), arguments=arguments, provider="gemini"))
    return calls


def execute_tool_calls(
    registry: SkillToolRegistry,
    storage,
    tool_calls: Iterable[ToolCall | Mapping[str, Any]],
    *,
    trace_config: Optional[SkillTraceConfig] = None,
    run_config: Optional[SkillRunConfig] = None,
    dry_run: bool = False,
) -> List[SkillToolResult]:
    results: List[SkillToolResult] = []
    for call in tool_calls:
        if isinstance(call, dict):
            name = call.get("name")
            arguments = call.get("arguments")
        else:
            name = call.name
            arguments = call.arguments
        if not name:
            raise ExecutionError("Tool call missing name.")
        results.append(
            execute_tool_call(
                storage,
                str(name),
                arguments,
                registry=registry,
                trace_config=trace_config,
                run_config=run_config,
                dry_run=dry_run,
            )
        )
    return results


def auto_execute_with_model(
    storage,
    registry: SkillToolRegistry,
    *,
    request: str,
    provider: str,
    model_call: ModelCall,
    trace_config: Optional[SkillTraceConfig] = None,
    run_config: Optional[SkillRunConfig] = None,
    dry_run: bool = False,
) -> List[SkillToolResult]:
    tools = to_provider_tools(provider, registry.definitions())
    response = model_call(request, tools)
    if not isinstance(response, dict):
        raise ExecutionError("model_call must return a dict-like response.")
    calls = extract_tool_calls(response, provider)
    return execute_tool_calls(
        registry,
        storage,
        calls,
        trace_config=trace_config,
        run_config=run_config,
        dry_run=dry_run,
    )

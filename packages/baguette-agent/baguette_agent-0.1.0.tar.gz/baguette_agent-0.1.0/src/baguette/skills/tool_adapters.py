from __future__ import annotations

from typing import Any, Iterable, List, Mapping, Sequence


def _coerce_definitions(definitions: Any) -> List[Mapping[str, Any]]:
    if hasattr(definitions, "definitions"):
        return list(definitions.definitions())
    if isinstance(definitions, dict):
        return [definitions]
    return list(definitions)


def _ensure_parameters(definition: Mapping[str, Any]) -> Mapping[str, Any]:
    parameters = definition.get("parameters")
    if parameters is None:
        return {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": True,
        }
    return parameters


def to_openai_tools(
    definitions: Iterable[Mapping[str, Any]] | Any,
    *,
    strict: bool | None = None,
    style: str = "responses",  # responses or chat_completions
) -> List[Mapping[str, Any]]:
    tools = []
    normalized_style = style.strip().lower()
    if normalized_style not in {"responses", "chat_completions"}:
        raise ValueError("style must be 'responses' or 'chat_completions'.")
    for definition in _coerce_definitions(definitions):
        function = {
            "name": definition.get("name"),
            "description": definition.get("description", ""),
            "parameters": _ensure_parameters(definition),
        }
        if strict is not None:
            function["strict"] = bool(strict)
        if normalized_style == "chat_completions":
            tools.append({"type": "function", "function": function})
        else:
            tools.append({"type": "function", **function})
    return tools


def to_anthropic_tools(
    definitions: Iterable[Mapping[str, Any]] | Any,
) -> List[Mapping[str, Any]]:
    tools = []
    for definition in _coerce_definitions(definitions):
        tools.append(
            {
                "name": definition.get("name"),
                "description": definition.get("description", ""),
                "input_schema": _ensure_parameters(definition),
            }
        )
    return tools


def to_gemini_function_declarations(
    definitions: Iterable[Mapping[str, Any]] | Any,
) -> List[Mapping[str, Any]]:
    declarations = []
    for definition in _coerce_definitions(definitions):
        declarations.append(
            {
                "name": definition.get("name"),
                "description": definition.get("description", ""),
                "parameters": _ensure_parameters(definition),
            }
        )
    return declarations


def to_gemini_tools(
    definitions: Iterable[Mapping[str, Any]] | Any,
) -> List[Mapping[str, Any]]:
    return [{"function_declarations": to_gemini_function_declarations(definitions)}]


def to_provider_tools(
    provider: str,
    definitions: Iterable[Mapping[str, Any]] | Any,
    *,
    strict: bool | None = None,
) -> Sequence[Mapping[str, Any]]:
    normalized = provider.strip().lower()
    if normalized in {"openai", "oai"}:
        return to_openai_tools(definitions, strict=strict)
    if normalized in {"anthropic", "claude"}:
        return to_anthropic_tools(definitions)
    if normalized in {"gemini", "google"}:
        return to_gemini_tools(definitions)
    raise ValueError(f"Unknown provider: {provider}")

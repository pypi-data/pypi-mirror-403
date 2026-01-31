from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence
import copy
import json
import math

from .artifacts import SkillArtifact


class SkillResolutionError(ValueError):
    pass


_ALLOWED_FORMATS = {"bullets", "json"}
_ALLOWED_IO_SCHEMA_MODES = {"names", "schema"}
_MODE_ALIASES = {
    "adaptive": "adaptive",
    "ref": "ref",
    "ref-only": "ref",
    "reference": "ref",
    "summary": "summary",
    "full": "full",
}


@dataclass
class SkillResolutionConfig:
    section_title: str = "Skill Context"
    placement: str = "append"  # append or prepend
    format: str = "bullets"  # bullets or json
    mode: str = "summary"  # ref, summary, full
    max_tokens: int = 300
    max_entries: int = 10
    description_max_chars: int = 160
    content_max_chars: int = 2000
    include_inputs: bool = False
    include_outputs: bool = False
    include_steps: bool = False
    max_steps: int = 5
    step_max_chars: int = 120
    io_schema_mode: str = "names"  # names or schema
    adaptive_order: List[str] = field(default_factory=lambda: ["full", "summary", "ref"])
    include_description: bool = True
    include_tags: bool = True
    include_type: bool = False
    chars_per_token: int = 4

    def __post_init__(self) -> None:
        if not isinstance(self.format, str):
            raise SkillResolutionError("Skill resolution format must be a string.")
        format_normalized = self.format.strip().lower()
        if format_normalized not in _ALLOWED_FORMATS:
            raise SkillResolutionError(
                f"Skill resolution format must be one of {sorted(_ALLOWED_FORMATS)}."
            )
        self.format = format_normalized

        if not isinstance(self.mode, str):
            raise SkillResolutionError("Skill resolution mode must be a string.")
        mode_normalized = _MODE_ALIASES.get(self.mode.strip().lower())
        if not mode_normalized:
            raise SkillResolutionError(
                "Skill resolution mode must be one of ['ref', 'summary', 'full', 'adaptive']."
            )
        self.mode = mode_normalized
        if not isinstance(self.io_schema_mode, str):
            raise SkillResolutionError("io_schema_mode must be a string.")
        schema_mode = self.io_schema_mode.strip().lower()
        if schema_mode not in _ALLOWED_IO_SCHEMA_MODES:
            raise SkillResolutionError(
                f"io_schema_mode must be one of {sorted(_ALLOWED_IO_SCHEMA_MODES)}."
            )
        self.io_schema_mode = schema_mode

        if self.max_tokens < 0:
            raise SkillResolutionError("max_tokens must be >= 0.")
        if self.max_entries < 0:
            raise SkillResolutionError("max_entries must be >= 0.")
        if self.max_steps < 0:
            raise SkillResolutionError("max_steps must be >= 0.")
        if self.step_max_chars < 0:
            raise SkillResolutionError("step_max_chars must be >= 0.")
        if not isinstance(self.adaptive_order, list) or not self.adaptive_order:
            raise SkillResolutionError("adaptive_order must be a non-empty list.")
        normalized_order = []
        for mode in self.adaptive_order:
            if not isinstance(mode, str):
                continue
            normalized = _MODE_ALIASES.get(mode.strip().lower())
            if normalized in {"full", "summary", "ref"} and normalized not in normalized_order:
                normalized_order.append(normalized)
        if not normalized_order:
            raise SkillResolutionError("adaptive_order must include at least one of full/summary/ref.")
        self.adaptive_order = normalized_order


def _estimate_tokens(text: str, *, chars_per_token: int) -> int:
    if chars_per_token <= 0:
        return len(text)
    return max(1, int(math.ceil(len(text) / chars_per_token)))


def _truncate(text: str, *, max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    return f"{text[: max(0, max_chars - 3)]}..."


def _truncate_to_tokens(text: str, *, max_tokens: int, chars_per_token: int) -> str:
    if max_tokens <= 0:
        return ""
    if chars_per_token <= 0:
        return _truncate(text, max_chars=max_tokens)
    return _truncate(text, max_chars=max_tokens * chars_per_token)


def _summary_line(skill: SkillArtifact, config: SkillResolutionConfig) -> str:
    parts = [skill.ref()]
    if config.include_type:
        parts.append(f"type={skill.type}")
    if config.include_tags:
        tags = skill.spec.get("tags") or []
        if isinstance(tags, list) and tags:
            parts.append(f"tags={','.join(str(tag) for tag in tags)}")
    line = f"- {parts[0]}"
    if len(parts) > 1:
        line += " (" + ", ".join(parts[1:]) + ")"
    if config.include_description:
        description = skill.spec.get("description") or ""
        if isinstance(description, str) and description.strip():
            line += f": {_truncate(description.strip(), max_chars=config.description_max_chars)}"
    if config.include_inputs:
        inputs = _summarize_io(skill.spec.get("inputs"), config)
        if inputs:
            line += f" | inputs: {', '.join(inputs)}"
    if config.include_outputs:
        outputs = _summarize_io(skill.spec.get("outputs"), config)
        if outputs:
            line += f" | outputs: {', '.join(outputs)}"
    if config.include_steps:
        steps = _summarize_steps(skill.spec.get("steps"), config)
        if steps:
            line += f" | steps: {'; '.join(steps)}"
    return line


def _full_payload(skill: SkillArtifact, config: SkillResolutionConfig) -> Dict[str, Any]:
    spec = copy.deepcopy(skill.spec)
    if (
        config.content_max_chars
        and isinstance(spec.get("content"), str)
        and len(spec["content"]) > config.content_max_chars
    ):
        spec["content"] = _truncate(spec["content"], max_chars=config.content_max_chars)
        spec["content_truncated"] = True
    return {
        "ref": skill.ref(),
        "spec": spec,
    }


def _summarize_io(spec: Any, config: SkillResolutionConfig) -> List[str]:
    properties, required = _extract_io_schema(spec)
    if not properties:
        return []
    if config.io_schema_mode == "names":
        return list(properties.keys())
    return _format_io_schema(properties, required)


def _extract_io_schema(spec: Any) -> tuple[Dict[str, Dict[str, Any]], List[str]]:
    if not isinstance(spec, dict):
        return {}, []
    if "properties" in spec and isinstance(spec.get("properties"), dict):
        properties = {
            str(key): (value if isinstance(value, dict) else {"type": value})
            for key, value in spec["properties"].items()
        }
        required = [str(item) for item in spec.get("required", properties.keys())]
        return properties, required

    properties: Dict[str, Dict[str, Any]] = {}
    required: List[str] = []
    for key, raw in spec.items():
        if not isinstance(key, str) or not key.strip():
            continue
        required.append(key)
        if isinstance(raw, dict):
            properties[key] = raw
        elif isinstance(raw, list):
            properties[key] = {"type": raw}
        elif isinstance(raw, str):
            properties[key] = {"type": raw}
        else:
            properties[key] = {"type": "any"}
    return properties, required


def _format_io_schema(properties: Dict[str, Dict[str, Any]], required: List[str]) -> List[str]:
    required_set = set(required)
    formatted = []
    for name, prop in properties.items():
        entry = _format_io_property(name, prop, required=name in required_set)
        if entry:
            formatted.append(entry)
    return formatted


def _format_io_property(name: str, prop: Dict[str, Any], *, required: bool) -> str:
    type_value = prop.get("type")
    type_label = "any"
    if isinstance(type_value, list):
        type_label = "|".join(str(item) for item in type_value)
    elif isinstance(type_value, str):
        type_label = type_value
    label = f"{name}:{type_label}"
    if required:
        label += "*"
    return label


def _compact_schema(properties: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    compact: Dict[str, Dict[str, Any]] = {}
    for name, prop in properties.items():
        if not isinstance(prop, dict):
            compact[name] = {"type": "any"}
            continue
        entry: Dict[str, Any] = {}
        if "type" in prop:
            entry["type"] = prop["type"]
        if "enum" in prop:
            entry["enum"] = prop["enum"]
        if "format" in prop:
            entry["format"] = prop["format"]
        if not entry:
            entry = {"type": "any"}
        compact[name] = entry
    return compact


def _summarize_steps(raw: Any, config: SkillResolutionConfig) -> List[str]:
    if not isinstance(raw, list):
        return []
    summaries: List[str] = []
    for step in raw[: config.max_steps]:
        if not isinstance(step, dict):
            continue
        note = step.get("note")
        run = step.get("run")
        parts: List[str] = []
        if isinstance(note, str) and note.strip():
            parts.append(note.strip())
        if isinstance(run, str) and run.strip():
            parts.append(run.strip())
        if not parts:
            continue
        combined = " - ".join(parts) if len(parts) > 1 else parts[0]
        summaries.append(_truncate(combined, max_chars=config.step_max_chars))
    return summaries


def _build_blocks(entries: Sequence[SkillArtifact], config: SkillResolutionConfig) -> List[str]:
    if config.max_entries == 0:
        return []

    limited = list(entries[: config.max_entries])

    if config.mode == "ref":
        if config.format == "json":
            payload = [skill.ref() for skill in limited]
            return [json.dumps(payload, ensure_ascii=True, separators=(",", ":"))]
        return [f"- {skill.ref()}" for skill in limited]

    if config.mode == "summary":
        if config.format == "json":
            payload = []
            for skill in limited:
                item: Dict[str, Any] = {
                    "ref": skill.ref(),
                    "name": skill.name,
                    "version": skill.version,
                    "type": skill.type,
                }
                if config.include_tags:
                    tags = skill.spec.get("tags") or []
                    if isinstance(tags, list):
                        item["tags"] = tags
                if config.include_description:
                    description = skill.spec.get("description") or ""
                    if isinstance(description, str) and description.strip():
                        item["description"] = _truncate(
                            description.strip(),
                            max_chars=config.description_max_chars,
                        )
                if config.include_inputs:
                    inputs_properties, inputs_required = _extract_io_schema(
                        skill.spec.get("inputs")
                    )
                    if inputs_properties:
                        if config.io_schema_mode == "schema":
                            item["inputs_schema"] = {
                                "properties": _compact_schema(inputs_properties),
                                "required": inputs_required,
                            }
                        else:
                            item["inputs"] = list(inputs_properties.keys())
                if config.include_outputs:
                    outputs_properties, outputs_required = _extract_io_schema(
                        skill.spec.get("outputs")
                    )
                    if outputs_properties:
                        if config.io_schema_mode == "schema":
                            item["outputs_schema"] = {
                                "properties": _compact_schema(outputs_properties),
                                "required": outputs_required,
                            }
                        else:
                            item["outputs"] = list(outputs_properties.keys())
                if config.include_steps:
                    steps = _summarize_steps(skill.spec.get("steps"), config)
                    if steps:
                        item["steps"] = steps
                payload.append(item)
            return [json.dumps(payload, ensure_ascii=True, separators=(",", ":"))]
        return [_summary_line(skill, config) for skill in limited]

    if config.mode == "full":
        if config.format == "json":
            payload = [_full_payload(skill, config) for skill in limited]
            return [json.dumps(payload, ensure_ascii=True, separators=(",", ":"))]
        blocks = []
        for skill in limited:
            payload = json.dumps(_full_payload(skill, config), ensure_ascii=True, separators=(",", ":"))
            blocks.append(f"- {skill.ref()}: {payload}")
        return blocks

    raise SkillResolutionError(f"Unsupported skill resolution mode: {config.mode}")


def _build_block_for_mode(skill: SkillArtifact, mode: str, config: SkillResolutionConfig) -> str:
    if mode == "ref":
        if config.format == "json":
            return json.dumps([skill.ref()], ensure_ascii=True, separators=(",", ":"))
        return f"- {skill.ref()}"
    if mode == "summary":
        if config.format == "json":
            payload = {
                "ref": skill.ref(),
                "name": skill.name,
                "version": skill.version,
                "type": skill.type,
            }
            if config.include_tags:
                tags = skill.spec.get("tags") or []
                if isinstance(tags, list):
                    payload["tags"] = tags
            if config.include_description:
                description = skill.spec.get("description") or ""
                if isinstance(description, str) and description.strip():
                    payload["description"] = _truncate(
                        description.strip(),
                        max_chars=config.description_max_chars,
                    )
            if config.include_inputs:
                inputs_properties, inputs_required = _extract_io_schema(skill.spec.get("inputs"))
                if inputs_properties:
                    if config.io_schema_mode == "schema":
                        payload["inputs_schema"] = {
                            "properties": _compact_schema(inputs_properties),
                            "required": inputs_required,
                        }
                    else:
                        payload["inputs"] = list(inputs_properties.keys())
            if config.include_outputs:
                outputs_properties, outputs_required = _extract_io_schema(skill.spec.get("outputs"))
                if outputs_properties:
                    if config.io_schema_mode == "schema":
                        payload["outputs_schema"] = {
                            "properties": _compact_schema(outputs_properties),
                            "required": outputs_required,
                        }
                    else:
                        payload["outputs"] = list(outputs_properties.keys())
            if config.include_steps:
                steps = _summarize_steps(skill.spec.get("steps"), config)
                if steps:
                    payload["steps"] = steps
            return json.dumps([payload], ensure_ascii=True, separators=(",", ":"))
        return _summary_line(skill, config)
    if mode == "full":
        if config.format == "json":
            payload = [_full_payload(skill, config)]
            return json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
        payload = json.dumps(_full_payload(skill, config), ensure_ascii=True, separators=(",", ":"))
        return f"- {skill.ref()}: {payload}"
    raise SkillResolutionError(f"Unsupported adaptive mode: {mode}")


def resolve_skills(entries: Sequence[SkillArtifact], config: SkillResolutionConfig) -> str:
    if not entries:
        return ""

    header = f"## {config.section_title}"
    section_lines = [header]
    used_tokens = _estimate_tokens(header, chars_per_token=config.chars_per_token)

    if config.mode == "adaptive":
        remaining = config.max_tokens - used_tokens
        if remaining <= 0:
            return ""
        for skill in entries[: config.max_entries]:
            block = _select_adaptive_block(skill, remaining, config)
            if not block:
                break
            section_lines.append(block)
            used_tokens += _estimate_tokens(block, chars_per_token=config.chars_per_token)
            remaining = config.max_tokens - used_tokens
            if remaining <= 0:
                break
        if len(section_lines) == 1:
            return ""
        return "\n".join(section_lines)

    blocks = _build_blocks(entries, config)
    if not blocks:
        return ""

    for block in blocks:
        if not block:
            continue
        estimate = _estimate_tokens(block, chars_per_token=config.chars_per_token)
        remaining = config.max_tokens - used_tokens
        if remaining <= 0:
            break
        if estimate > remaining:
            truncated = _truncate_to_tokens(
                block,
                max_tokens=remaining,
                chars_per_token=config.chars_per_token,
            )
            if truncated:
                section_lines.append(truncated)
            used_tokens = config.max_tokens
            break
        section_lines.append(block)
        used_tokens += estimate

    if len(section_lines) == 1:
        return ""
    return "\n".join(section_lines)

def _select_adaptive_block(
    skill: SkillArtifact,
    remaining: int,
    config: SkillResolutionConfig,
) -> str:
    if remaining <= 0:
        return ""
    for mode in config.adaptive_order:
        block = _build_block_for_mode(skill, mode, config)
        if not block:
            continue
        estimate = _estimate_tokens(block, chars_per_token=config.chars_per_token)
        if estimate <= remaining:
            return block
    return ""

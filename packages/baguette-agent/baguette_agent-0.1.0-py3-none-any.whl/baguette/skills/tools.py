from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional
import json
import re

from ..errors import ExecutionError
from ..storage.base import StorageBackend
from .artifacts import SkillArtifact
from .injection import SkillQueryConfig
from .runtime import RunResult, SkillRunConfig, run_skill
from .trace import SkillTraceConfig, build_skill_trace_metadata, load_skill_trace_config


@dataclass
class SkillToolSpec:
    name: str
    description: str
    parameters: Dict[str, Any]
    skill_ref: str
    skill_type: str

    def to_definition(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


@dataclass
class SkillToolConfig:
    name_strategy: str = "name"  # name, ref, name_version
    name_prefix: str = "skill_"
    sanitize_names: bool = True
    description_max_chars: int = 200
    include_description: bool = True
    include_tags: bool = True


@dataclass
class SkillToolResult:
    tool_name: str
    skill_ref: str
    status: str
    output: Any
    metadata: Dict[str, Any]
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "skill_ref": self.skill_ref,
            "status": self.status,
            "output": self.output,
            "metadata": self.metadata,
            "error": self.error,
        }


def _truncate(text: str, *, max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    return f"{text[: max(0, max_chars - 3)]}..."


def _tool_name_from_ref(skill: SkillArtifact, config: SkillToolConfig) -> str:
    if config.name_strategy == "ref":
        base = skill.ref()
    elif config.name_strategy == "name_version":
        base = f"{skill.name}_{skill.version}"
    else:
        base = skill.name
    if config.sanitize_names:
        base = re.sub(r"[^A-Za-z0-9_-]", "_", base)
        if not base:
            base = "skill"
        if base[0].isdigit():
            base = f"{config.name_prefix}{base}"
    if config.name_prefix and not base.startswith(config.name_prefix):
        base = f"{config.name_prefix}{base}"
    return base


def _looks_like_schema(spec: Dict[str, Any]) -> bool:
    for key in ("$schema", "$id", "type", "properties", "required", "additionalProperties"):
        if key in spec:
            return True
    return False


def _build_io_schema(io_spec: Any) -> Dict[str, Any]:
    if io_spec is None:
        return {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": True,
        }
    if not isinstance(io_spec, dict):
        raise ValueError("Skill inputs must be a mapping or JSON schema object.")
    if _looks_like_schema(io_spec):
        return io_spec

    properties: Dict[str, Any] = {}
    required: List[str] = []
    for key, raw in io_spec.items():
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
            properties[key] = {}
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": True,
    }


def build_tool_spec(skill: SkillArtifact, config: SkillToolConfig) -> SkillToolSpec:
    name = _tool_name_from_ref(skill, config)
    description = f"Execute skill {skill.ref()}"
    if config.include_description:
        raw = skill.spec.get("description")
        if isinstance(raw, str) and raw.strip():
            description = _truncate(raw.strip(), max_chars=config.description_max_chars)
    if config.include_tags:
        tags = skill.spec.get("tags") or []
        if isinstance(tags, list) and tags:
            description = f"{description} (tags: {', '.join(str(tag) for tag in tags)})"
    parameters = _build_io_schema(skill.spec.get("inputs"))
    return SkillToolSpec(
        name=name,
        description=description,
        parameters=parameters,
        skill_ref=skill.ref(),
        skill_type=skill.type,
    )


def _parse_skill_ref(ref: str) -> tuple[str, Optional[str]]:
    if "@" in ref:
        name, version = ref.split("@", 1)
        return name.strip(), version.strip()
    return ref.strip(), None


def _query_skills(storage: StorageBackend, query: SkillQueryConfig) -> List[SkillArtifact]:
    if query.limit <= 0:
        return []

    skills: List[SkillArtifact] = []
    if query.refs:
        seen: set[str] = set()
        for ref in query.refs:
            name, version = _parse_skill_ref(ref)
            if not name:
                continue
            skill = storage.get_skill(name, version)
            if skill.artifact_id in seen:
                continue
            seen.add(skill.artifact_id)
            skills.append(skill)
        return skills[: query.limit]

    tags = _normalize_tags(query.tags or [])
    if query.names:
        for name in query.names:
            if not isinstance(name, str) or not name.strip():
                continue
            skills.extend(storage.list_skills(name=name.strip()))
    else:
        skills = list(storage.list_skills())

    if tags:
        skills = [skill for skill in skills if _skill_has_tags(skill, tags)]

    if query.deduplicate_by_name:
        skills = _dedupe_latest(skills)

    skills.sort(key=lambda skill: skill.updated_at, reverse=True)
    return skills[: query.limit]


def _normalize_tags(tags: Iterable[str]) -> set[str]:
    normalized = set()
    for tag in tags:
        if not isinstance(tag, str):
            continue
        stripped = tag.strip()
        if stripped:
            normalized.add(stripped)
    return normalized


def _skill_has_tags(skill: SkillArtifact, tags: set[str]) -> bool:
    if not tags:
        return True
    raw = skill.spec.get("tags") or []
    if not isinstance(raw, list):
        return False
    return any(tag in raw for tag in tags)


def _dedupe_latest(skills: Iterable[SkillArtifact]) -> List[SkillArtifact]:
    latest: Dict[str, SkillArtifact] = {}
    for skill in skills:
        existing = latest.get(skill.name)
        if existing is None or skill.updated_at > existing.updated_at:
            latest[skill.name] = skill
    return list(latest.values())


class SkillToolRegistry:
    def __init__(self, specs: Iterable[SkillToolSpec]) -> None:
        self._specs = {spec.name: spec for spec in specs}

    @classmethod
    def from_storage(
        cls,
        storage: StorageBackend,
        *,
        query: Optional[SkillQueryConfig] = None,
        config: Optional[SkillToolConfig] = None,
    ) -> "SkillToolRegistry":
        query = query or SkillQueryConfig()
        config = config or SkillToolConfig()
        skills = _query_skills(storage, query)
        specs = [build_tool_spec(skill, config) for skill in skills]
        return cls(specs)

    def definitions(self) -> List[Dict[str, Any]]:
        return [spec.to_definition() for spec in self._specs.values()]

    def resolve(self, tool_name: str) -> SkillToolSpec:
        if tool_name not in self._specs:
            raise ExecutionError(f"Unknown tool: {tool_name}")
        return self._specs[tool_name]

    def __len__(self) -> int:
        return len(self._specs)


def _parse_tool_args(arguments: Any) -> Dict[str, Any]:
    if arguments is None:
        return {}
    if isinstance(arguments, dict):
        return arguments
    if isinstance(arguments, str):
        raw = arguments.strip()
        if not raw:
            return {}
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid tool arguments JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError("Tool arguments JSON must be an object.")
        return payload
    raise ValueError("Tool arguments must be a dict or JSON string.")


def execute_tool_call(
    storage: StorageBackend,
    tool_name: str,
    arguments: Any,
    *,
    registry: Optional[SkillToolRegistry] = None,
    trace_config: Optional[SkillTraceConfig] = None,
    run_config: Optional[SkillRunConfig] = None,
    dry_run: bool = False,
) -> SkillToolResult:
    if registry is None:
        raise ExecutionError("SkillToolRegistry is required to execute tool calls.")
    trace_config = trace_config or load_skill_trace_config()
    spec = registry.resolve(tool_name)
    name, version = _parse_skill_ref(spec.skill_ref)
    skill = storage.get_skill(name, version)
    inputs = _parse_tool_args(arguments)
    skill_run = run_skill(skill, inputs, dry_run, run_config)
    run_result = skill_run.run
    metadata = build_skill_trace_metadata(
        tool_name=spec.name,
        skill_ref=spec.skill_ref,
        inputs=inputs,
        run_result=run_result,
        duration_ms=skill_run.duration_ms,
        attempt=skill_run.attempt,
        max_attempts=skill_run.max_attempts,
        idempotency_key=skill_run.idempotency_key,
        config=trace_config,
    )
    return SkillToolResult(
        tool_name=spec.name,
        skill_ref=spec.skill_ref,
        status=run_result.status,
        output=run_result.output,
        metadata=metadata,
        error=run_result.error,
    )

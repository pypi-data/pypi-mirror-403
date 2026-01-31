from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, TYPE_CHECKING

from ..skills.artifacts import SkillArtifact
from ..skills.resolver import SkillResolutionConfig, resolve_skills

if TYPE_CHECKING:
    from ..adapters.sdk import AdapterContext
    from ..storage.base import StorageBackend


class SkillInjectionError(RuntimeError):
    pass


@dataclass
class SkillQueryConfig:
    refs: Optional[List[str]] = None
    names: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    limit: int = 20
    deduplicate_by_name: bool = True

SkillInjectionConfig = SkillResolutionConfig


def _parse_skill_ref(ref: str) -> tuple[str, Optional[str]]:
    if "@" in ref:
        name, version = ref.split("@", 1)
        return name.strip(), version.strip()
    return ref.strip(), None


def _normalize_tags(tags: Sequence[str]) -> set[str]:
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
    latest: dict[str, SkillArtifact] = {}
    for skill in skills:
        existing = latest.get(skill.name)
        if existing is None or skill.updated_at > existing.updated_at:
            latest[skill.name] = skill
    return list(latest.values())


def _query_skills(storage: "StorageBackend", query: SkillQueryConfig) -> List[SkillArtifact]:
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


def inject_skills(
    prompt: str,
    entries: Sequence[SkillArtifact],
    config: SkillInjectionConfig,
) -> str:
    section = resolve_skills(entries, config)
    if not section:
        return prompt
    if config.placement == "prepend":
        return f"{section}\n\n{prompt}"
    return f"{prompt}\n\n{section}"


class SkillInjectionHook:
    def __init__(
        self,
        *,
        query: Optional[SkillQueryConfig] = None,
        config: Optional[SkillInjectionConfig] = None,
    ) -> None:
        self.query = query or SkillQueryConfig()
        self.config = config or SkillInjectionConfig()

    def before_prompt(self, prompt: str, context: "AdapterContext") -> str:
        storage = context.storage
        if storage is None:
            return prompt
        entries = _query_skills(storage, self.query)
        if not entries:
            return prompt
        return inject_skills(prompt, entries, self.config)

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional
import copy
import hashlib
import json
import re

import semver
import yaml
from jsonschema import Draft202012Validator, SchemaError

from ..schema import SkillSchemaError, validate_artifact, validate_skill_spec
from ..utils import canonical_json, deterministic_uuid, utcnow_iso


class SkillValidationError(ValueError):
    pass


_FRONTMATTER_RE = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n?", re.DOTALL)
_SCHEMA_HINT_KEYS = {
    "$schema",
    "$id",
    "type",
    "properties",
    "required",
    "additionalProperties",
    "oneOf",
    "anyOf",
    "allOf",
}
_SIMPLE_TYPES = {"string", "number", "integer", "boolean", "object", "array", "null", "any"}


@dataclass
class Artifact:
    name: str
    version: str
    type: str
    kind: str
    spec: Dict[str, Any]
    artifact_id: str = ""
    created_at: str = field(default_factory=utcnow_iso)
    updated_at: str = field(default_factory=utcnow_iso)
    idempotency_key: str = ""
    lineage: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise SkillValidationError("Artifact name must be a non-empty string.")
        if not isinstance(self.version, str) or not self.version.strip():
            raise SkillValidationError("Artifact version must be a non-empty string.")
        if not isinstance(self.type, str) or not self.type.strip():
            raise SkillValidationError("Artifact type must be a non-empty string.")
        if not isinstance(self.kind, str) or not self.kind.strip():
            raise SkillValidationError("Artifact kind must be a non-empty string.")
        if not isinstance(self.spec, dict):
            raise SkillValidationError("Artifact spec must be a dictionary.")
        if not isinstance(self.lineage, dict):
            raise SkillValidationError("Artifact lineage must be a dictionary.")
        canonical_json(self.lineage)
        try:
            validate_skill_spec(self.spec)
        except SkillSchemaError as exc:
            raise SkillValidationError(str(exc)) from exc
        if self.spec.get("name") != self.name:
            raise SkillValidationError("Artifact spec name must match artifact name.")
        if self.spec.get("version") != self.version:
            raise SkillValidationError("Artifact spec version must match artifact version.")
        if self.spec.get("type") != self.type:
            raise SkillValidationError("Artifact spec type must match artifact type.")
        if self.spec.get("kind") != self.kind:
            raise SkillValidationError("Artifact spec kind must match artifact kind.")

        try:
            semver.VersionInfo.parse(self.version)
        except ValueError as exc:
            raise SkillValidationError(
                f"Artifact version must be valid semver: {self.version}"
            ) from exc

        if not self.idempotency_key:
            self.idempotency_key = f"{self.name}@{self.version}"
        if not self.artifact_id:
            self.artifact_id = deterministic_uuid("artifact", self.idempotency_key)
        if not self.updated_at:
            self.updated_at = self.created_at
        try:
            validate_artifact(self.to_dict())
        except SkillSchemaError as exc:
            raise SkillValidationError(str(exc)) from exc

    def ref(self) -> str:
        return f"{self.name}@{self.version}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "name": self.name,
            "version": self.version,
            "type": self.type,
            "kind": self.kind,
            "spec": self.spec,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "idempotency_key": self.idempotency_key,
            "lineage": self.lineage,
        }


class SkillArtifact(Artifact):
    pass


def _parse_frontmatter(raw: str) -> tuple[Dict[str, Any], str]:
    match = _FRONTMATTER_RE.match(raw)
    if not match:
        return {}, raw
    payload = match.group(1)
    data = yaml.safe_load(payload) or {}
    if not isinstance(data, dict):
        raise SkillValidationError("Frontmatter must be a YAML mapping.")
    content = raw[match.end():].lstrip("\r\n")
    return data, content


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_structured(path: Path) -> Dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(raw)
    return yaml.safe_load(raw)


def _infer_type(spec: Dict[str, Any]) -> Optional[str]:
    if "steps" in spec:
        return "workflow"
    if "content" in spec:
        return "prompt"
    return None


def _looks_like_schema(spec: Dict[str, Any]) -> bool:
    return any(key in spec for key in _SCHEMA_HINT_KEYS)


def _coerce_field_schema(name: str, raw: Any, *, label: str) -> Dict[str, Any]:
    if isinstance(raw, str):
        normalized = raw.strip().lower()
        if normalized == "any":
            return {}
        if normalized not in _SIMPLE_TYPES:
            raise SkillValidationError(
                f"{label} schema for '{name}' must use a JSON schema object or a simple type."
            )
        return {"type": normalized}
    if isinstance(raw, list) and all(isinstance(item, str) for item in raw):
        return {"type": [item.strip().lower() for item in raw]}
    if isinstance(raw, dict):
        return raw
    raise SkillValidationError(
        f"{label} schema for '{name}' must be a JSON schema object or a simple type."
    )


def _coerce_io_schema(io_spec: Dict[str, Any], *, label: str) -> Dict[str, Any]:
    properties: Dict[str, Any] = {}
    required: list[str] = []
    for key, raw in io_spec.items():
        if not isinstance(key, str) or not key.strip():
            raise SkillValidationError(f"{label} schema keys must be non-empty strings.")
        properties[key] = _coerce_field_schema(key, raw, label=label)
        required.append(key)
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": True,
    }


def _build_io_schema(io_spec: Any, *, label: str) -> Optional[Dict[str, Any]]:
    if io_spec is None:
        return None
    if not isinstance(io_spec, dict):
        raise SkillValidationError(f"{label} must be a mapping or JSON schema object.")
    schema = io_spec if _looks_like_schema(io_spec) else _coerce_io_schema(io_spec, label=label)
    schema_type = schema.get("type")
    if schema_type:
        if isinstance(schema_type, list):
            if "object" not in schema_type:
                raise SkillValidationError(f"{label} schema must accept an object.")
        elif schema_type != "object":
            raise SkillValidationError(f"{label} schema must accept an object.")
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise SkillValidationError(f"{label} schema error: {exc.message}") from exc
    return schema


def validate_skill_inputs(spec: Dict[str, Any], inputs: Dict[str, Any]) -> None:
    schema = _build_io_schema(spec.get("inputs"), label="inputs")
    if schema is None:
        return
    if not isinstance(inputs, dict):
        raise ValueError("Skill inputs must be a JSON object.")
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(inputs), key=lambda err: err.path)
    if errors:
        error = errors[0]
        path = ".".join(str(item) for item in error.path) or "<root>"
        raise ValueError(f"Input validation error at {path}: {error.message}")


def _validate_io_spec(spec: Dict[str, Any]) -> None:
    _build_io_schema(spec.get("inputs"), label="inputs")
    _build_io_schema(spec.get("outputs"), label="outputs")


def _normalize_spec(
    spec: Dict[str, Any],
    *,
    name: Optional[str],
    version: Optional[str],
    skill_type: Optional[str],
    source_path: Optional[Path] = None,
    source_checksum: Optional[str] = None,
    source_label: Optional[str] = None,
) -> Dict[str, Any]:
    if name:
        spec["name"] = name
    if version:
        spec["version"] = version
    if skill_type:
        spec["type"] = skill_type

    spec.setdefault("kind", "Skill")
    if "type" not in spec:
        inferred = _infer_type(spec)
        if inferred:
            spec["type"] = inferred

    if "name" not in spec or "version" not in spec or "type" not in spec:
        raise SkillValidationError("Skill spec requires name, version, and type.")

    if spec["type"] not in {"workflow", "prompt"}:
        raise SkillValidationError("Skill type must be workflow or prompt.")

    source = dict(spec.get("source", {}))
    if source_path:
        source["path"] = str(source_path)
        source["checksum"] = _sha256_bytes(source_path.read_bytes())
    elif source_checksum:
        source.setdefault("path", source_label or "<inline>")
        source.setdefault("checksum", source_checksum)

    if source:
        spec["source"] = source

    return spec


def load_skill_file(
    path: str | Path,
    *,
    name: Optional[str] = None,
    version: Optional[str] = None,
    skill_type: Optional[str] = None,
    lineage: Optional[Dict[str, Any]] = None,
    idempotency_key: Optional[str] = None,
) -> SkillArtifact:
    source_path = Path(path)
    if not source_path.exists():
        raise FileNotFoundError(f"Skill file not found: {source_path}")

    if source_path.suffix.lower() == ".md":
        raw = source_path.read_text(encoding="utf-8")
        frontmatter, content = _parse_frontmatter(raw)
        spec = dict(frontmatter)
        spec.setdefault("kind", "Skill")
        spec.setdefault("name", source_path.stem)
        spec.setdefault("version", "0.1.0")
        spec.setdefault("type", "prompt")
        spec["content"] = content
    else:
        spec = _load_structured(source_path)
        if not isinstance(spec, dict):
            raise SkillValidationError("Skill file must parse to a dictionary.")

    spec = _normalize_spec(
        spec,
        name=name,
        version=version,
        skill_type=skill_type,
        source_path=source_path,
    )

    try:
        validate_skill_spec(spec)
    except SkillSchemaError as exc:
        raise SkillValidationError(str(exc)) from exc
    _validate_io_spec(spec)

    normalized_lineage = lineage or {}
    normalized_lineage.setdefault("source", spec.get("source", {}))

    return SkillArtifact(
        artifact_id="",
        name=spec["name"],
        version=spec["version"],
        type=spec["type"],
        kind=spec["kind"],
        spec=spec,
        lineage=normalized_lineage,
        idempotency_key=idempotency_key or "",
    )


def load_skill_spec(
    spec: Dict[str, Any],
    *,
    name: Optional[str] = None,
    version: Optional[str] = None,
    skill_type: Optional[str] = None,
    lineage: Optional[Dict[str, Any]] = None,
    idempotency_key: Optional[str] = None,
    source_label: str = "<inline>",
) -> SkillArtifact:
    if not isinstance(spec, dict):
        raise SkillValidationError("Skill spec must be a dictionary.")

    normalized_spec = copy.deepcopy(spec)
    checksum = _sha256_bytes(canonical_json(normalized_spec).encode("utf-8"))
    normalized_spec = _normalize_spec(
        normalized_spec,
        name=name,
        version=version,
        skill_type=skill_type,
        source_checksum=checksum,
        source_label=source_label,
    )

    try:
        validate_skill_spec(normalized_spec)
    except SkillSchemaError as exc:
        raise SkillValidationError(str(exc)) from exc
    _validate_io_spec(normalized_spec)

    normalized_lineage = lineage or {}
    normalized_lineage.setdefault("source", normalized_spec.get("source", {}))

    return SkillArtifact(
        artifact_id="",
        name=normalized_spec["name"],
        version=normalized_spec["version"],
        type=normalized_spec["type"],
        kind=normalized_spec["kind"],
        spec=normalized_spec,
        lineage=normalized_lineage,
        idempotency_key=idempotency_key or "",
    )

from __future__ import annotations

from typing import Any, Dict, Iterable

import semver
from jsonschema import Draft202012Validator


class SkillSchemaError(ValueError):
    pass


_STEP_SCHEMA = {
    "type": "object",
    "properties": {
        "run": {"type": "string"},
        "note": {"type": "string"},
    },
    "minProperties": 1,
    "additionalProperties": True,
}


SKILL_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Baguette Skill Artifact",
    "type": "object",
    "required": ["kind", "name", "version", "type"],
    "properties": {
        "kind": {"const": "Skill"},
        "name": {"type": "string", "minLength": 1},
        "version": {"type": "string", "minLength": 1},
        "type": {"type": "string", "enum": ["workflow", "prompt"]},
        "description": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "inputs": {"type": "object"},
        "outputs": {"type": "object"},
        "steps": {"type": "array", "items": _STEP_SCHEMA, "minItems": 1},
        "constraints": {"type": "array", "items": {"type": "string"}},
        "success": {
            "type": "object",
            "properties": {"condition": {"type": "string"}},
            "required": ["condition"],
            "additionalProperties": True,
        },
        "fallback": {"type": "array", "items": _STEP_SCHEMA},
        "content": {"type": "string"},
        "source": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "checksum": {"type": "string"},
            },
            "required": ["path", "checksum"],
            "additionalProperties": True,
        },
    },
    "allOf": [
        {
            "if": {"properties": {"type": {"const": "workflow"}}},
            "then": {"required": ["steps"]},
        },
        {
            "if": {"properties": {"type": {"const": "prompt"}}},
            "then": {"required": ["content"]},
        },
    ],
    "additionalProperties": True,
}

LINEAGE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "parents": {"type": "array", "items": {"type": "string"}},
        "origin": {"type": "object"},
        "tx_id": {"type": "string"},
        "trace_id": {"type": "string"},
        "artifact_id": {"type": "string"},
    },
    "additionalProperties": True,
}

MEMORY_ENTRY_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Baguette Memory Entry",
    "type": "object",
    "required": [
        "entry_id",
        "idempotency_key",
        "key",
        "value",
        "type",
        "source",
        "confidence",
        "created_at",
        "metadata",
        "lineage",
    ],
    "properties": {
        "entry_id": {"type": "string", "minLength": 1},
        "idempotency_key": {"type": "string", "minLength": 1},
        "key": {"type": "string", "minLength": 1},
        "value": {},
        "type": {"type": "string", "minLength": 1},
        "source": {"type": "string", "minLength": 1},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "created_at": {"type": "string", "minLength": 1},
        "metadata": {"type": "object"},
        "lineage": LINEAGE_SCHEMA,
        "tx_id": {"type": ["string", "null"]},
    },
    "additionalProperties": True,
}

ARTIFACT_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Baguette Artifact",
    "type": "object",
    "required": [
        "artifact_id",
        "idempotency_key",
        "name",
        "version",
        "type",
        "kind",
        "spec",
        "created_at",
        "updated_at",
        "lineage",
    ],
    "properties": {
        "artifact_id": {"type": "string", "minLength": 1},
        "idempotency_key": {"type": "string", "minLength": 1},
        "name": {"type": "string", "minLength": 1},
        "version": {"type": "string", "minLength": 1},
        "type": {"type": "string", "minLength": 1},
        "kind": {"type": "string", "minLength": 1},
        "spec": {"type": "object"},
        "created_at": {"type": "string", "minLength": 1},
        "updated_at": {"type": "string", "minLength": 1},
        "lineage": LINEAGE_SCHEMA,
    },
    "additionalProperties": True,
}

TRANSACTION_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Baguette Transaction",
    "type": "object",
    "required": [
        "tx_id",
        "idempotency_key",
        "actor",
        "reason",
        "status",
        "created_at",
        "updated_at",
        "metadata",
        "lineage",
    ],
    "properties": {
        "tx_id": {"type": "string", "minLength": 1},
        "idempotency_key": {"type": "string", "minLength": 1},
        "actor": {"type": "string", "minLength": 1},
        "reason": {"type": "string", "minLength": 1},
        "status": {"type": "string", "minLength": 1},
        "created_at": {"type": "string", "minLength": 1},
        "updated_at": {"type": "string", "minLength": 1},
        "committed_at": {"type": ["string", "null"]},
        "rolled_back_at": {"type": ["string", "null"]},
        "metadata": {"type": "object"},
        "lineage": LINEAGE_SCHEMA,
        "validation": {"type": ["object", "null"]},
    },
    "additionalProperties": True,
}

DECISION_TRACE_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Baguette Decision Trace",
    "type": "object",
    "required": [
        "trace_id",
        "idempotency_key",
        "timestamp",
        "decision",
        "reason",
        "confidence",
        "result",
        "metadata",
        "lineage",
    ],
    "properties": {
        "trace_id": {"type": "string", "minLength": 1},
        "idempotency_key": {"type": "string", "minLength": 1},
        "timestamp": {"type": "string", "minLength": 1},
        "decision": {"type": "string", "minLength": 1},
        "skill_ref": {"type": ["string", "null"]},
        "reason": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "result": {"type": "string", "minLength": 1},
        "metadata": {"type": "object"},
        "tx_id": {"type": ["string", "null"]},
        "lineage": LINEAGE_SCHEMA,
    },
    "additionalProperties": True,
}


def validate_skill_spec(spec: Dict[str, Any]) -> None:
    validator = Draft202012Validator(SKILL_SCHEMA)
    errors = sorted(validator.iter_errors(spec), key=lambda err: err.path)
    if errors:
        error = errors[0]
        path = ".".join(str(item) for item in error.path) or "<root>"
        raise SkillSchemaError(f"Skill schema error at {path}: {error.message}")

    _validate_semver(spec.get("version"))


def validate_memory_entry(payload: Dict[str, Any]) -> None:
    _validate_schema(MEMORY_ENTRY_SCHEMA, payload, "MemoryEntry")


def validate_artifact(payload: Dict[str, Any]) -> None:
    _validate_schema(ARTIFACT_SCHEMA, payload, "Artifact")
    _validate_semver(payload.get("version"))


def validate_transaction(payload: Dict[str, Any]) -> None:
    _validate_schema(TRANSACTION_SCHEMA, payload, "Transaction")


def validate_decision_trace(payload: Dict[str, Any]) -> None:
    _validate_schema(DECISION_TRACE_SCHEMA, payload, "DecisionTrace")


def _validate_semver(version: Any) -> None:
    if not isinstance(version, str):
        raise SkillSchemaError("Skill version must be a string.")
    try:
        semver.VersionInfo.parse(version)
    except ValueError as exc:
        raise SkillSchemaError(f"Skill version must be valid semver: {version}") from exc


def _validate_schema(schema: Dict[str, Any], payload: Dict[str, Any], name: str) -> None:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda err: err.path)
    if errors:
        error = errors[0]
        path = ".".join(str(item) for item in error.path) or "<root>"
        raise SkillSchemaError(f"{name} schema error at {path}: {error.message}")

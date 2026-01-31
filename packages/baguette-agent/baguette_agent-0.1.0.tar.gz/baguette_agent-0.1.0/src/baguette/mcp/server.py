from __future__ import annotations

import argparse
import base64
import json
import logging
import sys
from dataclasses import fields
from typing import Any, Callable, Dict, Iterable, Optional
from urllib.parse import parse_qs, urlparse

from .. import __version__
from ..audit.traces import DecisionTrace
from ..cli.storage import build_storage
from ..errors import ExecutionError
from ..memory.transactions import MemoryEntry, ValidationRecord
from ..skills.artifacts import SkillArtifact
from ..skills.resolver import SkillResolutionConfig, resolve_skills
from ..skills.runtime import SkillRunConfig, run_skill
from ..skills.trace import SkillTraceConfig, build_skill_trace_metadata, load_skill_trace_config
from ..storage.base import StorageBackend


JSONRPC_PARSE_ERROR = -32700
JSONRPC_INVALID_REQUEST = -32600
JSONRPC_METHOD_NOT_FOUND = -32601
JSONRPC_INVALID_PARAMS = -32602
JSONRPC_INTERNAL_ERROR = -32603
JSONRPC_RESOURCE_NOT_FOUND = -32002

SUPPORTED_PROTOCOL_VERSIONS = ["2025-06-18", "2025-03-26", "2024-11-05"]
DEFAULT_PROTOCOL_VERSION = SUPPORTED_PROTOCOL_VERSIONS[0]
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200

_LOG_LEVELS = {
    "debug": 10,
    "info": 20,
    "notice": 25,
    "warning": 30,
    "error": 40,
    "critical": 50,
    "alert": 60,
    "emergency": 70,
}

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


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _coerce_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    return None


def _coerce_float(value: Any, *, default: float) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return default
    return default


def _coerce_optional_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _coerce_int(value: Any, *, default: int) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return default
    return default


def _decode_cursor(cursor: Optional[str]) -> int:
    if cursor is None or cursor == "":
        return 0
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii"))
        payload = json.loads(raw.decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid cursor.") from exc
    try:
        offset = int(payload.get("offset", 0))
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid cursor.") from exc
    if offset < 0:
        raise ValueError("Invalid cursor.")
    return offset


def _encode_cursor(offset: int) -> str:
    payload = json.dumps({"offset": offset}, ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii")


def _paginate(items: list, *, cursor: Optional[str], limit: Optional[int]) -> tuple[list, Optional[str]]:
    if cursor is None and limit is None:
        return list(items), None
    offset = _decode_cursor(cursor)
    page_size = _coerce_int(limit, default=DEFAULT_PAGE_SIZE)
    if page_size <= 0:
        return [], None
    page_size = min(page_size, MAX_PAGE_SIZE)
    page = items[offset : offset + page_size]
    next_cursor = None
    if offset + page_size < len(items):
        next_cursor = _encode_cursor(offset + page_size)
    return page, next_cursor


def _ensure_dict(value: Any, *, default: Optional[dict] = None) -> dict:
    if value is None:
        return default or {}
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object.")
    return value


def _parse_skill_ref(ref: str) -> tuple[str, Optional[str]]:
    if "@" in ref:
        name, version = ref.split("@", 1)
        return name.strip(), version.strip()
    return ref.strip(), None


def _parse_query_params(raw: dict[str, list[str]]) -> dict:
    params: dict = {}
    for key, values in raw.items():
        if not values:
            continue
        if key in {"tags", "names", "refs"}:
            params[key] = [item for item in values if item]
        else:
            params[key] = values[-1]
    return params


def _parse_resource_uri(uri: str) -> tuple[str, Optional[str], dict]:
    parsed = urlparse(uri)
    if parsed.scheme != "baguette":
        raise ValueError("Unsupported resource URI scheme.")
    base = parsed.netloc or ""
    path = parsed.path.lstrip("/")
    if not base and path:
        parts = path.split("/", 1)
        base = parts[0]
        path = parts[1] if len(parts) > 1 else ""
    if not base:
        raise ValueError("Invalid resource URI.")
    query_params = _parse_query_params(parse_qs(parsed.query))
    return base, path or None, query_params


def _skill_summary(skill: SkillArtifact, *, include_spec: bool) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "ref": skill.ref(),
        "name": skill.name,
        "version": skill.version,
        "type": skill.type,
        "updated_at": skill.updated_at,
        "tags": skill.spec.get("tags") or [],
        "description": skill.spec.get("description"),
    }
    if include_spec:
        payload.update(
            {
                "artifact_id": skill.artifact_id,
                "created_at": skill.created_at,
                "spec": skill.spec,
                "lineage": skill.lineage,
            }
        )
    return payload


def _dedupe_latest(skills: Iterable[SkillArtifact]) -> list[SkillArtifact]:
    latest: Dict[str, SkillArtifact] = {}
    for skill in skills:
        existing = latest.get(skill.name)
        if existing is None or skill.updated_at > existing.updated_at:
            latest[skill.name] = skill
    return list(latest.values())


def _filter_by_tags(skills: Iterable[SkillArtifact], tags: list[str]) -> list[SkillArtifact]:
    if not tags:
        return list(skills)
    required = set(tags)
    filtered: list[SkillArtifact] = []
    for skill in skills:
        raw = skill.spec.get("tags") or []
        if isinstance(raw, list) and any(tag in raw for tag in required):
            filtered.append(skill)
    return filtered


def _looks_like_schema(raw: Any) -> bool:
    return isinstance(raw, dict) and any(key in raw for key in _SCHEMA_HINT_KEYS)


def _prompt_arguments_from_inputs(inputs: Any) -> list[dict]:
    if inputs is None:
        return []
    if not isinstance(inputs, dict):
        return []
    arguments: list[dict] = []
    if _looks_like_schema(inputs):
        schema_type = inputs.get("type")
        if schema_type not in {None, "object"} and not (
            isinstance(schema_type, list) and "object" in schema_type
        ):
            return []
        properties = inputs.get("properties") if isinstance(inputs.get("properties"), dict) else {}
        required = inputs.get("required")
        required_set = {str(item) for item in required} if isinstance(required, list) else set()
        for name, payload in properties.items():
            if not isinstance(name, str) or not name.strip():
                continue
            description = None
            if isinstance(payload, dict):
                description = payload.get("description") or payload.get("title")
            arguments.append(
                {
                    "name": name,
                    "description": description,
                    "required": name in required_set,
                }
            )
        return arguments

    for name, raw in inputs.items():
        if not isinstance(name, str) or not name.strip():
            continue
        description = None
        required = True
        if isinstance(raw, dict):
            description = raw.get("description") or raw.get("title")
            if isinstance(raw.get("required"), bool):
                required = raw.get("required")
        arguments.append({"name": name, "description": description, "required": required})
    return arguments


def _prompt_summary(skill: SkillArtifact) -> dict:
    spec = skill.spec
    return {
        "name": skill.name,
        "description": spec.get("description"),
        "arguments": _prompt_arguments_from_inputs(spec.get("inputs")),
    }


def _query_skills(storage: StorageBackend, params: dict) -> list[SkillArtifact]:
    limit = params.get("limit", 20)
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 20
    if limit <= 0:
        return []

    refs = _as_list(params.get("refs"))
    if refs:
        skills: list[SkillArtifact] = []
        seen: set[str] = set()
        for ref in refs:
            name, version = _parse_skill_ref(ref)
            if not name:
                continue
            skill = storage.get_skill(name, version)
            if skill.artifact_id in seen:
                continue
            seen.add(skill.artifact_id)
            skills.append(skill)
        return skills[:limit]

    names = _as_list(params.get("names"))
    if names:
        skills = []
        for name in names:
            skills.extend(storage.list_skills(name=name))
    else:
        skills = list(storage.list_skills())

    tags = _as_list(params.get("tags"))
    skills = _filter_by_tags(skills, tags)
    if _coerce_bool(params.get("deduplicate_by_name")) is not False:
        skills = _dedupe_latest(skills)
    skills.sort(key=lambda skill: skill.updated_at, reverse=True)
    return skills[:limit]


def _dataclass_from_dict(cls, raw: Any):
    if not isinstance(raw, dict):
        return cls()
    field_names = {field.name for field in fields(cls)}
    kwargs = {name: raw[name] for name in field_names if name in raw}
    return cls(**kwargs)


def _parse_run_config(raw: Any) -> SkillRunConfig:
    if not isinstance(raw, dict):
        return SkillRunConfig().normalize()
    data = dict(raw)
    retry_on = data.get("retry_on")
    if isinstance(retry_on, str):
        data["retry_on"] = [item.strip() for item in retry_on.split(",") if item.strip()]
    backoff_ms = data.get("backoff_ms")
    if isinstance(backoff_ms, str):
        data["backoff_ms"] = [
            int(item.strip()) for item in backoff_ms.split(",") if item.strip().isdigit()
        ]
    config = _dataclass_from_dict(SkillRunConfig, data)
    return config.normalize()


def _parse_trace_config(raw: Any) -> SkillTraceConfig:
    config = load_skill_trace_config()
    if not isinstance(raw, dict):
        return config
    inputs_preview = _coerce_bool(raw.get("inputs_preview"))
    output_preview = _coerce_bool(raw.get("output_preview"))
    preview_max = raw.get("preview_max_chars")
    if inputs_preview is not None:
        config.include_inputs_preview = inputs_preview
    if output_preview is not None:
        config.include_output_preview = output_preview
    if isinstance(preview_max, int):
        config.preview_max_chars = max(0, preview_max)
    return config


def _tool_text(payload: Any) -> dict:
    return {
        "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
        "structuredContent": payload,
        "isError": False,
    }


def _tool_error(message: str) -> dict:
    return {"content": [{"type": "text", "text": message}], "isError": True}

_TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "skills.list",
        "description": "List skills with optional filters.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "names": {"type": "array", "items": {"type": "string"}},
                "tags": {"type": "array", "items": {"type": "string"}},
                "refs": {"type": "array", "items": {"type": "string"}},
                "limit": {"type": "integer", "minimum": 1},
                "deduplicate_by_name": {"type": "boolean"},
                "include_spec": {"type": "boolean"},
            },
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "skills": {"type": "array", "items": {"type": "object"}},
                "nextCursor": {"type": "string"},
            },
            "additionalProperties": True,
        },
    },
    {
        "name": "skills.get",
        "description": "Fetch a skill artifact by ref (name or name@version).",
        "inputSchema": {
            "type": "object",
            "properties": {"ref": {"type": "string"}, "include_spec": {"type": "boolean"}},
            "required": ["ref"],
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {"skill": {"type": "object"}},
            "additionalProperties": True,
        },
    },
    {
        "name": "skills.resolve",
        "description": "Render skills into a prompt chunk (ref/summary/full/adaptive).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "refs": {"type": "array", "items": {"type": "string"}},
                "names": {"type": "array", "items": {"type": "string"}},
                "tags": {"type": "array", "items": {"type": "string"}},
                "limit": {"type": "integer", "minimum": 1},
                "deduplicate_by_name": {"type": "boolean"},
                "config": {"type": "object"},
            },
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "section": {"type": "string"},
                "count": {"type": "integer"},
            },
            "additionalProperties": True,
        },
    },
    {
        "name": "skills.execute",
        "description": "Execute a skill by ref with optional retries/timeouts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ref": {"type": "string"},
                "inputs": {"type": "object"},
                "dry_run": {"type": "boolean"},
                "run_config": {"type": "object"},
                "trace": {"type": "object"},
            },
            "required": ["ref"],
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "skill_ref": {"type": "string"},
                "skill_type": {"type": "string"},
                "status": {"type": "string"},
                "output": {},
                "error": {},
                "metadata": {"type": "object"},
                "attempt": {"type": "integer"},
                "max_attempts": {"type": "integer"},
                "duration_ms": {"type": "integer"},
                "trace_id": {},
            },
            "additionalProperties": True,
        },
    },
    {
        "name": "memory.tx_begin",
        "description": "Begin a transactional memory write.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "actor": {"type": "string"},
                "reason": {"type": "string"},
                "metadata": {"type": "object"},
                "lineage": {"type": "object"},
                "idempotency_key": {"type": "string"},
            },
            "required": ["actor", "reason"],
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {"tx_id": {"type": "string"}},
            "additionalProperties": True,
        },
    },
    {
        "name": "memory.tx_stage",
        "description": "Stage memory entries inside a transaction.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tx_id": {"type": "string"},
                "entry": {"type": "object"},
                "entries": {"type": "array", "items": {"type": "object"}},
            },
            "required": ["tx_id"],
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "tx_id": {"type": "string"},
                "staged": {"type": "integer"},
            },
            "additionalProperties": True,
        },
    },
    {
        "name": "memory.tx_validate",
        "description": "Validate a transaction with confidence and evidence.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tx_id": {"type": "string"},
                "status": {"type": "string"},
                "confidence": {"type": "number"},
                "evidence": {"type": "string"},
                "validator": {"type": "string"},
                "metadata": {"type": "object"},
                "idempotency_key": {"type": "string"},
            },
            "required": ["tx_id", "status", "confidence", "evidence", "validator"],
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "tx_id": {"type": "string"},
                "status": {"type": "string"},
            },
            "additionalProperties": True,
        },
    },
    {
        "name": "memory.tx_commit",
        "description": "Commit a transaction (optionally superseding prior entries).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tx_id": {"type": "string"},
                "supersede": {"type": "boolean"},
                "validation": {"type": "object"},
            },
            "required": ["tx_id"],
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "tx_id": {"type": "string"},
                "status": {"type": "string"},
                "supersede": {"type": "boolean"},
            },
            "additionalProperties": True,
        },
    },
    {
        "name": "memory.tx_rollback",
        "description": "Rollback a transaction.",
        "inputSchema": {
            "type": "object",
            "properties": {"tx_id": {"type": "string"}, "reason": {"type": "string"}},
            "required": ["tx_id", "reason"],
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "tx_id": {"type": "string"},
                "status": {"type": "string"},
            },
            "additionalProperties": True,
        },
    },
    {
        "name": "memory.list",
        "description": "List committed memory entries.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {"type": "string"},
                "entry_type": {"type": "string"},
                "source": {"type": "string"},
                "created_after": {"type": "string"},
                "created_before": {"type": "string"},
                "min_confidence": {"type": "number"},
                "max_confidence": {"type": "number"},
                "limit": {"type": "integer", "minimum": 1},
            },
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {"entries": {"type": "array", "items": {"type": "object"}}},
            "additionalProperties": True,
        },
    },
    {
        "name": "memory.list_staged",
        "description": "List staged memory entries for a transaction.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tx_id": {"type": "string"},
                "key": {"type": "string"},
                "entry_type": {"type": "string"},
                "source": {"type": "string"},
                "min_confidence": {"type": "number"},
                "max_confidence": {"type": "number"},
                "limit": {"type": "integer", "minimum": 1},
            },
            "required": ["tx_id"],
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {"entries": {"type": "array", "items": {"type": "object"}}},
            "additionalProperties": True,
        },
    },
    {
        "name": "trace.log",
        "description": "Record a decision trace.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "decision": {"type": "string"},
                "skill_ref": {"type": "string"},
                "reason": {"type": "string"},
                "confidence": {"type": "number"},
                "result": {"type": "string"},
                "metadata": {"type": "object"},
                "lineage": {"type": "object"},
                "tx_id": {"type": "string"},
                "idempotency_key": {"type": "string"},
                "correlation_id": {"type": "string"},
            },
            "required": ["decision", "reason", "confidence", "result"],
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {"trace_id": {"type": "string"}},
            "additionalProperties": True,
        },
    },
    {
        "name": "trace.list",
        "description": "List decision traces.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "minimum": 1},
                "tx_id": {"type": "string"},
                "decision": {"type": "string"},
                "skill_ref": {"type": "string"},
                "result": {"type": "string"},
                "created_after": {"type": "string"},
                "created_before": {"type": "string"},
                "correlation_id": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {"traces": {"type": "array", "items": {"type": "object"}}},
            "additionalProperties": True,
        },
    },
]

_RESOURCE_DEFINITIONS: list[dict] = [
    {
        "uri": "baguette://skills",
        "name": "Skills Snapshot",
        "description": "Snapshot of skill artifacts (query params: names,tags,refs,limit,include_spec).",
        "mimeType": "application/json",
    },
    {
        "uri": "baguette://memory",
        "name": "Memory Snapshot",
        "description": "Snapshot of committed memory entries (query params: key,entry_type,source,limit,...).",
        "mimeType": "application/json",
    },
    {
        "uri": "baguette://traces",
        "name": "Trace Snapshot",
        "description": "Snapshot of decision traces (query params: decision,skill_ref,result,limit,...).",
        "mimeType": "application/json",
    },
]

_RESOURCE_TEMPLATE_DEFINITIONS: list[dict] = [
    {
        "uriTemplate": "baguette://skills{?names,tags,refs,limit,include_spec}",
        "name": "Skills Snapshot",
        "description": "Snapshot of skill artifacts (query params: names,tags,refs,limit,include_spec).",
        "mimeType": "application/json",
    },
    {
        "uriTemplate": "baguette://skills/{ref}",
        "name": "Skill Artifact",
        "description": "Single skill artifact by ref (name@version or name@tag).",
        "mimeType": "application/json",
    },
    {
        "uriTemplate": "baguette://memory{?key,entry_type,source,limit,created_after,created_before,min_confidence,max_confidence}",
        "name": "Memory Snapshot",
        "description": "Snapshot of committed memory entries (query params: key,entry_type,source,...).",
        "mimeType": "application/json",
    },
    {
        "uriTemplate": "baguette://traces{?decision,skill_ref,result,limit,created_after,created_before,tx_id,correlation_id}",
        "name": "Trace Snapshot",
        "description": "Snapshot of decision traces (query params: decision,skill_ref,result,...).",
        "mimeType": "application/json",
    },
]


class MCPError(RuntimeError):
    def __init__(self, code: int, message: str, *, data: Optional[dict] = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


class MCPServer:
    def __init__(self, storage: StorageBackend, *, initialize: bool = False) -> None:
        self.storage = storage
        if initialize:
            self.storage.initialize()
        self._initialized = False
        self._client_initialized = False
        self._protocol_version: Optional[str] = None
        self._resource_subscriptions: set[str] = set()
        self._notify: Optional[Callable[[dict], None]] = None
        self._log_level = "info"
        self._skills_count: Optional[int] = None
        self._tool_handlers: Dict[str, Callable[[dict], dict]] = {
            "skills.list": self._tool_skills_list,
            "skills.get": self._tool_skills_get,
            "skills.resolve": self._tool_skills_resolve,
            "skills.execute": self._tool_skills_execute,
            "memory.tx_begin": self._tool_memory_tx_begin,
            "memory.tx_stage": self._tool_memory_tx_stage,
            "memory.tx_validate": self._tool_memory_tx_validate,
            "memory.tx_commit": self._tool_memory_tx_commit,
            "memory.tx_rollback": self._tool_memory_tx_rollback,
            "memory.list": self._tool_memory_list,
            "memory.list_staged": self._tool_memory_list_staged,
            "trace.log": self._tool_trace_log,
            "trace.list": self._tool_trace_list,
        }
        self._log = logging.getLogger(__name__)

    def set_notifier(self, notifier: Optional[Callable[[dict], None]]) -> None:
        self._notify = notifier

    def handle_request(self, request: dict) -> Optional[dict]:
        if not isinstance(request, dict):
            raise MCPError(JSONRPC_INVALID_REQUEST, "Request must be an object.")

        method = request.get("method")
        req_id = request.get("id")
        params = request.get("params") or {}

        if not method:
            raise MCPError(JSONRPC_INVALID_REQUEST, "Request method is required.")

        if isinstance(method, str) and method.startswith("notifications/"):
            self._handle_notification(method, params)
            return None

        if method == "initialize":
            if self._initialized:
                raise MCPError(JSONRPC_INVALID_REQUEST, "Server already initialized.")
            result = self._handle_initialize(params)
            self._initialized = True
        else:
            if not self._initialized:
                raise MCPError(JSONRPC_INVALID_REQUEST, "Server not initialized. Call initialize.")
            if not self._client_initialized:
                raise MCPError(
                    JSONRPC_INVALID_REQUEST,
                    "Client not initialized. Send notifications/initialized.",
                )

            if method == "tools/list":
                result = self._handle_tools_list(params)
            elif method == "tools/call":
                result = self._handle_tools_call(params)
            elif method == "resources/list":
                result = self._handle_resources_list(params)
            elif method == "resources/read":
                result = self._handle_resources_read(params)
            elif method == "resources/templates/list":
                result = self._handle_resources_templates_list(params)
            elif method == "resources/subscribe":
                result = self._handle_resources_subscribe(params)
            elif method == "resources/unsubscribe":
                result = self._handle_resources_unsubscribe(params)
            elif method == "prompts/list":
                result = self._handle_prompts_list(params)
            elif method == "prompts/get":
                result = self._handle_prompts_get(params)
            elif method == "logging/setLevel":
                result = self._handle_logging_set_level(params)
            elif method == "completion/complete":
                result = self._handle_completion_complete(params)
            else:
                raise MCPError(JSONRPC_METHOD_NOT_FOUND, f"Unknown method: {method}")

        if req_id is None:
            return None
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    def _handle_initialize(self, params: Any) -> dict:
        payload = params if isinstance(params, dict) else {}
        raw_version = payload.get("protocolVersion")
        if not isinstance(raw_version, str) or not raw_version.strip():
            raise MCPError(JSONRPC_INVALID_PARAMS, "initialize params must include protocolVersion.")
        requested = raw_version.strip()
        if requested in SUPPORTED_PROTOCOL_VERSIONS:
            selected = requested
        else:
            selected = DEFAULT_PROTOCOL_VERSION
        self._protocol_version = selected
        return {
            "protocolVersion": selected,
            "capabilities": self._server_capabilities(),
            "serverInfo": {"name": "baguette", "version": __version__},
        }

    def _server_capabilities(self) -> dict:
        return {
            "tools": {"listChanged": False},
            "resources": {"subscribe": True, "listChanged": True},
            "prompts": {"listChanged": False},
            "logging": {},
            "completions": {},
        }

    def _handle_notification(self, method: str, params: Any) -> None:
        if method == "notifications/initialized":
            self._client_initialized = True

    def _notify_message(self, level: str, message: str, *, data: Optional[dict] = None) -> None:
        if self._notify is None:
            return
        if _LOG_LEVELS.get(level, 0) < _LOG_LEVELS.get(self._log_level, 0):
            return
        payload: dict = {"level": level, "message": message}
        if data:
            payload["data"] = data
        self._notify({"jsonrpc": "2.0", "method": "notifications/message", "params": payload})

    def _notify_resource_updated(self, base: str) -> None:
        if self._notify is None or not self._resource_subscriptions:
            return
        for uri in list(self._resource_subscriptions):
            try:
                resource_base, _path, _query = _parse_resource_uri(uri)
            except ValueError:
                continue
            if resource_base != base:
                continue
            self._notify(
                {
                    "jsonrpc": "2.0",
                    "method": "notifications/resources/updated",
                    "params": {"uri": uri},
                }
            )

    def _notify_resources_list_changed(self) -> None:
        if self._notify is None or not self._resource_subscriptions:
            return
        self._notify(
            {
                "jsonrpc": "2.0",
                "method": "notifications/resources/list_changed",
            }
        )

    def _check_skills_list_changed(self) -> None:
        try:
            skills = list(self.storage.list_skills())
        except Exception:
            return
        count = len(skills)
        if self._skills_count is None:
            self._skills_count = count
            return
        if count != self._skills_count:
            self._skills_count = count
            self._notify_resources_list_changed()

    def _handle_logging_set_level(self, params: Any) -> dict:
        if not isinstance(params, dict):
            raise MCPError(JSONRPC_INVALID_PARAMS, "logging/setLevel params must be an object.")
        level = params.get("level")
        if not isinstance(level, str) or level.strip().lower() not in _LOG_LEVELS:
            raise MCPError(JSONRPC_INVALID_PARAMS, "logging/setLevel requires a valid level.")
        self._log_level = level.strip().lower()
        return {}

    def _handle_completion_complete(self, params: Any) -> dict:
        if not isinstance(params, dict):
            raise MCPError(JSONRPC_INVALID_PARAMS, "completion/complete params must be an object.")
        ref = params.get("ref")
        argument = params.get("argument") or {}
        limit = params.get("limit")
        if not isinstance(ref, dict):
            raise MCPError(JSONRPC_INVALID_PARAMS, "completion/complete ref must be an object.")
        if not isinstance(argument, dict):
            raise MCPError(JSONRPC_INVALID_PARAMS, "completion/complete argument must be an object.")
        ref_type = ref.get("type")
        ref_name = ref.get("name")
        arg_name = argument.get("name")
        arg_value = argument.get("value") or ""
        max_results = _coerce_int(limit, default=100)
        if max_results <= 0:
            max_results = 0

        values: list[str] = []
        if ref_type == "ref/prompt":
            if isinstance(arg_name, str) and arg_name == "name":
                values = self._prompt_name_completions(str(arg_value), limit=max_results)
            elif isinstance(ref_name, str) and isinstance(arg_name, str):
                values = self._prompt_argument_completions(
                    ref_name, arg_name, str(arg_value), limit=max_results
                )
        elif ref_type == "ref/tool":
            if isinstance(arg_name, str) and arg_name == "name":
                values = self._tool_name_completions(str(arg_value), limit=max_results)
        elif ref_type == "ref/skill":
            if isinstance(arg_name, str) and arg_name in {"ref", "name"}:
                values = self._skill_ref_completions(str(arg_value), limit=max_results)
        elif ref_type == "ref/resource" and isinstance(arg_name, str):
            if arg_name == "uri":
                values = self._resource_uri_completions(str(arg_value), limit=max_results)

        return {"completion": {"values": values, "total": len(values), "hasMore": False}}

    def _prompt_name_completions(self, prefix: str, *, limit: int = 100) -> list[str]:
        skills = [skill for skill in self.storage.list_skills() if skill.type == "prompt"]
        skills = _dedupe_latest(skills)
        candidates = [skill.name for skill in skills]
        return self._filter_candidates(candidates, prefix, limit=limit)

    def _tool_name_completions(self, prefix: str, *, limit: int = 100) -> list[str]:
        candidates = [tool["name"] for tool in _TOOL_DEFINITIONS]
        return self._filter_candidates(candidates, prefix, limit=limit)

    def _skill_ref_completions(self, prefix: str, *, limit: int = 100) -> list[str]:
        skills = list(self.storage.list_skills())
        if "@" not in prefix:
            skills = _dedupe_latest(skills)
        refs: list[str] = []
        for skill in skills:
            refs.append(skill.ref())
            tags = skill.spec.get("tags")
            if isinstance(tags, list):
                for tag in tags:
                    if isinstance(tag, str) and tag.strip():
                        refs.append(f"{skill.name}@{tag.strip()}")
            refs.append(f"{skill.name}@latest")
        return self._filter_candidates(refs, prefix, limit=limit)

    def _prompt_argument_completions(
        self, prompt_name: str, argument_name: str, prefix: str, *, limit: int = 100
    ) -> list[str]:
        skill = self._get_prompt_skill(prompt_name)
        inputs = skill.spec.get("inputs")
        if not isinstance(inputs, dict):
            return []
        raw = None
        if _looks_like_schema(inputs):
            properties = inputs.get("properties") if isinstance(inputs.get("properties"), dict) else {}
            raw = properties.get(argument_name)
        else:
            raw = inputs.get(argument_name)
        if not isinstance(raw, dict):
            return []
        candidates = self._schema_candidates(raw)
        if not candidates:
            candidates = self._schema_hints(raw)
        return self._filter_candidates(candidates, prefix, limit=limit)

    def _resource_uri_completions(self, prefix: str, *, limit: int = 100) -> list[str]:
        candidates = [resource["uri"] for resource in _RESOURCE_DEFINITIONS]
        candidates.extend(
            [
                "baguette://skills?tags=stable&limit=10",
                "baguette://skills?limit=10",
                "baguette://memory?limit=50",
                "baguette://traces?limit=50",
            ]
        )
        return self._filter_candidates(candidates, prefix, limit=limit)

    def _filter_candidates(self, candidates: list[str], prefix: str, *, limit: int = 100) -> list[str]:
        if not candidates:
            return []
        unique = []
        seen = set()
        for item in candidates:
            if item in seen:
                continue
            seen.add(item)
            unique.append(item)
        if not prefix:
            return unique[: max(0, limit)]
        lowered = prefix.lower()
        return [value for value in unique if value.lower().startswith(lowered)][: max(0, limit)]

    def _schema_candidates(self, schema: dict) -> list[str]:
        candidates: list[str] = []
        if "const" in schema:
            candidates.append(str(schema["const"]))
        if isinstance(schema.get("enum"), list):
            candidates.extend(str(item) for item in schema.get("enum", []))
        if isinstance(schema.get("examples"), list):
            candidates.extend(str(item) for item in schema.get("examples", []))
        if "default" in schema:
            candidates.append(str(schema["default"]))
        for key in ("oneOf", "anyOf", "allOf"):
            options = schema.get(key)
            if isinstance(options, list):
                for option in options:
                    if isinstance(option, dict):
                        candidates.extend(self._schema_candidates(option))
        return candidates

    def _schema_hints(self, schema: dict) -> list[str]:
        format_hint = schema.get("format")
        if isinstance(format_hint, str):
            hints = {
                "date": "YYYY-MM-DD",
                "date-time": "YYYY-MM-DDTHH:MM:SSZ",
                "time": "HH:MM:SS",
                "email": "user@example.com",
                "uri": "https://example.com",
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "ipv4": "192.0.2.1",
                "ipv6": "2001:db8::1",
                "hostname": "example.com",
            }
            if format_hint in hints:
                return [hints[format_hint]]
            return [f"<{format_hint}>"]
        pattern_hint = schema.get("pattern")
        if isinstance(pattern_hint, str) and pattern_hint.strip():
            return [f"<pattern:{pattern_hint}>"]
        return []

    def _handle_tools_list(self, params: Any) -> dict:
        payload = params if isinstance(params, dict) else {}
        tools = list(_TOOL_DEFINITIONS)
        try:
            page, next_cursor = _paginate(
                tools,
                cursor=payload.get("cursor"),
                limit=payload.get("limit"),
            )
        except ValueError as exc:
            raise MCPError(JSONRPC_INVALID_PARAMS, str(exc)) from exc
        result: dict = {"tools": page}
        if next_cursor is not None:
            result["nextCursor"] = next_cursor
        return result

    def _handle_resources_list(self, params: Any) -> dict:
        payload = params if isinstance(params, dict) else {}
        resources = list(_RESOURCE_DEFINITIONS)
        try:
            page, next_cursor = _paginate(
                resources,
                cursor=payload.get("cursor"),
                limit=payload.get("limit"),
            )
        except ValueError as exc:
            raise MCPError(JSONRPC_INVALID_PARAMS, str(exc)) from exc
        result: dict = {"resources": page}
        if next_cursor is not None:
            result["nextCursor"] = next_cursor
        return result

    def _handle_resources_templates_list(self, params: Any) -> dict:
        payload = params if isinstance(params, dict) else {}
        templates = list(_RESOURCE_TEMPLATE_DEFINITIONS)
        try:
            page, next_cursor = _paginate(
                templates,
                cursor=payload.get("cursor"),
                limit=payload.get("limit"),
            )
        except ValueError as exc:
            raise MCPError(JSONRPC_INVALID_PARAMS, str(exc)) from exc
        result: dict = {"resourceTemplates": page}
        if next_cursor is not None:
            result["nextCursor"] = next_cursor
        return result

    def _handle_resources_subscribe(self, params: Any) -> dict:
        if not isinstance(params, dict):
            raise MCPError(JSONRPC_INVALID_PARAMS, "resources/subscribe params must be an object.")
        uri = params.get("uri")
        if not isinstance(uri, str) or not uri.strip():
            raise MCPError(JSONRPC_INVALID_PARAMS, "resources/subscribe uri must be provided.")
        self._validate_resource_uri(uri.strip())
        self._resource_subscriptions.add(uri.strip())
        return {}

    def _handle_resources_unsubscribe(self, params: Any) -> dict:
        if not isinstance(params, dict):
            raise MCPError(JSONRPC_INVALID_PARAMS, "resources/unsubscribe params must be an object.")
        uri = params.get("uri")
        if not isinstance(uri, str) or not uri.strip():
            raise MCPError(JSONRPC_INVALID_PARAMS, "resources/unsubscribe uri must be provided.")
        self._resource_subscriptions.discard(uri.strip())
        return {}

    def _handle_prompts_list(self, params: Any) -> dict:
        payload = params if isinstance(params, dict) else {}
        skills = [skill for skill in self.storage.list_skills() if skill.type == "prompt"]
        skills = _dedupe_latest(skills)
        skills.sort(key=lambda skill: skill.updated_at, reverse=True)
        prompts = [_prompt_summary(skill) for skill in skills]
        try:
            page, next_cursor = _paginate(
                prompts,
                cursor=payload.get("cursor"),
                limit=payload.get("limit"),
            )
        except ValueError as exc:
            raise MCPError(JSONRPC_INVALID_PARAMS, str(exc)) from exc
        result: dict = {"prompts": page}
        if next_cursor is not None:
            result["nextCursor"] = next_cursor
        return result

    def _handle_prompts_get(self, params: Any) -> dict:
        if not isinstance(params, dict):
            raise MCPError(JSONRPC_INVALID_PARAMS, "prompts/get params must be an object.")
        name = params.get("name")
        if not isinstance(name, str) or not name.strip():
            raise MCPError(JSONRPC_INVALID_PARAMS, "prompts/get name must be provided.")
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            raise MCPError(JSONRPC_INVALID_PARAMS, "prompts/get arguments must be an object.")
        skill = self._get_prompt_skill(name.strip())
        try:
            rendered = run_skill(skill, arguments).run.output
        except (ExecutionError, ValueError) as exc:
            raise MCPError(JSONRPC_INVALID_PARAMS, str(exc)) from exc
        return {
            "description": skill.spec.get("description"),
            "messages": [{"role": "user", "content": rendered or ""}],
        }

    def _handle_tools_call(self, params: Any) -> dict:
        if not isinstance(params, dict):
            raise MCPError(JSONRPC_INVALID_PARAMS, "tools/call params must be an object.")
        name = params.get("name")
        if not isinstance(name, str) or not name.strip():
            raise MCPError(JSONRPC_INVALID_PARAMS, "tools/call name must be provided.")
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            raise MCPError(JSONRPC_INVALID_PARAMS, "tools/call arguments must be an object.")
        handler = self._tool_handlers.get(name)
        if handler is None:
            raise MCPError(JSONRPC_METHOD_NOT_FOUND, f"Unknown tool: {name}")
        try:
            return _tool_text(handler(arguments))
        except (ExecutionError, ValueError, KeyError) as exc:
            self._log.info("MCP tool error: %s", exc)
            return _tool_error(str(exc))

    def _handle_resources_read(self, params: Any) -> dict:
        if not isinstance(params, dict):
            raise MCPError(JSONRPC_INVALID_PARAMS, "resources/read params must be an object.")
        uri = params.get("uri")
        if not isinstance(uri, str) or not uri.strip():
            raise MCPError(JSONRPC_INVALID_PARAMS, "resources/read uri must be provided.")
        try:
            resource = self._read_resource(uri.strip())
        except MCPError:
            raise
        except ValueError as exc:
            raise MCPError(JSONRPC_INVALID_PARAMS, str(exc)) from exc
        return {"contents": [resource]}

    def _tool_skills_list(self, params: dict) -> dict:
        include_spec = _coerce_bool(params.get("include_spec")) is True
        skills = _query_skills(self.storage, params)
        self._check_skills_list_changed()
        return {"skills": [_skill_summary(skill, include_spec=include_spec) for skill in skills]}

    def _tool_skills_get(self, params: dict) -> dict:
        ref = params.get("ref")
        if not isinstance(ref, str) or not ref.strip():
            raise ValueError("ref must be a non-empty string.")
        include_spec = _coerce_bool(params.get("include_spec"))
        name, version = _parse_skill_ref(ref)
        skill = self.storage.get_skill(name, version)
        payload = _skill_summary(skill, include_spec=include_spec is not False)
        return {"skill": payload}

    def _tool_skills_resolve(self, params: dict) -> dict:
        config = _dataclass_from_dict(SkillResolutionConfig, _ensure_dict(params.get("config")))
        entries = _query_skills(self.storage, params)
        section = resolve_skills(entries, config)
        return {"section": section, "count": len(entries)}

    def _tool_skills_execute(self, params: dict) -> dict:
        ref = params.get("ref")
        if not isinstance(ref, str) or not ref.strip():
            raise ValueError("ref must be a non-empty string.")
        name, version = _parse_skill_ref(ref)
        skill = self.storage.get_skill(name, version)
        inputs = _ensure_dict(params.get("inputs"))
        dry_run = _coerce_bool(params.get("dry_run")) is True
        run_config = _parse_run_config(params.get("run_config"))

        skill_run = run_skill(skill, inputs, dry_run, run_config)
        run_result = skill_run.run
        trace_config = _parse_trace_config(params.get("trace"))
        trace_meta = build_skill_trace_metadata(
            tool_name=None,
            skill_ref=skill.ref(),
            inputs=inputs,
            run_result=run_result,
            duration_ms=skill_run.duration_ms,
            attempt=skill_run.attempt,
            max_attempts=skill_run.max_attempts,
            idempotency_key=skill_run.idempotency_key,
            config=trace_config,
        )

        trace_params = params.get("trace") if isinstance(params.get("trace"), dict) else {}
        trace_id = None
        if _coerce_bool(trace_params.get("log")) is True:
            metadata = dict(trace_meta)
            extra_metadata = trace_params.get("metadata")
            if isinstance(extra_metadata, dict):
                metadata.update(extra_metadata)
            lineage = trace_params.get("lineage")
            if not isinstance(lineage, dict):
                lineage = {}
            correlation_id = trace_params.get("correlation_id")
            if correlation_id:
                metadata.setdefault("correlation_id", correlation_id)
                lineage.setdefault("correlation_id", correlation_id)
            trace = DecisionTrace.new(
                decision=str(trace_params.get("decision") or "execute_skill"),
                skill_ref=skill.ref(),
                reason=str(trace_params.get("reason") or "mcp.execute_skill"),
                confidence=_coerce_float(trace_params.get("confidence"), default=1.0),
                result=run_result.status,
                metadata=metadata,
                tx_id=trace_params.get("tx_id"),
                lineage=lineage,
                idempotency_key=trace_params.get("idempotency_key"),
            )
            self.storage.record_trace(trace)
            trace_id = trace.trace_id
            self._notify_resource_updated("traces")

        return {
            "skill_ref": skill.ref(),
            "skill_type": skill.type,
            "status": run_result.status,
            "output": run_result.output,
            "error": run_result.error,
            "metadata": trace_meta,
            "attempt": skill_run.attempt,
            "max_attempts": skill_run.max_attempts,
            "duration_ms": skill_run.duration_ms,
            "trace_id": trace_id,
        }

    def _tool_memory_tx_begin(self, params: dict) -> dict:
        actor = params.get("actor")
        reason = params.get("reason")
        if not isinstance(actor, str) or not actor.strip():
            raise ValueError("actor must be a non-empty string.")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("reason must be a non-empty string.")
        tx_id = self.storage.begin_transaction(
            actor=actor,
            reason=reason,
            metadata=_ensure_dict(params.get("metadata")),
            idempotency_key=params.get("idempotency_key"),
            lineage=_ensure_dict(params.get("lineage")),
        )
        return {"tx_id": tx_id}

    def _build_entry(self, raw: dict, tx_id: str) -> MemoryEntry:
        key = raw.get("key")
        entry_type = raw.get("type") or raw.get("entry_type")
        source = raw.get("source")
        confidence = _coerce_float(raw.get("confidence"), default=0.0)
        entry = MemoryEntry.new(
            key=key,
            value=raw.get("value"),
            type=entry_type,
            source=source,
            confidence=confidence,
            metadata=_ensure_dict(raw.get("metadata")),
            lineage=_ensure_dict(raw.get("lineage")),
            idempotency_key=raw.get("idempotency_key"),
        )
        return entry.scope_to_tx(tx_id)

    def _tool_memory_tx_stage(self, params: dict) -> dict:
        tx_id = params.get("tx_id")
        if not isinstance(tx_id, str) or not tx_id.strip():
            raise ValueError("tx_id must be a non-empty string.")
        entries_raw = params.get("entries")
        if entries_raw is None:
            entry_raw = params.get("entry")
            if entry_raw is None:
                raise ValueError("entry or entries must be provided.")
            entries_raw = [entry_raw]
        if not isinstance(entries_raw, list):
            raise ValueError("entries must be a list of objects.")
        staged = 0
        for raw in entries_raw:
            if not isinstance(raw, dict):
                raise ValueError("entry must be an object.")
            entry = self._build_entry(raw, tx_id)
            self.storage.stage_memory(tx_id, entry)
            staged += 1
        return {"tx_id": tx_id, "staged": staged}

    def _tool_memory_tx_validate(self, params: dict) -> dict:
        tx_id = params.get("tx_id")
        if not isinstance(tx_id, str) or not tx_id.strip():
            raise ValueError("tx_id must be a non-empty string.")
        validation = ValidationRecord(
            status=str(params.get("status") or ""),
            confidence=_coerce_float(params.get("confidence"), default=0.0),
            evidence=str(params.get("evidence") or ""),
            validator=str(params.get("validator") or ""),
            metadata=_ensure_dict(params.get("metadata")),
            idempotency_key=params.get("idempotency_key"),
        )
        self.storage.validate_transaction(tx_id, validation)
        return {"tx_id": tx_id, "status": validation.status}

    def _tool_memory_tx_commit(self, params: dict) -> dict:
        tx_id = params.get("tx_id")
        if not isinstance(tx_id, str) or not tx_id.strip():
            raise ValueError("tx_id must be a non-empty string.")
        supersede = _coerce_bool(params.get("supersede")) is True
        validation_payload = params.get("validation")
        validation = None
        if isinstance(validation_payload, dict):
            validation = ValidationRecord(
                status=str(validation_payload.get("status") or ""),
                confidence=_coerce_float(validation_payload.get("confidence"), default=0.0),
                evidence=str(validation_payload.get("evidence") or ""),
                validator=str(validation_payload.get("validator") or ""),
                metadata=_ensure_dict(validation_payload.get("metadata")),
                idempotency_key=validation_payload.get("idempotency_key"),
            )
        self.storage.commit_transaction(tx_id, validation, supersede=supersede)
        self._notify_resource_updated("memory")
        return {"tx_id": tx_id, "status": "committed", "supersede": supersede}

    def _tool_memory_tx_rollback(self, params: dict) -> dict:
        tx_id = params.get("tx_id")
        reason = params.get("reason")
        if not isinstance(tx_id, str) or not tx_id.strip():
            raise ValueError("tx_id must be a non-empty string.")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("reason must be a non-empty string.")
        self.storage.rollback_transaction(tx_id, reason)
        return {"tx_id": tx_id, "status": "rolled_back"}

    def _tool_memory_list(self, params: dict) -> dict:
        limit = params.get("limit", 100)
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 100
        entries = [
            entry.to_dict()
            for entry in self.storage.list_memory(
                key=params.get("key"),
                entry_type=params.get("entry_type"),
                source=params.get("source"),
                created_after=params.get("created_after"),
                created_before=params.get("created_before"),
                min_confidence=params.get("min_confidence"),
                max_confidence=params.get("max_confidence"),
                limit=limit,
            )
        ]
        return {"entries": entries}

    def _tool_memory_list_staged(self, params: dict) -> dict:
        tx_id = params.get("tx_id")
        if not isinstance(tx_id, str) or not tx_id.strip():
            raise ValueError("tx_id must be a non-empty string.")
        limit = params.get("limit", 100)
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 100
        entries = [
            entry.to_dict()
            for entry in self.storage.list_staged_memory(
                tx_id=tx_id,
                key=params.get("key"),
                entry_type=params.get("entry_type"),
                source=params.get("source"),
                min_confidence=params.get("min_confidence"),
                max_confidence=params.get("max_confidence"),
                limit=limit,
            )
        ]
        return {"entries": entries}

    def _tool_trace_log(self, params: dict) -> dict:
        metadata = _ensure_dict(params.get("metadata"))
        lineage = _ensure_dict(params.get("lineage"))
        correlation_id = params.get("correlation_id")
        if correlation_id:
            metadata.setdefault("correlation_id", correlation_id)
            lineage.setdefault("correlation_id", correlation_id)
        trace = DecisionTrace.new(
            decision=str(params.get("decision") or ""),
            skill_ref=params.get("skill_ref"),
            reason=str(params.get("reason") or ""),
            confidence=_coerce_float(params.get("confidence"), default=0.0),
            result=str(params.get("result") or ""),
            metadata=metadata,
            tx_id=params.get("tx_id"),
            lineage=lineage,
            idempotency_key=params.get("idempotency_key"),
        )
        self.storage.record_trace(trace)
        self._notify_resource_updated("traces")
        return {"trace_id": trace.trace_id}

    def _tool_trace_list(self, params: dict) -> dict:
        limit = params.get("limit", 100)
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 100
        traces = [
            trace.to_dict()
            for trace in self.storage.list_traces(
                limit=limit,
                tx_id=params.get("tx_id"),
                decision=params.get("decision"),
                skill_ref=params.get("skill_ref"),
                result=params.get("result"),
                created_after=params.get("created_after"),
                created_before=params.get("created_before"),
                correlation_id=params.get("correlation_id"),
            )
        ]
        return {"traces": traces}

    def _get_prompt_skill(self, name: str) -> SkillArtifact:
        skill_name, version = _parse_skill_ref(name)
        try:
            skill = self.storage.get_skill(skill_name, version)
        except KeyError as exc:
            raise MCPError(
                JSONRPC_RESOURCE_NOT_FOUND,
                f"Prompt not found: {name}",
                data={"name": name},
            ) from exc
        if skill.type != "prompt":
            raise MCPError(
                JSONRPC_RESOURCE_NOT_FOUND,
                f"Prompt not found: {name}",
                data={"name": name},
            )
        return skill

    def _validate_resource_uri(self, uri: str) -> None:
        try:
            base, path, _query = _parse_resource_uri(uri)
        except ValueError as exc:
            raise MCPError(JSONRPC_INVALID_PARAMS, str(exc)) from exc
        if base not in {"skills", "memory", "traces"}:
            raise MCPError(
                JSONRPC_RESOURCE_NOT_FOUND,
                f"Unknown resource: {base}",
                data={"uri": uri},
            )
        if base == "skills" and path:
            name, version = _parse_skill_ref(path)
            try:
                self.storage.get_skill(name, version)
            except KeyError as exc:
                raise MCPError(
                    JSONRPC_RESOURCE_NOT_FOUND,
                    f"Skill not found: {path}",
                    data={"uri": uri},
                ) from exc

    def _read_resource(self, uri: str) -> dict:
        base, path, query = _parse_resource_uri(uri)
        if base == "skills":
            payload = self._read_skills_resource(path, query)
        elif base == "memory":
            payload = self._read_memory_resource(query)
        elif base == "traces":
            payload = self._read_traces_resource(query)
        else:
            raise MCPError(
                JSONRPC_RESOURCE_NOT_FOUND,
                f"Unknown resource: {base}",
                data={"uri": uri},
            )
        return {
            "uri": uri,
            "mimeType": "application/json",
            "text": json.dumps(payload, ensure_ascii=False),
        }

    def _read_skills_resource(self, path: Optional[str], query: dict) -> dict:
        include_spec = _coerce_bool(query.get("include_spec")) is True
        if path:
            name, version = _parse_skill_ref(path)
            try:
                skill = self.storage.get_skill(name, version)
            except KeyError as exc:
                raise MCPError(
                    JSONRPC_RESOURCE_NOT_FOUND,
                    f"Skill not found: {path}",
                    data={"uri": f"baguette://skills/{path}"},
                ) from exc
            return {"skill": _skill_summary(skill, include_spec=True)}
        params = dict(query)
        skills = _query_skills(self.storage, params)
        self._check_skills_list_changed()
        return {"skills": [_skill_summary(skill, include_spec=include_spec) for skill in skills]}

    def _read_memory_resource(self, query: dict) -> dict:
        limit = _coerce_int(query.get("limit"), default=100)
        entries = [
            entry.to_dict()
            for entry in self.storage.list_memory(
                key=query.get("key"),
                entry_type=query.get("entry_type"),
                source=query.get("source"),
                created_after=query.get("created_after"),
                created_before=query.get("created_before"),
                min_confidence=_coerce_optional_float(query.get("min_confidence")),
                max_confidence=_coerce_optional_float(query.get("max_confidence")),
                limit=limit,
            )
        ]
        return {"entries": entries}

    def _read_traces_resource(self, query: dict) -> dict:
        limit = _coerce_int(query.get("limit"), default=100)
        traces = [
            trace.to_dict()
            for trace in self.storage.list_traces(
                limit=limit,
                tx_id=query.get("tx_id"),
                decision=query.get("decision"),
                skill_ref=query.get("skill_ref"),
                result=query.get("result"),
                created_after=query.get("created_after"),
                created_before=query.get("created_before"),
                correlation_id=query.get("correlation_id"),
            )
        ]
        return {"traces": traces}


def _serve_stdio(server: MCPServer) -> int:
    for line in sys.stdin:
        raw = line.strip()
        if not raw:
            continue
        try:
            request = json.loads(raw)
        except json.JSONDecodeError as exc:
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": JSONRPC_PARSE_ERROR, "message": str(exc)},
            }
            print(json.dumps(response, ensure_ascii=False), flush=True)
            continue

        try:
            response = server.handle_request(request)
        except MCPError as exc:
            error = {"code": exc.code, "message": exc.message}
            if exc.data is not None:
                error["data"] = exc.data
            response = {"jsonrpc": "2.0", "id": request.get("id"), "error": error}
        except Exception as exc:
            response = {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": JSONRPC_INTERNAL_ERROR, "message": str(exc)},
            }

        if response is None:
            continue
        print(json.dumps(response, ensure_ascii=False), flush=True)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="baguette-mcp", description="Baguette MCP server")
    parser.add_argument("--db", help="Path to SQLite DB")
    parser.add_argument(
        "--backend",
        help="Storage backend name (env: BAGUETTE_BACKEND, default: sqlite)",
    )
    parser.add_argument(
        "--backend-config",
        help="JSON object with backend-specific configuration",
    )
    parser.add_argument("--log-level", default="info", help="Logging level (stderr)")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(levelname)s %(message)s",
        stream=sys.stderr,
    )

    storage = build_storage(args)
    storage.initialize()

    server = MCPServer(storage)
    server.set_notifier(lambda payload: print(json.dumps(payload, ensure_ascii=False), flush=True))
    return _serve_stdio(server)


if __name__ == "__main__":
    raise SystemExit(main())

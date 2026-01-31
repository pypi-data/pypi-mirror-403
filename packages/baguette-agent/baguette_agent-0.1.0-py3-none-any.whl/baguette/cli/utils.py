from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Dict, Iterable, List, Tuple

from ..errors import ExecutionError


def parse_skill_ref(ref: str) -> Tuple[str, str]:
    if "@" in ref:
        name, version = ref.split("@", 1)
        return name, version
    return ref, "latest"


def parse_backend_config(raw: Any) -> Dict[str, Any]:
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            config = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON for --backend-config: {exc}") from exc
        if not isinstance(config, dict):
            raise ValueError("--backend-config must be a JSON object.")
        return config
    raise ValueError("--backend-config must be a JSON object.")


def parse_json_arg(raw: str | None, label: str, default: Any) -> Any:
    if raw is None:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON for {label}: {exc}") from exc


def parse_json_or_text(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def parse_iso_timestamp(raw: str | None, label: str) -> str | None:
    if raw is None:
        return None
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"Invalid ISO-8601 timestamp for {label}: {exc}") from exc
    return normalized


def format_table(headers: List[str], rows: Iterable[List[str]]) -> str:
    widths = [len(header) for header in headers]
    rows_list = list(rows)
    for row in rows_list:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))
    line = "  ".join(header.ljust(widths[idx]) for idx, header in enumerate(headers))
    sep = "  ".join("-" * widths[idx] for idx in range(len(headers)))
    body = ["  ".join(cell.ljust(widths[idx]) for idx, cell in enumerate(row)) for row in rows_list]
    return "\n".join([line, sep] + body)


def format_kv_table(payload: Dict[str, Any], order: List[str]) -> str:
    rows: List[List[str]] = []
    for key in order:
        value = payload.get(key)
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value, ensure_ascii=False)
        elif value is None:
            value_str = ""
        else:
            value_str = str(value)
        rows.append([key, value_str])
    return format_table(["FIELD", "VALUE"], rows)


def format_payload_preview(payload: Any, limit: int = 200) -> str:
    if isinstance(payload, (dict, list)):
        rendered = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    else:
        rendered = str(payload)
    if len(rendered) <= limit:
        return rendered
    return f"{rendered[:limit - 3]}..."


def sanitize_config_value(value: Any) -> Any:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    return value


def resolve_value_with_source(
    cli_value: Any,
    env_value: Any,
    config_value: Any,
    default_value: Any,
) -> Tuple[Any, str]:
    cli_value = sanitize_config_value(cli_value)
    env_value = sanitize_config_value(env_value)
    config_value = sanitize_config_value(config_value)

    if cli_value is not None:
        return cli_value, "cli"
    if env_value is not None:
        return env_value, "env"
    if config_value is not None:
        return config_value, "config"
    return default_value, "default"

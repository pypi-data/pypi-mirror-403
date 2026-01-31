from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import json
import os

import yaml


def get_config_path() -> Path:
    override = os.getenv("BAGUETTE_CONFIG", "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / ".baguette" / "baguette.yaml"


def load_config() -> Dict[str, Any]:
    path = get_config_path()
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = yaml.safe_load(raw)
    if isinstance(data, dict):
        return data
    return {}


def get_config_section(section: str) -> Dict[str, Any]:
    data = load_config()
    payload = data.get(section)
    if isinstance(payload, dict):
        return payload
    return {}

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import hashlib
import json
import uuid

import semver

def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_UUID_NAMESPACE = uuid.UUID("1a94cfb9-cc5a-4b26-9bf4-2f3a2b9fdb9f")


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    except TypeError as exc:
        raise ValueError("Value must be JSON serializable.") from exc


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def deterministic_uuid(namespace: str, value: str) -> str:
    scoped = uuid.uuid5(_UUID_NAMESPACE, namespace)
    return str(uuid.uuid5(scoped, value))


def derive_idempotency_key(*parts: str) -> str:
    return sha256_text("|".join(parts))


def is_semver(value: str) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip()
    if not normalized:
        return False
    try:
        semver.VersionInfo.parse(normalized)
    except ValueError:
        return False
    return True

from __future__ import annotations

from pathlib import Path
import os

from .utils import parse_backend_config
from ..config import get_config_section
from ..storage.base import StorageBackend
from ..storage.registry import create_backend


def default_db_path() -> Path:
    override = os.getenv("BAGUETTE_DB")
    if override:
        return Path(override)
    return Path.home() / ".baguette" / "baguette.db"


def resolve_backend_name(arg_value: str | None, config_value: str | None) -> str:
    return arg_value or os.getenv("BAGUETTE_BACKEND") or config_value or "sqlite"


def build_storage(args) -> StorageBackend:
    storage_config = get_config_section("storage")
    backend_name = resolve_backend_name(args.backend, storage_config.get("backend"))
    raw_backend_config = (
        args.backend_config
        or os.getenv("BAGUETTE_BACKEND_CONFIG")
        or storage_config.get("backend_config")
    )
    config = parse_backend_config(raw_backend_config)

    if backend_name == "sqlite":
        db_path = (
            Path(args.db).expanduser()
            if args.db
            else Path(os.getenv("BAGUETTE_DB")).expanduser()
            if os.getenv("BAGUETTE_DB")
            else Path(storage_config.get("db")).expanduser()
            if storage_config.get("db")
            else default_db_path()
        )
        config.setdefault("db_path", db_path)
    elif args.db:
        raise ValueError("--db is only supported for the sqlite backend. Use --backend-config instead.")

    return create_backend(backend_name, **config)

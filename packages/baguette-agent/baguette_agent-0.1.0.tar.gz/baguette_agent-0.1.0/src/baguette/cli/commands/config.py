from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from ..storage import default_db_path
from ..utils import parse_backend_config, resolve_value_with_source, format_table
from ...config import get_config_path, load_config


def register(subparsers: argparse._SubParsersAction) -> None:
    config_parser = subparsers.add_parser("config", help="Configuration commands")
    config_sub = config_parser.add_subparsers(dest="config_command", required=True)
    config_show = config_sub.add_parser("show", help="Show resolved configuration")
    config_show.add_argument("--format", choices=["table", "json"], default="json")
    config_show.set_defaults(handler=handle_config_show, needs_storage=False)


def handle_config_show(args: argparse.Namespace) -> int:
    config_path = get_config_path()
    config_path_source = "env" if os.getenv("BAGUETTE_CONFIG", "").strip() else "default"
    config_loaded = config_path.exists()
    config_payload = load_config()
    storage_config = config_payload.get("storage") if isinstance(config_payload, dict) else {}
    if not isinstance(storage_config, dict):
        storage_config = {}

    backend, backend_source = resolve_value_with_source(
        args.backend,
        os.getenv("BAGUETTE_BACKEND"),
        storage_config.get("backend"),
        "sqlite",
    )
    raw_backend_config, backend_config_source = resolve_value_with_source(
        args.backend_config,
        os.getenv("BAGUETTE_BACKEND_CONFIG"),
        storage_config.get("backend_config"),
        None,
    )
    backend_config = parse_backend_config(raw_backend_config)
    raw_db, db_source = resolve_value_with_source(
        args.db,
        os.getenv("BAGUETTE_DB"),
        storage_config.get("db"),
        None,
    )
    db_path = Path(raw_db).expanduser() if raw_db else default_db_path()

    resolved = {
        "storage": {
            "backend": backend,
            "db": str(db_path),
            "backend_config": backend_config,
        }
    }
    sources = {
        "config.path": config_path_source,
        "storage.backend": backend_source,
        "storage.db": db_source if raw_db is not None else "default",
        "storage.backend_config": backend_config_source,
    }
    payload = {
        "config_path": str(config_path),
        "config_loaded": config_loaded,
        "precedence": ["cli", "env", "config", "defaults"],
        "resolved": resolved,
        "sources": sources,
        "notes": ["storage.db is only used when backend == sqlite"],
    }

    if args.format == "json":
        print(json.dumps(payload, indent=2))
        return 0

    rows = [
        ["config.path", str(config_path), config_path_source],
        ["config.loaded", str(config_loaded).lower(), "filesystem"],
        ["storage.backend", str(backend), backend_source],
        ["storage.db", str(db_path), sources["storage.db"]],
        ["storage.backend_config", json.dumps(backend_config, ensure_ascii=True), backend_config_source],
    ]
    print("Precedence: cli > env > config > defaults")
    print(format_table(["KEY", "VALUE", "SOURCE"], rows))
    return 0

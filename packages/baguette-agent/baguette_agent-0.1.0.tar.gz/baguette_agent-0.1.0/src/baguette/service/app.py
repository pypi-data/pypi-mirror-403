from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Dict, Optional
import argparse
import json
import os
from pathlib import Path

from ..config import get_config_section
from ..skills import SkillValidationError
from ..storage.base import StorageBackend
from ..storage.registry import BackendNotFoundError, BackendRegistryError, create_backend
from .routes import register_routes


class ServiceError(RuntimeError):
    pass


def _require_fastapi():
    try:
        from fastapi import Body, FastAPI, HTTPException, Query
    except ImportError as exc:
        raise ServiceError(
            "fastapi is required for the storage service; install baguette[service]."
        ) from exc
    return Body, FastAPI, HTTPException, Query


def default_db_path() -> Path:
    override = os.getenv("BAGUETTE_DB")
    if override:
        return Path(override)
    return Path.home() / ".baguette" / "baguette.db"


def parse_backend_config(raw: Any) -> Dict[str, Any]:
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            config = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON for backend config: {exc}") from exc
        if not isinstance(config, dict):
            raise ValueError("Backend config must be a JSON object.")
        return config
    raise ValueError("Backend config must be a JSON object.")


def resolve_backend_name(value: Optional[str]) -> str:
    config = get_config_section("storage")
    return value or os.getenv("BAGUETTE_BACKEND") or config.get("backend") or "sqlite"


def build_storage_from_env() -> StorageBackend:
    storage_config = get_config_section("storage")
    backend_name = resolve_backend_name(None)
    raw_backend_config = os.getenv("BAGUETTE_BACKEND_CONFIG") or storage_config.get("backend_config")
    config = parse_backend_config(raw_backend_config)

    if backend_name == "sqlite":
        db_value = os.getenv("BAGUETTE_DB") or storage_config.get("db")
        config.setdefault(
            "db_path",
            Path(db_value).expanduser() if db_value else default_db_path(),
        )

    return create_backend(backend_name, **config)


def create_app(storage: StorageBackend):
    Body, FastAPI, HTTPException, Query = _require_fastapi()
    @asynccontextmanager
    async def lifespan(app: Any):
        storage.initialize()
        yield

    app = FastAPI(title="Baguette Storage Service", version="0.1.0", lifespan=lifespan)

    def _raise_http(exc: Exception) -> None:
        if isinstance(exc, KeyError):
            raise HTTPException(status_code=404, detail=str(exc))
        if isinstance(exc, (ValueError, FileNotFoundError, SkillValidationError)):
            raise HTTPException(status_code=400, detail=str(exc))
        if isinstance(exc, (BackendNotFoundError, BackendRegistryError, ServiceError)):
            raise HTTPException(status_code=500, detail=str(exc))
        raise HTTPException(status_code=500, detail="Internal server error.")

    @app.get("/health")
    def health() -> Dict[str, str]:
        return {"status": "ok"}

    register_routes(app, storage, _raise_http, Body, Query)
    return app


def create_app_from_env():
    storage = build_storage_from_env()
    return create_app(storage)


def run_server(
    *,
    storage: Optional[StorageBackend] = None,
    host: str = "127.0.0.1",
    port: int = 8000,
    log_level: str = "info",
    reload: bool = False,
) -> int:
    try:
        import uvicorn
    except ImportError as exc:
        raise ServiceError(
            "uvicorn is required for the storage service; install baguette[service]."
        ) from exc

    if reload:
        uvicorn.run(
            "baguette.service.app:create_app_from_env",
            factory=True,
            host=host,
            port=port,
            log_level=log_level,
            reload=True,
        )
        return 0

    if storage is None:
        storage = build_storage_from_env()
    app = create_app(storage)
    uvicorn.run(app, host=host, port=port, log_level=log_level)
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="baguette-service", description="Baguette storage service")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8000, help="Bind port")
    parser.add_argument("--log-level", default="info", help="Uvicorn log level")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (env-based config only)")
    parser.add_argument(
        "--backend",
        help="Storage backend name (env: BAGUETTE_BACKEND, default: sqlite)",
    )
    parser.add_argument(
        "--backend-config",
        help="JSON object with backend-specific configuration",
    )
    parser.add_argument("--db", help="Path to SQLite DB")
    args = parser.parse_args(argv)

    if args.backend:
        os.environ["BAGUETTE_BACKEND"] = args.backend
    if args.backend_config:
        os.environ["BAGUETTE_BACKEND_CONFIG"] = args.backend_config
    if args.db:
        os.environ["BAGUETTE_DB"] = args.db

    storage = build_storage_from_env()
    try:
        storage.initialize()
    except Exception as exc:
        raise ServiceError(f"Storage error: {exc}") from exc

    return run_server(
        storage=None if args.reload else storage,
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        reload=args.reload,
    )

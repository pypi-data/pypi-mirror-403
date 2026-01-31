from __future__ import annotations

from importlib import metadata
from pathlib import Path
from typing import Callable, Dict, Iterable, Optional
import warnings

from .base import StorageBackend

BackendFactory = Callable[..., StorageBackend]

_BACKENDS: Dict[str, BackendFactory] = {}
_DEFAULT_BACKEND: Optional[str] = None
_BUILTINS_LOADED = False
_ENTRYPOINTS_LOADED = False


class BackendRegistryError(RuntimeError):
    pass


class BackendNotFoundError(KeyError):
    pass


def register_backend(
    name: str,
    factory: BackendFactory,
    *,
    is_default: bool = False,
    overwrite: bool = False,
) -> None:
    normalized = name.strip().lower()
    if not normalized:
        raise BackendRegistryError("Backend name cannot be empty.")
    if not overwrite and normalized in _BACKENDS:
        raise BackendRegistryError(f"Backend already registered: {normalized}")
    _BACKENDS[normalized] = factory

    global _DEFAULT_BACKEND
    if is_default or _DEFAULT_BACKEND is None:
        _DEFAULT_BACKEND = normalized


def list_backends() -> Iterable[str]:
    _ensure_loaded()
    return sorted(_BACKENDS.keys())


def get_default_backend_name() -> str:
    _ensure_loaded()
    if not _DEFAULT_BACKEND:
        raise BackendRegistryError("No default backend has been registered.")
    return _DEFAULT_BACKEND


def create_backend(name: str, **config: object) -> StorageBackend:
    _ensure_loaded()
    normalized = name.strip().lower()
    if normalized not in _BACKENDS:
        available = ", ".join(sorted(_BACKENDS.keys()))
        raise BackendNotFoundError(f"Unknown backend '{name}'. Available: {available or 'none'}")
    factory = _BACKENDS[normalized]
    try:
        return factory(**config)
    except TypeError as exc:
        raise BackendRegistryError(
            f"Failed to initialize backend '{name}': {exc}"
        ) from exc


def _ensure_loaded() -> None:
    _register_builtin_backends()
    _load_entrypoints()


def _register_builtin_backends() -> None:
    global _BUILTINS_LOADED
    if _BUILTINS_LOADED:
        return

    from .sqlite import SQLiteStorage

    def _sqlite_factory(*, db_path: str | Path, **_: object) -> StorageBackend:
        if not db_path:
            raise BackendRegistryError("sqlite backend requires 'db_path'.")
        return SQLiteStorage(db_path)

    register_backend("sqlite", _sqlite_factory, is_default=True)

    try:
        from .postgres import PostgresStorage
    except Exception as exc:
        warnings.warn(
            f"Postgres backend unavailable: {exc}. Install baguette[postgres] to enable.",
            RuntimeWarning,
        )
    else:
        def _postgres_factory(
            *,
            dsn: str,
            schema: str = "public",
            connect_timeout: int = 10,
            application_name: str = "baguette",
            **_: object,
        ) -> StorageBackend:
            if not dsn:
                raise BackendRegistryError("postgres backend requires 'dsn'.")
            return PostgresStorage(
                dsn=dsn,
                schema=schema,
                connect_timeout=connect_timeout,
                application_name=application_name,
            )

        register_backend("postgres", _postgres_factory)
    _BUILTINS_LOADED = True


def _load_entrypoints() -> None:
    global _ENTRYPOINTS_LOADED
    if _ENTRYPOINTS_LOADED:
        return

    eps = metadata.entry_points()
    if hasattr(eps, "select"):
        matches = eps.select(group="baguette.storage_backends")
    else:
        matches = eps.get("baguette.storage_backends", [])

    for entry_point in matches:
        name = entry_point.name
        try:
            loaded = entry_point.load()
        except Exception as exc:
            warnings.warn(f"Failed to load backend plugin '{name}': {exc}", RuntimeWarning)
            continue

        factory: Optional[BackendFactory] = None
        if isinstance(loaded, type) and issubclass(loaded, StorageBackend):
            factory = loaded  # type: ignore[assignment]
        elif callable(loaded):
            factory = loaded  # type: ignore[assignment]

        if not factory:
            warnings.warn(
                f"Ignoring backend plugin '{name}': not a callable or StorageBackend subclass.",
                RuntimeWarning,
            )
            continue

        try:
            register_backend(name, factory)
        except BackendRegistryError as exc:
            warnings.warn(f"Failed to register backend plugin '{name}': {exc}", RuntimeWarning)

    _ENTRYPOINTS_LOADED = True

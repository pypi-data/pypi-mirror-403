from __future__ import annotations

import argparse
import sys
from typing import List

from .commands import artifacts, config, journal, memory, replay, run, serve, trace, transactions
from .storage import build_storage
from .utils import ExecutionError
from ..skills import SkillValidationError
from ..storage.registry import BackendNotFoundError, BackendRegistryError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="baguette", description="Baguette CLI")
    parser.add_argument("--db", help="Path to SQLite DB")
    parser.add_argument(
        "--backend",
        help="Storage backend name (env: BAGUETTE_BACKEND, default: sqlite)",
    )
    parser.add_argument(
        "--backend-config",
        help="JSON object with backend-specific configuration",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    artifacts.register(subparsers)
    run.register(subparsers)
    transactions.register(subparsers)
    trace.register(subparsers)
    journal.register(subparsers)
    replay.register(subparsers)
    memory.register(subparsers)
    config.register(subparsers)
    serve.register(subparsers)

    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    handler = getattr(args, "handler", None)
    if handler is None:
        parser.error("No handler registered.")
    needs_storage = getattr(args, "needs_storage", True)

    try:
        if not needs_storage:
            return handler(args)

        storage = build_storage(args)
        storage.initialize()
        return handler(storage, args)
    except SkillValidationError as exc:
        print(f"Invalid skill: {exc}", file=sys.stderr)
        return 1
    except (BackendNotFoundError, BackendRegistryError) as exc:
        print(f"Storage error: {exc}", file=sys.stderr)
        return 2
    except (ValueError, FileNotFoundError) as exc:
        print(f"Invalid input: {exc}", file=sys.stderr)
        return 1
    except ExecutionError as exc:
        print(f"Execution error: {exc}", file=sys.stderr)
        return 3
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import os


def register(subparsers: argparse._SubParsersAction) -> None:
    serve_parser = subparsers.add_parser("serve", help="Run storage service")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    serve_parser.add_argument("--port", type=int, default=8000, help="Bind port")
    serve_parser.add_argument("--log-level", default="info", help="Uvicorn log level")
    serve_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (uses env-based configuration)",
    )
    serve_parser.set_defaults(handler=handle_serve, needs_storage=True)


def handle_serve(storage, args: argparse.Namespace) -> int:
    try:
        from ...service.app import run_server
    except Exception as exc:
        raise RuntimeError(
            "Storage service dependencies are missing. Install baguette[service]."
        ) from exc

    if args.reload:
        if args.backend:
            os.environ["BAGUETTE_BACKEND"] = args.backend
        if args.backend_config:
            os.environ["BAGUETTE_BACKEND_CONFIG"] = args.backend_config
        if args.db:
            os.environ["BAGUETTE_DB"] = str(args.db)
        return run_server(
            storage=None,
            host=args.host,
            port=args.port,
            log_level=args.log_level,
            reload=True,
        )

    return run_server(
        storage=storage,
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        reload=False,
    )

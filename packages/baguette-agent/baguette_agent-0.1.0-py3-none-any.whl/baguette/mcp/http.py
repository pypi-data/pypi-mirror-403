from __future__ import annotations

import argparse
import json
import os
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..cli.storage import build_storage
from ..config import get_config_section
from ..storage.base import StorageBackend
from .server import MCPError, MCPServer, JSONRPC_INVALID_REQUEST, JSONRPC_PARSE_ERROR


class MCPHttpError(RuntimeError):
    pass


def _require_fastapi():
    try:
        from fastapi import FastAPI, HTTPException, Request, Response
        from fastapi.responses import JSONResponse, StreamingResponse
    except ImportError as exc:
        raise MCPHttpError(
            "fastapi is required for MCP HTTP/SSE; install baguette[service]."
        ) from exc
    return FastAPI, HTTPException, Request, Response, JSONResponse, StreamingResponse


def _parse_allowed_origins(raw: Optional[str]) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _default_allowed_origins() -> list[str]:
    return [
        "http://localhost",
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
    ]


def _validate_origin(origin: Optional[str], allowed: list[str]) -> None:
    if not origin:
        return
    if "*" in allowed:
        return
    if origin not in allowed:
        raise MCPHttpError(f"Origin not allowed: {origin}")


@dataclass
class _SSEClient:
    client_id: Optional[str]
    queue: "asyncio.Queue[str]"
    event_name: Optional[str]


class _SSEManager:
    def __init__(self) -> None:
        import asyncio

        self._asyncio = asyncio
        self._stream_clients: list[_SSEClient] = []
        self._legacy_clients: Dict[str, _SSEClient] = {}

    def register_stream(self) -> _SSEClient:
        client = _SSEClient(client_id=None, queue=self._asyncio.Queue(), event_name=None)
        self._stream_clients.append(client)
        return client

    def register_legacy(self, client_id: str) -> _SSEClient:
        client = _SSEClient(client_id=client_id, queue=self._asyncio.Queue(), event_name="message")
        self._legacy_clients[client_id] = client
        return client

    def unregister(self, client: _SSEClient) -> None:
        if client.client_id and client.client_id in self._legacy_clients:
            self._legacy_clients.pop(client.client_id, None)
        if client in self._stream_clients:
            self._stream_clients.remove(client)

    async def send_endpoint(self, client: _SSEClient, endpoint: str) -> None:
        payload = f"event: endpoint\ndata: {endpoint}\n\n"
        await client.queue.put(payload)

    async def send(self, client: _SSEClient, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False)
        if client.event_name:
            message = f"event: {client.event_name}\ndata: {data}\n\n"
        else:
            message = f"data: {data}\n\n"
        await client.queue.put(message)

    async def broadcast(self, payload: dict) -> None:
        for client in list(self._stream_clients):
            await self.send(client, payload)
        for client in list(self._legacy_clients.values()):
            await self.send(client, payload)

    async def send_to_legacy(self, client_id: str, payload: dict) -> None:
        client = self._legacy_clients.get(client_id)
        if client is None:
            return
        await self.send(client, payload)


def create_app(
    storage: StorageBackend,
    *,
    enable_sse: bool = True,
    enable_legacy_sse: bool = True,
    allowed_origins: Optional[list[str]] = None,
) -> Any:
    FastAPI, HTTPException, Request, Response, JSONResponse, StreamingResponse = _require_fastapi()
    import asyncio

    @asynccontextmanager
    async def lifespan(app: Any):
        storage.initialize()
        yield

    app = FastAPI(title="Baguette MCP Server", version="0.1.0", lifespan=lifespan)
    mcp = MCPServer(storage)
    sse = _SSEManager()

    # Ensure FastAPI can resolve the Request type with future annotations.
    globals()["FastAPIRequest"] = Request

    if enable_sse or enable_legacy_sse:
        mcp.set_notifier(lambda payload: asyncio.create_task(sse.broadcast(payload)))

    if allowed_origins is None:
        allowed_origins = _default_allowed_origins()

    def _check_origin(request: Request) -> None:
        try:
            _validate_origin(request.headers.get("origin"), allowed_origins or [])
        except MCPHttpError as exc:
            raise HTTPException(status_code=403, detail=str(exc))

    @app.post("/mcp")
    async def mcp_post(request: "FastAPIRequest") -> Response:
        _check_origin(request)
        try:
            payload = await request.json()
        except Exception as exc:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": JSONRPC_PARSE_ERROR, "message": str(exc)},
                },
            )

        try:
            response = mcp.handle_request(payload)
        except MCPError as exc:
            error = {"code": exc.code, "message": exc.message}
            if exc.data is not None:
                error["data"] = exc.data
            return JSONResponse(
                status_code=200,
                content={"jsonrpc": "2.0", "id": payload.get("id"), "error": error},
            )
        except Exception as exc:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": payload.get("id"),
                    "error": {"code": JSONRPC_INVALID_REQUEST, "message": str(exc)},
                },
            )

        if response is None:
            return Response(status_code=202)
        return JSONResponse(status_code=200, content=response)

    @app.get("/mcp")
    async def mcp_get(request: "FastAPIRequest"):
        _check_origin(request)
        if not enable_sse:
            raise HTTPException(status_code=405, detail="SSE not enabled.")
        accept = request.headers.get("accept", "")
        if "text/event-stream" not in accept:
            raise HTTPException(status_code=406, detail="text/event-stream required.")
        client = sse.register_stream()

        async def _events():
            try:
                while True:
                    data = await client.queue.get()
                    yield data
                    if await request.is_disconnected():
                        break
            finally:
                sse.unregister(client)

        return StreamingResponse(_events(), media_type="text/event-stream")

    @app.get("/sse")
    async def legacy_sse(request: "FastAPIRequest"):
        _check_origin(request)
        if not enable_legacy_sse:
            raise HTTPException(status_code=405, detail="Legacy SSE not enabled.")
        accept = request.headers.get("accept", "")
        if "text/event-stream" not in accept:
            raise HTTPException(status_code=406, detail="text/event-stream required.")
        client_id = uuid.uuid4().hex
        client = sse.register_legacy(client_id)
        endpoint = str(request.base_url) + f"messages/{client_id}"
        await sse.send_endpoint(client, endpoint)

        async def _events():
            try:
                while True:
                    data = await client.queue.get()
                    yield data
                    if await request.is_disconnected():
                        break
            finally:
                sse.unregister(client)

        return StreamingResponse(_events(), media_type="text/event-stream")

    @app.post("/messages/{client_id}")
    async def legacy_messages(client_id: str, request: "FastAPIRequest") -> Response:
        _check_origin(request)
        if not enable_legacy_sse:
            raise HTTPException(status_code=405, detail="Legacy SSE not enabled.")
        try:
            payload = await request.json()
        except Exception as exc:
            error = {"code": JSONRPC_PARSE_ERROR, "message": str(exc)}
            await sse.send_to_legacy(
                client_id,
                {"jsonrpc": "2.0", "id": None, "error": error},
            )
            return Response(status_code=400)

        try:
            response = mcp.handle_request(payload)
        except MCPError as exc:
            error = {"code": exc.code, "message": exc.message}
            if exc.data is not None:
                error["data"] = exc.data
            await sse.send_to_legacy(
                client_id,
                {"jsonrpc": "2.0", "id": payload.get("id"), "error": error},
            )
            return Response(status_code=202)
        except Exception as exc:
            await sse.send_to_legacy(
                client_id,
                {
                    "jsonrpc": "2.0",
                    "id": payload.get("id"),
                    "error": {"code": JSONRPC_INVALID_REQUEST, "message": str(exc)},
                },
            )
            return Response(status_code=202)

        if response is not None:
            await sse.send_to_legacy(client_id, response)
        return Response(status_code=202)

    return app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="baguette-mcp-http", description="Baguette MCP HTTP server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8001, help="Bind port")
    parser.add_argument("--log-level", default="info", help="Uvicorn log level")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (env-based config only)")
    parser.add_argument("--allowed-origins", help="Comma-separated Origin allowlist (use * to allow all)")
    parser.add_argument("--disable-sse", action="store_true", help="Disable SSE stream on GET /mcp")
    parser.add_argument(
        "--enable-legacy-sse",
        action="store_true",
        help="Enable legacy SSE transport (/sse + /messages/{client_id})",
    )
    parser.add_argument(
        "--backend",
        help="Storage backend name (env: BAGUETTE_BACKEND, default: sqlite)",
    )
    parser.add_argument(
        "--backend-config",
        help="JSON object with backend-specific configuration",
    )
    parser.add_argument("--db", help="Path to SQLite DB")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    try:
        import uvicorn
    except ImportError as exc:
        raise MCPHttpError("uvicorn is required for MCP HTTP/SSE; install baguette[service].") from exc

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.backend:
        os.environ["BAGUETTE_BACKEND"] = args.backend
    if args.backend_config:
        os.environ["BAGUETTE_BACKEND_CONFIG"] = args.backend_config
    if args.db:
        os.environ["BAGUETTE_DB"] = args.db

    storage = build_storage(args)
    storage.initialize()
    allowlist = _parse_allowed_origins(
        args.allowed_origins
        or os.getenv("BAGUETTE_MCP_ALLOWED_ORIGINS")
        or get_config_section("mcp").get("allowed_origins")
    )
    app = create_app(
        storage,
        enable_sse=not bool(args.disable_sse),
        enable_legacy_sse=bool(args.enable_legacy_sse),
        allowed_origins=allowlist or _default_allowed_origins(),
    )
    if args.reload:
        uvicorn.run(
            "baguette.mcp.http:create_app_from_env",
            factory=True,
            host=args.host,
            port=args.port,
            log_level=args.log_level,
            reload=True,
        )
        return 0
    uvicorn.run(app, host=args.host, port=args.port, log_level=args.log_level)
    return 0


def create_app_from_env():
    storage = build_storage(argparse.Namespace(backend=None, backend_config=None, db=None))
    allowlist = _parse_allowed_origins(
        os.getenv("BAGUETTE_MCP_ALLOWED_ORIGINS") or get_config_section("mcp").get("allowed_origins")
    )
    return create_app(storage, allowed_origins=allowlist or _default_allowed_origins())


if __name__ == "__main__":
    raise SystemExit(main())

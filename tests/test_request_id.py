"""Unit tests for RequestIDMiddleware."""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.requests import Request
from starlette.responses import Response

from app.core.middleware.request_id import RequestIDMiddleware


def _make_request(headers: dict | None = None):
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_request_id_middleware_generates_id():
    app = AsyncMock()
    middleware = RequestIDMiddleware(app=app)
    
    scope = {
        "type": "http",
        "headers": [],
    }
    
    async def receive(): return {"type": "http.request"}
    
    async def send(message):
        if message["type"] == "http.response.start":
            headers = dict(message["headers"])
            assert b"x-request-id" in headers
            rid = headers[b"x-request-id"].decode()
            uuid.UUID(rid)

    await middleware(scope, receive, send)


@pytest.mark.asyncio
async def test_request_id_middleware_uses_provided_id():
    app = AsyncMock()
    middleware = RequestIDMiddleware(app=app)
    
    scope = {
        "type": "http",
        "headers": [(b"x-request-id", b"custom-123")],
    }
    
    async def receive(): return {"type": "http.request"}
    
    async def send(message):
        if message["type"] == "http.response.start":
            headers = dict(message["headers"])
            assert headers[b"x-request-id"] == b"custom-123"

    await middleware(scope, receive, send)


@pytest.mark.asyncio
async def test_request_id_middleware_sets_state():
    app = AsyncMock()
    middleware = RequestIDMiddleware(app=app)
    
    scope = {
        "type": "http",
        "headers": [(b"x-request-id", b"state-test")],
    }
    
    async def receive(): return {"type": "http.request"}
    async def send(message): pass

    await middleware(scope, receive, send)
    assert scope["state"]["request_id"] == "state-test"

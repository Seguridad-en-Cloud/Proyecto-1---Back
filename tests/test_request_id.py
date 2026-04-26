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
    middleware = RequestIDMiddleware(app=MagicMock())
    request = _make_request()
    response = Response("ok", status_code=200)
    call_next = AsyncMock(return_value=response)

    result = await middleware.dispatch(request, call_next)
    # Should have X-Request-Id header
    assert "x-request-id" in result.headers
    # Should be a valid UUID
    rid = result.headers["x-request-id"]
    uuid.UUID(rid)  # will raise if not valid


@pytest.mark.asyncio
async def test_request_id_middleware_uses_provided_id():
    middleware = RequestIDMiddleware(app=MagicMock())
    request = _make_request({"X-Request-Id": "custom-123"})
    response = Response("ok", status_code=200)
    call_next = AsyncMock(return_value=response)

    result = await middleware.dispatch(request, call_next)
    assert result.headers["x-request-id"] == "custom-123"


@pytest.mark.asyncio
async def test_request_id_middleware_sets_state():
    middleware = RequestIDMiddleware(app=MagicMock())
    request = _make_request({"X-Request-Id": "state-test"})
    response = Response("ok", status_code=200)
    call_next = AsyncMock(return_value=response)

    await middleware.dispatch(request, call_next)
    assert request.state.request_id == "state-test"

"""Unit tests for middleware: request_id and errors."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request

from app.core.middleware.errors import (
    general_exception_handler,
    http_exception_handler,
    rate_limit_exception_handler,
    validation_exception_handler,
)


def _make_request_with_id(request_id: str = "test-id") -> MagicMock:
    """Create a mock Request with request_id state."""
    mock = MagicMock(spec=Request)
    mock.state.request_id = request_id
    return mock


@pytest.mark.asyncio
async def test_http_exception_handler():
    """Test HTTP exception handler returns correct format."""
    request = _make_request_with_id("req-123")
    exc = HTTPException(status_code=404, detail="Not found")

    response = await http_exception_handler(request, exc)

    assert response.status_code == 404
    import json
    body = json.loads(response.body)
    assert body["detail"] == "Not found"
    assert body["request_id"] == "req-123"


@pytest.mark.asyncio
async def test_validation_exception_handler():
    """Test validation exception handler returns 422."""
    request = _make_request_with_id("req-456")
    exc = RequestValidationError(errors=[{"loc": ["body", "name"], "msg": "required"}])

    response = await validation_exception_handler(request, exc)

    assert response.status_code == 422
    import json
    body = json.loads(response.body)
    assert body["detail"] == "validation_error"
    assert body["request_id"] == "req-456"


@pytest.mark.asyncio
async def test_general_exception_handler():
    """Test general exception handler returns 500."""
    request = _make_request_with_id("req-789")
    exc = RuntimeError("unexpected")

    response = await general_exception_handler(request, exc)

    assert response.status_code == 500
    import json
    body = json.loads(response.body)
    assert body["detail"] == "internal_server_error"
    assert body["request_id"] == "req-789"


@pytest.mark.asyncio
async def test_rate_limit_exception_handler():
    """Test rate limit exception handler returns 429."""
    from slowapi.errors import RateLimitExceeded

    request = _make_request_with_id("req-rate")
    exc = RateLimitExceeded(MagicMock())

    response = await rate_limit_exception_handler(request, exc)

    assert response.status_code == 429
    import json
    body = json.loads(response.body)
    assert body["detail"] == "rate_limit_exceeded"

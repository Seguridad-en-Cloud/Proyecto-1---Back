"""Unit tests for FastAPI application setup (main.py)."""
import pytest
from unittest.mock import patch, MagicMock

from app.main import app, shutdown_event


def test_app_title():
    assert app.title is not None
    assert len(app.title) > 0


def test_app_has_routes():
    routes = [r.path for r in app.routes]
    assert "/api/v1/auth/health" in routes or any("/api/v1/auth" in r for r in routes)


def test_app_has_middleware():
    # At minimum, CORS and RequestID middleware should be registered
    middleware_classes = [m.cls.__name__ if hasattr(m, 'cls') else str(m) for m in app.user_middleware]
    assert any("RequestID" in str(mc) for mc in middleware_classes)


def test_app_exception_handlers():
    # The app should have custom exception handlers registered
    assert len(app.exception_handlers) > 0


def test_app_version():
    assert app.version == "1.0.0"


def test_app_routers_registered():
    paths = [r.path for r in app.routes]
    # Check key route prefixes exist
    expected_prefixes = [
        "/api/v1/auth",
        "/api/v1/admin/restaurant",
        "/api/v1/admin/categories",
        "/api/v1/admin/dishes",
        "/api/v1/admin/analytics",
        "/api/v1/menu",
    ]
    for prefix in expected_prefixes:
        assert any(prefix in p for p in paths), f"Missing route prefix: {prefix}"


# ── Graceful shutdown ──

@pytest.mark.asyncio
async def test_shutdown_event_with_executor():
    """shutdown_event calls _executor.shutdown(wait=True) when pool exists."""
    mock_executor = MagicMock()
    with patch("app.services.upload_service._executor", mock_executor):
        await shutdown_event()
        mock_executor.shutdown.assert_called_once_with(wait=True)


@pytest.mark.asyncio
async def test_shutdown_event_without_executor():
    """shutdown_event does nothing when no pool has been created."""
    with patch("app.services.upload_service._executor", None):
        await shutdown_event()  # should not raise

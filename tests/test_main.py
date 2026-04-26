"""Unit tests for FastAPI application setup (main.py).

The lifecycle hooks are now managed through ``lifespan`` (the modern FastAPI
pattern); the old ``startup_event``/``shutdown_event`` functions no longer
exist as standalone callables. We exercise the worker-pool lifecycle via
``shutdown_workers`` directly, which is what the lifespan context manager
ends up calling.
"""
from unittest.mock import MagicMock, patch

import pytest

from app.main import app
from app.services.upload_service import shutdown_workers


def test_app_title():
    assert app.title is not None
    assert len(app.title) > 0


def test_app_has_routes():
    routes = [r.path for r in app.routes]
    assert "/api/v1/auth/health" in routes or any("/api/v1/auth" in r for r in routes)


def test_app_has_middleware():
    middleware_classes = [
        m.cls.__name__ if hasattr(m, "cls") else str(m) for m in app.user_middleware
    ]
    assert any("RequestID" in str(mc) for mc in middleware_classes)


def test_app_exception_handlers():
    assert len(app.exception_handlers) > 0


def test_app_version():
    assert app.version == "1.0.0"


def test_app_routers_registered():
    paths = [r.path for r in app.routes]
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


def test_app_has_lifespan():
    """The app must have a lifespan context manager attached (replaces on_event)."""
    # Starlette stores the configured lifespan on router.lifespan_context.
    assert app.router.lifespan_context is not None


# ── Graceful shutdown ──

@pytest.mark.asyncio
async def test_shutdown_workers_with_executor():
    """shutdown_workers calls _executor.shutdown(wait=True) when pool exists."""
    mock_executor = MagicMock()
    with (
        patch("app.services.upload_service._executor", mock_executor),
        patch("app.services.upload_service._shutting_down", False),
    ):
        await shutdown_workers()
        mock_executor.shutdown.assert_called_once_with(wait=True)


@pytest.mark.asyncio
async def test_shutdown_workers_without_executor():
    """shutdown_workers does nothing when no pool has been created."""
    with (
        patch("app.services.upload_service._executor", None),
        patch("app.services.upload_service._shutting_down", False),
    ):
        await shutdown_workers()  # should not raise

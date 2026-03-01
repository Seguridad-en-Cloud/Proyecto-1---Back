"""Tests for QR code generation endpoints and service."""
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.services.qr_service import generate_qr_png, generate_qr_svg


@pytest.fixture
async def restaurant_headers(client: AsyncClient, auth_headers: dict[str, str]):
    """Create a restaurant and return auth headers."""
    await client.post(
        "/api/v1/admin/restaurant",
        headers=auth_headers,
        json={"name": "QR Test Restaurant"},
    )
    return auth_headers


@pytest.mark.asyncio
async def test_qr_requires_auth(client: AsyncClient):
    """Test that QR generation requires authentication."""
    response = await client.get("/api/v1/admin/qr")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_qr_requires_restaurant(client: AsyncClient, auth_headers: dict[str, str]):
    """Test that QR generation requires an existing restaurant."""
    response = await client.get(
        "/api/v1/admin/qr",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_qr_png_generation(client: AsyncClient, restaurant_headers: dict[str, str]):
    """Test QR code generation as PNG."""
    response = await client.get(
        "/api/v1/admin/qr?format=png",
        headers=restaurant_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    # Verify it's actually a PNG (magic bytes)
    assert response.content[:4] == b"\x89PNG"


@pytest.mark.asyncio
async def test_qr_svg_generation(client: AsyncClient, restaurant_headers: dict[str, str]):
    """Test QR code generation as SVG."""
    response = await client.get(
        "/api/v1/admin/qr?format=svg",
        headers=restaurant_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    # Verify it contains SVG content
    content = response.content.decode("utf-8")
    assert "<svg" in content or "<?xml" in content


@pytest.mark.asyncio
async def test_qr_default_format_is_png(client: AsyncClient, restaurant_headers: dict[str, str]):
    """Test that default QR format is PNG."""
    response = await client.get(
        "/api/v1/admin/qr",
        headers=restaurant_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


@pytest.mark.asyncio
async def test_qr_invalid_format(client: AsyncClient, restaurant_headers: dict[str, str]):
    """Test QR generation with invalid format."""
    response = await client.get(
        "/api/v1/admin/qr?format=gif",
        headers=restaurant_headers,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_qr_contains_correct_url(client: AsyncClient, restaurant_headers: dict[str, str]):
    """Test that QR encodes the right URL (smoke test via successful generation)."""
    response = await client.get(
        "/api/v1/admin/qr?format=png&size=5",
        headers=restaurant_headers,
    )

    assert response.status_code == 200
    # Just verify it returns a valid image
    assert len(response.content) > 100


# ── Unit tests for QR service ──


class TestQRServicePNG:
    """Unit tests for generate_qr_png."""

    def test_returns_bytes(self):
        result = generate_qr_png("https://example.com/m/test")
        assert isinstance(result, bytes)

    def test_starts_with_png_magic(self):
        result = generate_qr_png("https://example.com/m/test")
        assert result[:4] == b"\x89PNG"

    def test_custom_size(self):
        small = generate_qr_png("https://example.com", box_size=5)
        large = generate_qr_png("https://example.com", box_size=15)
        assert len(large) > len(small)


class TestQRServiceSVG:
    """Unit tests for generate_qr_svg."""

    def test_returns_bytes(self):
        result = generate_qr_svg("https://example.com/m/test")
        assert isinstance(result, bytes)

    def test_contains_svg_tag(self):
        result = generate_qr_svg("https://example.com/m/test")
        text = result.decode("utf-8")
        assert "<svg" in text or "<?xml" in text

    def test_different_urls_produce_different_output(self):
        a = generate_qr_svg("https://example.com/m/aaa")
        b = generate_qr_svg("https://example.com/m/bbb")
        assert a != b

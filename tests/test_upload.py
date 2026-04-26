"""Tests for upload endpoints and service."""
import io
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.services.upload_service import (
    ALLOWED_CONTENT_TYPES,
    _process_image_variant,
)
from app.core.storage import generate_object_key


@pytest.fixture
async def restaurant_headers(client: AsyncClient, auth_headers: dict[str, str]):
    """Create a restaurant and return auth headers."""
    await client.post(
        "/api/v1/admin/restaurant",
        headers=auth_headers,
        json={"name": "Upload Test Restaurant"},
    )
    return auth_headers


@pytest.mark.asyncio
async def test_upload_requires_auth(client: AsyncClient):
    """Test that upload requires authentication."""
    response = await client.post("/api/v1/admin/upload")
    assert response.status_code in (401, 403, 422)


@pytest.mark.asyncio
async def test_upload_requires_restaurant(client: AsyncClient, auth_headers: dict[str, str]):
    """Test that upload requires an existing restaurant."""
    # Create a small valid PNG (1x1 pixel)
    image_bytes = _create_test_png()

    response = await client.post(
        "/api/v1/admin/upload?prefix=dishes",
        headers=auth_headers,
        files={"file": ("test.png", image_bytes, "image/png")},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
@patch("app.services.upload_service.process_and_upload_image")
async def test_upload_image_success(
    mock_upload,
    client: AsyncClient,
    restaurant_headers: dict[str, str],
):
    """Test successful image upload."""
    mock_upload.return_value = {
        "thumbnail": "http://localhost:9000/livemenu/dishes/thumbnail/abc.webp",
        "medium": "http://localhost:9000/livemenu/dishes/medium/abc.webp",
        "large": "http://localhost:9000/livemenu/dishes/large/abc.webp",
    }

    image_bytes = _create_test_png()

    response = await client.post(
        "/api/v1/admin/upload?prefix=dishes",
        headers=restaurant_headers,
        files={"file": ("test.png", image_bytes, "image/png")},
    )

    assert response.status_code == 201
    data = response.json()
    assert "thumbnail" in data
    assert "medium" in data
    assert "large" in data


@pytest.mark.asyncio
@patch("app.services.upload_service.process_and_upload_image")
async def test_upload_invalid_type(
    mock_upload,
    client: AsyncClient,
    restaurant_headers: dict[str, str],
):
    """Test upload with invalid file type."""
    mock_upload.side_effect = ValueError("Invalid file type. Allowed: image/jpeg, image/png, image/webp")

    response = await client.post(
        "/api/v1/admin/upload?prefix=dishes",
        headers=restaurant_headers,
        files={"file": ("test.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
@patch("app.api.routers.upload.delete_image")
async def test_delete_image_success(
    mock_delete,
    client: AsyncClient,
    restaurant_headers: dict[str, str],
):
    """Test deleting an uploaded image.

    The endpoint is ``DELETE /api/v1/admin/upload/{filename:path}`` so the
    object key is part of the URL, not a query parameter.
    """
    mock_delete.return_value = None

    response = await client.delete(
        "/api/v1/admin/upload/dishes/thumbnail/abc.webp",
        headers=restaurant_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["detail"] == "Image deleted successfully"


def _create_test_png() -> bytes:
    """Create a minimal valid PNG image for testing."""
    try:
        from PIL import Image as PILImage

        img = PILImage.new("RGB", (10, 10), color="red")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        # Minimal 1x1 PNG if Pillow not available in test env
        return (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
            b"\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00"
            b"\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
        )


# ── Unit tests for upload service / storage ──


class TestProcessImageVariant:
    """Unit tests for _process_image_variant (runs in-process)."""

    def test_returns_webp_bytes(self):
        png_bytes = _create_test_png()
        result = _process_image_variant(png_bytes, (50, 50), 80)
        assert isinstance(result, bytes)
        # WebP magic bytes: RIFF....WEBP
        assert result[:4] == b"RIFF"
        assert result[8:12] == b"WEBP"

    def test_respects_target_size(self):
        png_bytes = _create_test_png()
        small = _process_image_variant(png_bytes, (5, 5), 80)
        large = _process_image_variant(png_bytes, (100, 100), 80)
        # Both should be valid (non-empty)
        assert len(small) > 0
        assert len(large) > 0


class TestGenerateObjectKey:
    """Unit tests for generate_object_key."""

    def test_returns_string_with_prefix(self):
        key = generate_object_key("dishes/thumbnail", "photo.jpg")
        assert key.startswith("dishes/thumbnail/")

    def test_preserves_file_extension(self):
        key = generate_object_key("logos", "logo.png")
        assert key.endswith(".png")

    def test_unique_keys_for_same_input(self):
        k1 = generate_object_key("dishes", "photo.jpg")
        k2 = generate_object_key("dishes", "photo.jpg")
        assert k1 != k2

    def test_default_webp_for_no_extension(self):
        key = generate_object_key("dishes", "noext")
        assert key.endswith(".webp")


class TestAllowedContentTypes:
    """Verify allowed content types constant."""

    def test_includes_jpeg(self):
        assert "image/jpeg" in ALLOWED_CONTENT_TYPES

    def test_includes_png(self):
        assert "image/png" in ALLOWED_CONTENT_TYPES

    def test_includes_webp(self):
        assert "image/webp" in ALLOWED_CONTENT_TYPES

    def test_excludes_others(self):
        assert "text/plain" not in ALLOWED_CONTENT_TYPES
        assert "application/pdf" not in ALLOWED_CONTENT_TYPES

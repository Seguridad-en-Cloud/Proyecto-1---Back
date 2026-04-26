"""Unit tests for UploadService using mocked S3 and image processing."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.upload_service import (
    ALLOWED_CONTENT_TYPES,
    IMAGE_VARIANTS,
    MAX_SIZE_BYTES,
    _process_image_variant,
    delete_image,
    process_and_upload_image,
)


# ── _process_image_variant ──

def test_process_image_variant_creates_webp():
    """Produce a valid WebP image from a minimal red PNG."""
    from PIL import Image
    import io
    img = Image.new("RGB", (200, 200), "red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw = buf.getvalue()

    result = _process_image_variant(raw, (100, 100), 80)
    assert isinstance(result, bytes)
    assert len(result) > 0
    # Verify it's a valid WebP
    out_img = Image.open(io.BytesIO(result))
    assert out_img.format == "WEBP"


def test_process_image_variant_rgba():
    """RGBA images get converted to RGB before WebP save."""
    from PIL import Image
    import io
    img = Image.new("RGBA", (200, 200), (255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw = buf.getvalue()

    result = _process_image_variant(raw, (50, 50), 90)
    out_img = Image.open(io.BytesIO(result))
    assert out_img.mode == "RGB"


def test_process_image_variant_p_mode():
    """Palette (P) mode images get converted to RGB."""
    from PIL import Image
    import io
    img = Image.new("P", (100, 100))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw = buf.getvalue()

    result = _process_image_variant(raw, (50, 50), 80)
    out_img = Image.open(io.BytesIO(result))
    assert out_img.mode == "RGB"


# ── process_and_upload_image ──

@pytest.mark.asyncio
async def test_process_and_upload_too_large():
    huge = b"\x00" * (MAX_SIZE_BYTES + 1)
    with pytest.raises(ValueError, match="size exceeds"):
        await process_and_upload_image(huge, "image/png", "dishes", "test.png")


@pytest.mark.asyncio
async def test_process_and_upload_invalid_content_type():
    with pytest.raises(ValueError, match="Invalid file type"):
        await process_and_upload_image(b"\x00", "text/plain", "dishes", "test.txt")


@pytest.fixture
async def with_workers():
    """Start the worker pool for tests that exercise the full pipeline.

    In production the workers are launched by the FastAPI ``lifespan`` context
    manager. Plain pytest tests don't go through that lifecycle, so without
    this fixture ``process_and_upload_image`` would put a job on the queue
    and await a future that no consumer ever resolves — i.e. the test would
    hang forever.
    """
    from app.services import upload_service

    await upload_service.start_workers()
    try:
        yield
    finally:
        await upload_service.shutdown_workers()
        # Reset module-level state so the next test starts fresh.
        upload_service._workers.clear()
        upload_service._executor = None
        upload_service._job_queue = None
        upload_service._shutting_down = False


@pytest.mark.asyncio
@patch("app.services.upload_service.upload_file_to_s3")
@patch("app.services.upload_service.generate_object_key", return_value="dishes/abc.webp")
async def test_process_and_upload_success(mock_key, mock_upload, with_workers):
    """Full pipeline: generate variants and upload each."""
    import io

    from PIL import Image

    img = Image.new("RGB", (500, 500), "blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw = buf.getvalue()

    mock_upload.return_value = "http://s3/dishes/abc.webp"

    result = await process_and_upload_image(raw, "image/png", "dishes", "photo.png")
    assert "thumbnail" in result
    assert "medium" in result
    assert "large" in result
    assert mock_upload.call_count == 3  # one per variant


# ── delete_image ──

@pytest.mark.asyncio
@patch("app.services.upload_service.delete_file_from_s3")
@patch("app.services.upload_service.get_public_prefix")
async def test_delete_image_success(mock_prefix, mock_delete):
    mock_prefix.return_value = "http://minio:9000/livemenu"
    url = "http://minio:9000/livemenu/dishes/abc.webp"
    await delete_image(url)
    mock_delete.assert_called_once_with("dishes/abc.webp")


@pytest.mark.asyncio
@patch("app.services.upload_service.delete_file_from_s3")
@patch("app.services.upload_service.get_public_prefix")
async def test_delete_image_foreign_url(mock_prefix, mock_delete):
    """URL that does not start with the configured prefix should not delete."""
    mock_prefix.return_value = "http://minio:9000/livemenu"
    url = "http://other-server/image.png"
    await delete_image(url)
    mock_delete.assert_not_called()


# ── constants ──

def test_image_variants_has_three():
    assert set(IMAGE_VARIANTS.keys()) == {"thumbnail", "medium", "large"}


def test_allowed_content_types():
    assert "image/jpeg" in ALLOWED_CONTENT_TYPES
    assert "image/png" in ALLOWED_CONTENT_TYPES
    assert "image/webp" in ALLOWED_CONTENT_TYPES
    assert "text/plain" not in ALLOWED_CONTENT_TYPES

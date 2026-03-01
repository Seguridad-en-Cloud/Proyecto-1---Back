"""Image upload service with worker pool for processing."""
import asyncio
import io
import logging
from concurrent.futures import ProcessPoolExecutor
from functools import partial

from PIL import Image

from app.core.config import settings
from app.core.storage import delete_file_from_s3, generate_object_key, upload_file_to_s3

logger = logging.getLogger(__name__)

# Image size variants as required by the spec
IMAGE_VARIANTS = {
    "thumbnail": {"size": (150, 150), "quality": 80},
    "medium": {"size": (400, 400), "quality": 85},
    "large": {"size": (800, 800), "quality": 90},
}

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE_BYTES = settings.image_max_size_mb * 1024 * 1024

# Global process pool for image processing
_executor: ProcessPoolExecutor | None = None


def _get_executor() -> ProcessPoolExecutor:
    """Get or create the process pool executor (lazy singleton)."""
    global _executor
    if _executor is None:
        _executor = ProcessPoolExecutor(max_workers=settings.image_worker_count)
    return _executor


def _process_image_variant(
    image_bytes: bytes,
    size: tuple[int, int],
    quality: int,
) -> bytes:
    """Process a single image variant (runs in separate process).

    Args:
        image_bytes: Raw image bytes.
        size: Target (width, height).
        quality: JPEG/WebP quality 1-100.

    Returns:
        Processed image bytes in WebP format.
    """
    img = Image.open(io.BytesIO(image_bytes))

    # Convert RGBA to RGB if needed (for WebP compatibility)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Resize maintaining aspect ratio with cover crop
    img.thumbnail(size, Image.LANCZOS)

    output = io.BytesIO()
    img.save(output, format="WEBP", quality=quality)
    return output.getvalue()


async def process_and_upload_image(
    file_bytes: bytes,
    content_type: str,
    prefix: str,
    original_filename: str,
) -> dict[str, str]:
    """Process image into variants and upload all to S3.

    Args:
        file_bytes: Raw uploaded file bytes.
        content_type: MIME type of the uploaded file.
        prefix: S3 folder prefix ('logos' or 'dishes').
        original_filename: Original filename from the upload.

    Returns:
        dict with keys 'thumbnail', 'medium', 'large' mapping to public URLs.

    Raises:
        ValueError: If file exceeds size limit or has invalid content type.
    """
    if len(file_bytes) > MAX_SIZE_BYTES:
        raise ValueError(
            f"File size exceeds {settings.image_max_size_mb}MB limit"
        )

    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError(
            f"Invalid file type. Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}"
        )

    loop = asyncio.get_event_loop()
    executor = _get_executor()
    urls: dict[str, str] = {}

    # Process all variants concurrently in the process pool
    tasks = {}
    for variant_name, spec in IMAGE_VARIANTS.items():
        func = partial(
            _process_image_variant,
            file_bytes,
            spec["size"],
            spec["quality"],
        )
        tasks[variant_name] = loop.run_in_executor(executor, func)

    # Await all processing tasks
    for variant_name, task in tasks.items():
        processed_bytes = await task
        key = generate_object_key(f"{prefix}/{variant_name}", original_filename)
        # Override extension to webp since we always convert
        key = key.rsplit(".", 1)[0] + ".webp"
        url = upload_file_to_s3(processed_bytes, key, "image/webp")
        urls[variant_name] = url

    return urls


async def delete_image(url: str) -> None:
    """Delete an image from S3 by its public URL.

    Args:
        url: The full public URL of the image.
    """
    # Extract the key from the URL
    public_prefix = settings.s3_public_url.rstrip("/")
    if url.startswith(public_prefix):
        key = url[len(public_prefix) + 1 :]
        delete_file_from_s3(key)

"""Image upload service with worker pool for processing.

Implements a worker pool pattern with:
- asyncio.Queue for pending image processing jobs
- ProcessPoolExecutor for CPU-bound image manipulation
- Configurable number of workers via IMAGE_WORKER_COUNT env var
- Graceful shutdown on SIGTERM/SIGINT
"""
import asyncio
import io
import logging
import signal
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any

from PIL import Image

from app.core.config import settings
from app.core.storage import (
    delete_file_from_s3,
    generate_object_key,
    get_public_prefix,
    upload_file_to_s3,
)

logger = logging.getLogger(__name__)

# Image size variants as required by the spec
IMAGE_VARIANTS = {
    "thumbnail": {"size": (150, 150), "quality": 80},
    "medium": {"size": (400, 400), "quality": 85},
    "large": {"size": (800, 800), "quality": 90},
}

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE_BYTES = settings.image_max_size_mb * 1024 * 1024

# ── Worker pool globals ──
_executor: ThreadPoolExecutor | None = None
_job_queue: asyncio.Queue[dict[str, Any]] | None = None
_workers: list[asyncio.Task[None]] = []
_shutting_down = False


def _get_executor() -> ThreadPoolExecutor:
    """Get or create the thread pool executor (lazy singleton)."""
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=settings.image_worker_count)
    return _executor


def get_job_queue() -> asyncio.Queue[dict[str, Any]]:
    """Get or create the asyncio job queue (lazy singleton)."""
    global _job_queue
    if _job_queue is None:
        _job_queue = asyncio.Queue()
    return _job_queue


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
    """Process image into variants and upload all to storage.

    Inline implementation: image variants are processed in a thread pool
    (CPU-bound PIL work) and uploaded to GCS in parallel. Cloud Run already
    gives us per-request concurrency, so the previous queue-based worker
    pool added complexity without throughput benefit and was a source of
    "request hangs forever" bugs when the lifespan failed silently.

    Args:
        file_bytes: Raw uploaded file bytes.
        content_type: MIME type of the uploaded file.
        prefix: Storage folder prefix ('logos' or 'dishes').
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

    # 1) Resize variants in parallel (CPU-bound, runs in ThreadPool).
    logger.info(
        "Processing %d variants for %s", len(IMAGE_VARIANTS), original_filename
    )
    processing_tasks = {}
    for variant_name, spec in IMAGE_VARIANTS.items():
        func = partial(
            _process_image_variant,
            file_bytes,
            spec["size"],
            spec["quality"],
        )
        processing_tasks[variant_name] = loop.run_in_executor(executor, func)

    variant_data: dict[str, bytes] = {}
    for name, task in processing_tasks.items():
        variant_data[name] = await task

    # 2) Upload each variant (I/O-bound, runs in default thread pool).
    async def _upload_one(name: str, payload: bytes) -> tuple[str, str]:
        key = generate_object_key(f"{prefix}/{name}", original_filename)
        key = key.rsplit(".", 1)[0] + ".webp"
        url = await loop.run_in_executor(
            None, upload_file_to_s3, payload, key, "image/webp"
        )
        return name, url

    upload_results = await asyncio.gather(
        *[_upload_one(n, b) for n, b in variant_data.items()]
    )
    urls = {name: url for name, url in upload_results}
    logger.info("Uploaded variants for %s: %s", original_filename, list(urls))
    return urls


async def _process_job(job: dict[str, Any]) -> None:
    """Process a single image job from the queue.

    Runs image processing in the ProcessPoolExecutor and uploads results
    in parallel to storage, resolving the job's future with the URLs.
    """
    loop = asyncio.get_event_loop()
    executor = _get_executor()
    future: asyncio.Future[dict[str, str]] = job["future"]
    filename = job["original_filename"]

    try:
        # 1. Process all variants in parallel (CPU-bound)
        logger.info("Generating %d variants for image: %s", len(IMAGE_VARIANTS), filename)
        processing_tasks = {}
        for variant_name, spec in IMAGE_VARIANTS.items():
            func = partial(
                _process_image_variant,
                job["file_bytes"],
                spec["size"],
                spec["quality"],
            )
            processing_tasks[variant_name] = loop.run_in_executor(executor, func)

        # Await all processing to finish
        variant_data = {}
        for name, task in processing_tasks.items():
            variant_data[name] = await task

        # 2. Upload all variants in parallel (I/O-bound)
        logger.info("Uploading variants to storage for: %s", filename)

        async def _upload_task(name: str, p_bytes: bytes) -> tuple[str, str]:
            key = generate_object_key(
                f"{job['prefix']}/{name}", filename
            )
            key = key.rsplit(".", 1)[0] + ".webp"
            # run_in_executor(None, ...) uses the default ThreadPoolExecutor for I/O
            url = await loop.run_in_executor(
                None, upload_file_to_s3, p_bytes, key, "image/webp"
            )
            return name, url

        upload_coros = [
            _upload_task(name, b) for name, b in variant_data.items()
        ]
        upload_results = await asyncio.gather(*upload_coros)
        
        urls = {name: url for name, url in upload_results}
        logger.info("Successfully processed and uploaded: %s", filename)
        future.set_result(urls)

    except Exception as exc:
        logger.exception("Failed to process image job for %s", filename)
        if not future.done():
            future.set_exception(exc)


async def _worker(worker_id: int) -> None:
    """Worker coroutine that pulls jobs from the queue and processes them."""
    queue = get_job_queue()
    logger.info("Image worker %d ready", worker_id)
    while True:
        try:
            job = await queue.get()
            logger.info("Worker %d started processing: %s", worker_id, job["original_filename"])
            await _process_job(job)
            queue.task_done()
        except asyncio.CancelledError:
            logger.info("Image worker %d shutting down", worker_id)
            break
        except Exception:
            logger.exception("Worker %d encountered an error", worker_id)


async def start_workers() -> None:
    """No-op kept for backwards compatibility with the lifespan handler.

    The original worker-pool architecture pulled jobs from an ``asyncio.Queue``
    and resolved a per-job ``Future``. On Cloud Run that pattern is fragile:
    if any startup error keeps workers from spawning (silently failing
    lifespan, ``ConnectorLoopError`` during init, …) every upload request
    hangs forever waiting on a future no one resolves. Cloud Run already
    gives us per-request concurrency, so we now process inline in
    ``process_and_upload_image`` and this function is just a marker.
    """
    logger.info("Worker pool disabled — uploads run inline (Cloud Run concurrency).")


async def shutdown_workers() -> None:
    """Graceful shutdown: wait for pending jobs, cancel workers, shutdown executor."""
    global _shutting_down, _workers, _executor
    if _shutting_down:
        return
    _shutting_down = True
    logger.info("Shutting down image processing workers...")

    # Wait for the queue to drain (with timeout)
    queue = get_job_queue()
    try:
        await asyncio.wait_for(queue.join(), timeout=30.0)
    except asyncio.TimeoutError:
        logger.warning("Timed out waiting for image queue to drain")

    # Cancel worker tasks
    for task in _workers:
        task.cancel()
    if _workers:
        await asyncio.gather(*_workers, return_exceptions=True)
    _workers.clear()

    # Shutdown process pool
    if _executor is not None:
        _executor.shutdown(wait=True)
        _executor = None

    logger.info("Image processing workers shut down")


def install_signal_handlers() -> None:
    """Install SIGTERM/SIGINT handlers for graceful shutdown of the worker pool.

    Should be called after the event loop is running (e.g., in FastAPI startup).
    """
    loop = asyncio.get_event_loop()

    def _handle_signal(sig: signal.Signals) -> None:
        logger.info("Received signal %s, initiating graceful shutdown", sig.name)
        loop.create_task(shutdown_workers())

    try:
        loop.add_signal_handler(signal.SIGTERM, _handle_signal, signal.SIGTERM)
        loop.add_signal_handler(signal.SIGINT, _handle_signal, signal.SIGINT)
        logger.info("Installed SIGTERM/SIGINT signal handlers for worker pool")
    except NotImplementedError:
        # Windows doesn't support add_signal_handler
        logger.debug("Signal handlers not supported on this platform")


async def delete_image(url: str) -> None:
    """Delete an image from object storage by its public URL.

    Works with both the S3/MinIO and the GCS backend by stripping the
    backend's public prefix to recover the object key.
    """
    public_prefix = get_public_prefix().rstrip("/")
    if url.startswith(public_prefix):
        key = url[len(public_prefix) + 1 :]
        delete_file_from_s3(key)
    else:
        logger.warning("delete_image called with foreign URL: %s", url)

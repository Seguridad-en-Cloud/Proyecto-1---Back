"""Upload routes for image management."""
import logging

from fastapi import APIRouter, HTTPException, Query, UploadFile, status

from app.api.deps import CurrentUserId, DatabaseSession
from app.core.storage import get_public_prefix
from app.schemas.upload import DeleteResponse, UploadResponse
from app.services.restaurant_service import RestaurantService
from app.services.upload_service import delete_image, process_and_upload_image

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/upload", tags=["upload"])


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile,
    user_id: CurrentUserId,
    session: DatabaseSession,
    prefix: str = Query(default="dishes", pattern="^(logos|dishes)$"),
):
    """Upload an image and get back URLs for all processed variants.

    The image is validated (type, size), processed into thumbnail/medium/large
    variants, and uploaded to object storage (S3/MinIO).

    Args:
        file: Uploaded image file (JPEG, PNG, WebP; max 5MB).
        user_id: Authenticated user ID.
        session: Database session.
        prefix: Storage folder ('logos' or 'dishes').

    Returns:
        UploadResponse with URLs for each variant.
    """
    # Verify user owns a restaurant (authorization)
    service = RestaurantService(session)
    await service.get_by_owner(user_id)

    file_bytes = await file.read()
    content_type = file.content_type or "application/octet-stream"

    try:
        urls = await process_and_upload_image(
            file_bytes=file_bytes,
            content_type=content_type,
            prefix=prefix,
            original_filename=file.filename or "image.jpg",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return UploadResponse(**urls)


@router.delete("/{filename:path}", response_model=DeleteResponse)
async def delete_uploaded_image(
    filename: str,
    user_id: CurrentUserId = ...,
    session: DatabaseSession = ...,
):
    """Delete a previously uploaded image from object storage.

    Args:
        filename: Object key / path of the image to delete (e.g., 'dishes/large/abc.webp').
        user_id: Authenticated user ID.
        session: Database session.

    Returns:
        Confirmation message.
    """
    # Verify user owns a restaurant (authorization)
    service = RestaurantService(session)
    await service.get_by_owner(user_id)

    # Reconstruct the full URL from the filename to delegate to delete_image
    url = f"{get_public_prefix().rstrip('/')}/{filename}"

    try:
        await delete_image(url)
    except Exception as exc:
        logger.error("Failed to delete image: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete image",
        ) from exc

    return DeleteResponse()

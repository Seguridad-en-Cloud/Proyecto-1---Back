"""Menu routes - Public endpoints."""
import hashlib
import logging

from fastapi import APIRouter, Request

from app.api.deps import DatabaseSession
from app.core.config import settings
from app.models.scan_event import ScanEvent
from app.schemas.menu import MenuResponse
from app.services.menu_service import MenuService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/menu", tags=["menu"])


def _hash_ip(ip: str) -> str:
    """Hash an IP address with salt for privacy."""
    return hashlib.sha256(f"{settings.ip_hash_salt}:{ip}".encode()).hexdigest()


@router.get("/{slug}", response_model=MenuResponse)
async def get_menu(
    slug: str,
    request: Request,
    session: DatabaseSession,
):
    """Get complete menu by restaurant slug.

    This is a public endpoint that returns the full menu structure
    including restaurant information, active categories, and available dishes.
    Records a scan event for analytics.

    Args:
        slug: Restaurant slug (URL-friendly identifier)
        request: FastAPI request
        session: Database session

    Returns:
        MenuResponse: Complete menu with categories and dishes

    Raises:
        HTTPException 404: If restaurant not found
    """
    service = MenuService(session)
    menu = await service.get_menu_by_slug(slug)

    # Record scan event (best-effort, don't fail the request)
    try:
        client_ip = request.client.host if request.client else "unknown"
        event = ScanEvent(
            restaurant_id=menu.restaurant_id,
            user_agent=request.headers.get("user-agent", "unknown"),
            ip_hash=_hash_ip(client_ip),
            referrer=request.headers.get("referer"),
        )
        session.add(event)
        await session.commit()
    except Exception:
        logger.debug("Failed to record scan event", exc_info=True)

    return menu

"""Menu routes - Public endpoints."""
from fastapi import APIRouter

from app.api.deps import DatabaseSession
from app.schemas.menu import MenuResponse
from app.services.menu_service import MenuService

router = APIRouter(prefix="/api/v1/menu", tags=["menu"])


@router.get("/{slug}", response_model=MenuResponse)
async def get_menu(
    slug: str,
    session: DatabaseSession,
):
    """Get complete menu by restaurant slug.
    
    This is a public endpoint that returns the full menu structure
    including restaurant information, active categories, and available dishes.
    
    Args:
        slug: Restaurant slug (URL-friendly identifier)
        session: Database session
        
    Returns:
        MenuResponse: Complete menu with categories and dishes
        
    Raises:
        HTTPException 404: If restaurant not found
    """
    service = MenuService(session)
    menu = await service.get_menu_by_slug(slug)
    return menu

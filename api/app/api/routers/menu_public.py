"""Public menu HTML renderer - Server Side Rendering."""
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.api.deps import DatabaseSession
from app.services.menu_service import MenuService

# Setup templates
templates_dir = Path(__file__).parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

router = APIRouter(tags=["menu-public"])


@router.get("/m/{slug}", response_class=HTMLResponse)
async def render_menu(
    request: Request,
    slug: str,
    session: DatabaseSession,
):
    """Render menu as HTML page (Server Side Rendering).
    
    Public endpoint that returns a fully rendered HTML page with the restaurant's menu.
    This endpoint is designed for direct browser access and QR code scanning.
    
    Args:
        request: FastAPI request object (required for templates)
        slug: Restaurant slug (URL-friendly identifier)
        session: Database session
        
    Returns:
        HTMLResponse: Rendered HTML page with complete menu
        
    Raises:
        HTTPException 404: If restaurant not found
    """
    service = MenuService(session)
    menu = await service.get_menu_by_slug(slug)
    
    # Convert Decimal to float for template rendering
    context = {
        "request": request,
        "restaurant_name": menu.restaurant_name,
        "restaurant_slug": menu.restaurant_slug,
        "description": menu.description,
        "logo_url": menu.logo_url,
        "phone": menu.phone,
        "address": menu.address,
        "hours": menu.hours,
        "categories": [
            {
                "name": cat.name,
                "description": cat.description,
                "position": cat.position,
                "dishes": [
                    {
                        "name": dish.name,
                        "description": dish.description,
                        "price": float(dish.price),
                        "sale_price": float(dish.sale_price) if dish.sale_price else None,
                        "image_url": dish.image_url,
                        "tags": dish.tags,
                        "featured": dish.featured,
                    }
                    for dish in cat.dishes
                ],
            }
            for cat in menu.categories
        ],
    }
    
    return templates.TemplateResponse("menu.html", context)

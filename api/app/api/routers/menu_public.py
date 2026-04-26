"""Public menu HTML renderer - Server Side Rendering."""
import hashlib
import json
import logging
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.api.deps import DatabaseSession
from app.core.config import settings
from app.models.scan_event import ScanEvent
from app.services.menu_service import MenuService

logger = logging.getLogger(__name__)

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

    # Record scan event (best-effort)
    try:
        client_ip = request.client.host if request.client else "unknown"
        ip_hash = hashlib.sha256(f"{settings.ip_hash_salt}:{client_ip}".encode()).hexdigest()
        event = ScanEvent(
            restaurant_id=menu.restaurant_id,
            user_agent=request.headers.get("user-agent", "unknown"),
            ip_hash=ip_hash,
            referrer=request.headers.get("referer"),
        )
        session.add(event)
        await session.commit()
    except Exception:
        logger.debug("Failed to record scan event", exc_info=True)

    # Convert Decimal to float for template rendering - all primitives
    categories_data = []
    for cat in menu.categories:
        dishes_data = []
        for dish in cat.dishes:
            dishes_data.append({
                "id": str(dish.id),
                "name": dish.name,
                "description": dish.description,
                "price": float(dish.price),
                "sale_price": float(dish.sale_price) if dish.sale_price else None,
                "image_url": dish.image_url,
                "tags": dish.tags or [],
                "featured": dish.featured,
                "position": dish.position,
            })
        categories_data.append({
            "id": str(cat.id),
            "name": cat.name,
            "description": cat.description,
            "position": cat.position,
            "dishes": dishes_data,
        })

    # Force all data to be JSON-serializable primitives (no objects)
    # request is passed implicitly by Starlette for template context injection
    context_data = {
        "request": request,
        "restaurant_name": str(menu.restaurant_name) if menu.restaurant_name else "",
        "restaurant_slug": str(menu.restaurant_slug) if menu.restaurant_slug else "",
        "description": str(menu.description) if menu.description else "",
        "logo_url": str(menu.logo_url) if menu.logo_url else "",
        "phone": str(menu.phone) if menu.phone else "",
        "address": str(menu.address) if menu.address else "",
        "hours": json.dumps(menu.hours) if menu.hours else "{}",
        "categories": categories_data,
    }
    
    return templates.TemplateResponse("menu.html", context_data)

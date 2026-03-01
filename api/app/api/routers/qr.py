"""QR code generation routes."""
from fastapi import APIRouter, Query
from fastapi.responses import Response

from app.api.deps import CurrentUserId, DatabaseSession
from app.core.config import settings
from app.services.qr_service import (
    generate_qr_png,
    generate_qr_svg,
    resolve_box_size,
)
from app.services.restaurant_service import RestaurantService

router = APIRouter(prefix="/api/v1/admin/qr", tags=["qr"])


@router.get("")
async def get_qr_code(
    user_id: CurrentUserId,
    session: DatabaseSession,
    format: str = Query(default="png", pattern="^(png|svg)$"),
    size: str = Query(
        default="M",
        pattern="^(S|M|L|XL)$",
        description="QR output size: S (200px), M (400px), L (800px), XL (1200px)",
    ),
    fill_color: str = Query(
        default="black",
        max_length=20,
        description="QR foreground color (hex like '#FF0000' or CSS name like 'black')",
    ),
    back_color: str = Query(
        default="white",
        max_length=20,
        description="QR background color (hex like '#FFFFFF' or CSS name like 'white')",
    ),
):
    """Generate QR code for the authenticated user's restaurant menu.

    The QR encodes the public menu URL (/m/{slug}). The code is static --
    it always points to the same URL, but the menu content updates in real time.

    Supports color customization (RF-20) and named sizes S/M/L/XL (CU-07).

    Args:
        user_id: Authenticated user ID.
        session: Database session.
        format: Output format ('png' or 'svg').
        size: Named size preset (S/M/L/XL).
        fill_color: QR foreground color.
        back_color: QR background color.

    Returns:
        QR code image (PNG or SVG).
    """
    service = RestaurantService(session)
    restaurant = await service.get_by_owner(user_id)

    # Build the public menu URL using configurable base
    base = settings.public_base_url.rstrip("/")
    menu_url = f"{base}/m/{restaurant.slug}"
    box_size = resolve_box_size(size)

    if format == "svg":
        qr_bytes = generate_qr_svg(
            menu_url, box_size=box_size, fill_color=fill_color, back_color=back_color
        )
        return Response(
            content=qr_bytes,
            media_type="image/svg+xml",
            headers={
                "Content-Disposition": f'inline; filename="{restaurant.slug}-qr.svg"'
            },
        )

    qr_bytes = generate_qr_png(
        menu_url, box_size=box_size, fill_color=fill_color, back_color=back_color
    )
    return Response(
        content=qr_bytes,
        media_type="image/png",
        headers={
            "Content-Disposition": f'inline; filename="{restaurant.slug}-qr.png"'
        },
    )

"""Dish routes."""
import uuid
from decimal import Decimal

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUserId, DatabaseSession
from app.schemas.dish import DishCreate, DishListResponse, DishResponse, DishUpdate
from app.services.dish_service import DishService

router = APIRouter(prefix="/api/v1/admin/dishes", tags=["dishes"])


@router.get("", response_model=DishListResponse)
async def list_dishes(
    user_id: CurrentUserId,
    session: DatabaseSession,
    category_id: uuid.UUID | None = Query(default=None),
    available: bool | None = Query(default=None),
    featured: bool | None = Query(default=None),
    q: str | None = Query(default=None, description="Search query"),
    tag: str | None = Query(default=None),
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List dishes with filters and pagination."""
    service = DishService(session)
    return await service.list_dishes(
        owner_user_id=user_id,
        category_id=category_id,
        available=available,
        featured=featured,
        q=q,
        tag=tag,
        min_price=min_price,
        max_price=max_price,
        limit=limit,
        offset=offset,
    )


@router.get("/{id}", response_model=DishResponse)
async def get_dish(
    id: uuid.UUID,
    user_id: CurrentUserId,
    session: DatabaseSession,
):
    """Get a single dish by ID."""
    service = DishService(session)
    dish = await service.get_dish(id, user_id)
    
    return DishResponse(
        id=dish.id,
        category_id=dish.category_id,
        name=dish.name,
        description=dish.description,
        price=dish.price,
        sale_price=dish.sale_price,
        image_url=dish.image_url,
        available=dish.available,
        featured=dish.featured,
        tags=dish.tags,
        position=dish.position,
        created_at=dish.created_at.isoformat(),
        updated_at=dish.updated_at.isoformat(),
        deleted_at=dish.deleted_at.isoformat() if dish.deleted_at else None,
    )


@router.post("", response_model=DishResponse, status_code=status.HTTP_201_CREATED)
async def create_dish(
    data: DishCreate,
    user_id: CurrentUserId,
    session: DatabaseSession,
):
    """Create a new dish."""
    service = DishService(session)
    dish = await service.create(user_id, data)
    
    return DishResponse(
        id=dish.id,
        category_id=dish.category_id,
        name=dish.name,
        description=dish.description,
        price=dish.price,
        sale_price=dish.sale_price,
        image_url=dish.image_url,
        available=dish.available,
        featured=dish.featured,
        tags=dish.tags,
        position=dish.position,
        created_at=dish.created_at.isoformat(),
        updated_at=dish.updated_at.isoformat(),
        deleted_at=dish.deleted_at.isoformat() if dish.deleted_at else None,
    )


@router.put("/{id}", response_model=DishResponse)
async def update_dish(
    id: uuid.UUID,
    data: DishUpdate,
    user_id: CurrentUserId,
    session: DatabaseSession,
):
    """Update a dish."""
    service = DishService(session)
    dish = await service.update(id, user_id, data)
    
    return DishResponse(
        id=dish.id,
        category_id=dish.category_id,
        name=dish.name,
        description=dish.description,
        price=dish.price,
        sale_price=dish.sale_price,
        image_url=dish.image_url,
        available=dish.available,
        featured=dish.featured,
        tags=dish.tags,
        position=dish.position,
        created_at=dish.created_at.isoformat(),
        updated_at=dish.updated_at.isoformat(),
        deleted_at=dish.deleted_at.isoformat() if dish.deleted_at else None,
    )


@router.delete("/{id}", response_model=DishResponse)
async def delete_dish(
    id: uuid.UUID,
    user_id: CurrentUserId,
    session: DatabaseSession,
):
    """Soft delete a dish."""
    service = DishService(session)
    dish = await service.delete(id, user_id)
    
    return DishResponse(
        id=dish.id,
        category_id=dish.category_id,
        name=dish.name,
        description=dish.description,
        price=dish.price,
        sale_price=dish.sale_price,
        image_url=dish.image_url,
        available=dish.available,
        featured=dish.featured,
        tags=dish.tags,
        position=dish.position,
        created_at=dish.created_at.isoformat(),
        updated_at=dish.updated_at.isoformat(),
        deleted_at=dish.deleted_at.isoformat() if dish.deleted_at else None,
    )


@router.patch("/{id}/availability", response_model=DishResponse)
async def toggle_dish_availability(
    id: uuid.UUID,
    user_id: CurrentUserId,
    session: DatabaseSession,
):
    """Toggle dish availability."""
    service = DishService(session)
    dish = await service.toggle_availability(id, user_id)
    
    return DishResponse(
        id=dish.id,
        category_id=dish.category_id,
        name=dish.name,
        description=dish.description,
        price=dish.price,
        sale_price=dish.sale_price,
        image_url=dish.image_url,
        available=dish.available,
        featured=dish.featured,
        tags=dish.tags,
        position=dish.position,
        created_at=dish.created_at.isoformat(),
        updated_at=dish.updated_at.isoformat(),
        deleted_at=dish.deleted_at.isoformat() if dish.deleted_at else None,
    )

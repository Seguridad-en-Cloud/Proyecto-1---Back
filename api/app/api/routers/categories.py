"""Category routes."""
import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentUserId, DatabaseSession
from app.schemas.category import CategoryCreate, CategoryReorderRequest, CategoryResponse, CategoryUpdate
from app.services.category_service import CategoryService

router = APIRouter(prefix="/api/v1/admin/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
async def list_categories(
    user_id: CurrentUserId,
    session: DatabaseSession,
):
    """List all categories for the user's restaurant."""
    service = CategoryService(session)
    categories = await service.list_categories(user_id)
    
    return [
        CategoryResponse(
            id=cat.id,
            restaurant_id=cat.restaurant_id,
            name=cat.name,
            description=cat.description,
            position=cat.position,
            active=cat.active,
            created_at=cat.created_at.isoformat(),
            updated_at=cat.updated_at.isoformat(),
        )
        for cat in categories
    ]


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    user_id: CurrentUserId,
    session: DatabaseSession,
):
    """Create a new category."""
    service = CategoryService(session)
    category = await service.create(user_id, data)
    
    return CategoryResponse(
        id=category.id,
        restaurant_id=category.restaurant_id,
        name=category.name,
        description=category.description,
        position=category.position,
        active=category.active,
        created_at=category.created_at.isoformat(),
        updated_at=category.updated_at.isoformat(),
    )


@router.put("/{id}", response_model=CategoryResponse)
async def update_category(
    id: uuid.UUID,
    data: CategoryUpdate,
    user_id: CurrentUserId,
    session: DatabaseSession,
):
    """Update a category."""
    service = CategoryService(session)
    category = await service.update(id, user_id, data)
    
    return CategoryResponse(
        id=category.id,
        restaurant_id=category.restaurant_id,
        name=category.name,
        description=category.description,
        position=category.position,
        active=category.active,
        created_at=category.created_at.isoformat(),
        updated_at=category.updated_at.isoformat(),
    )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    id: uuid.UUID,
    user_id: CurrentUserId,
    session: DatabaseSession,
):
    """Delete a category."""
    service = CategoryService(session)
    await service.delete(id, user_id)


@router.patch("/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_categories(
    data: CategoryReorderRequest,
    user_id: CurrentUserId,
    session: DatabaseSession,
):
    """Reorder categories."""
    service = CategoryService(session)
    await service.reorder(user_id, data.ordered_ids)

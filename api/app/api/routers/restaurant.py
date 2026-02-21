"""Restaurant routes."""
from fastapi import APIRouter, status

from app.api.deps import CurrentUserId, DatabaseSession
from app.schemas.restaurant import RestaurantCreate, RestaurantResponse, RestaurantUpdate
from app.services.restaurant_service import RestaurantService

router = APIRouter(prefix="/api/v1/admin/restaurant", tags=["restaurant"])


@router.get("", response_model=RestaurantResponse)
async def get_restaurant(
    user_id: CurrentUserId,
    session: DatabaseSession,
):
    """Get restaurant for current user."""
    service = RestaurantService(session)
    restaurant = await service.get_by_owner(user_id)
    
    return RestaurantResponse(
        id=restaurant.id,
        owner_user_id=restaurant.owner_user_id,
        name=restaurant.name,
        slug=restaurant.slug,
        description=restaurant.description,
        logo_url=restaurant.logo_url,
        phone=restaurant.phone,
        address=restaurant.address,
        hours=restaurant.hours,
        created_at=restaurant.created_at.isoformat(),
        updated_at=restaurant.updated_at.isoformat(),
    )


@router.post("", response_model=RestaurantResponse, status_code=status.HTTP_201_CREATED)
async def create_restaurant(
    data: RestaurantCreate,
    user_id: CurrentUserId,
    session: DatabaseSession,
):
    """Create a new restaurant."""
    service = RestaurantService(session)
    restaurant = await service.create(user_id, data)
    
    return RestaurantResponse(
        id=restaurant.id,
        owner_user_id=restaurant.owner_user_id,
        name=restaurant.name,
        slug=restaurant.slug,
        description=restaurant.description,
        logo_url=restaurant.logo_url,
        phone=restaurant.phone,
        address=restaurant.address,
        hours=restaurant.hours,
        created_at=restaurant.created_at.isoformat(),
        updated_at=restaurant.updated_at.isoformat(),
    )


@router.put("", response_model=RestaurantResponse)
async def update_restaurant(
    data: RestaurantUpdate,
    user_id: CurrentUserId,
    session: DatabaseSession,
):
    """Update restaurant."""
    service = RestaurantService(session)
    restaurant = await service.update(user_id, data)
    
    return RestaurantResponse(
        id=restaurant.id,
        owner_user_id=restaurant.owner_user_id,
        name=restaurant.name,
        slug=restaurant.slug,
        description=restaurant.description,
        logo_url=restaurant.logo_url,
        phone=restaurant.phone,
        address=restaurant.address,
        hours=restaurant.hours,
        created_at=restaurant.created_at.isoformat(),
        updated_at=restaurant.updated_at.isoformat(),
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_restaurant(
    user_id: CurrentUserId,
    session: DatabaseSession,
):
    """Delete restaurant."""
    service = RestaurantService(session)
    await service.delete(user_id)

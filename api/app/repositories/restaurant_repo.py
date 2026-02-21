"""Restaurant repository for database operations."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.restaurant import Restaurant


class RestaurantRepository:
    """Repository for Restaurant database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        owner_user_id: uuid.UUID,
        name: str,
        slug: str,
        description: str | None = None,
        logo_url: str | None = None,
        phone: str | None = None,
        address: str | None = None,
        hours: dict | None = None,
    ) -> Restaurant:
        """Create a new restaurant."""
        restaurant = Restaurant(
            owner_user_id=owner_user_id,
            name=name,
            slug=slug,
            description=description,
            logo_url=logo_url,
            phone=phone,
            address=address,
            hours=hours,
        )
        self.session.add(restaurant)
        await self.session.commit()
        await self.session.refresh(restaurant)
        return restaurant
    
    async def get_by_id(self, restaurant_id: uuid.UUID) -> Restaurant | None:
        """Get restaurant by ID."""
        result = await self.session.execute(
            select(Restaurant).where(Restaurant.id == restaurant_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_owner_id(self, owner_user_id: uuid.UUID) -> Restaurant | None:
        """Get restaurant by owner user ID."""
        result = await self.session.execute(
            select(Restaurant).where(Restaurant.owner_user_id == owner_user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_slug(self, slug: str) -> Restaurant | None:
        """Get restaurant by slug."""
        result = await self.session.execute(
            select(Restaurant).where(Restaurant.slug == slug)
        )
        return result.scalar_one_or_none()
    
    async def update(
        self,
        restaurant: Restaurant,
        **kwargs,
    ) -> Restaurant:
        """Update restaurant fields."""
        for key, value in kwargs.items():
            if hasattr(restaurant, key):
                setattr(restaurant, key, value)
        
        await self.session.commit()
        await self.session.refresh(restaurant)
        return restaurant
    
    async def delete(self, restaurant: Restaurant) -> None:
        """Delete a restaurant."""
        await self.session.delete(restaurant)
        await self.session.commit()
    
    async def slug_exists(self, slug: str) -> bool:
        """Check if slug already exists."""
        restaurant = await self.get_by_slug(slug)
        return restaurant is not None

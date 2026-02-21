"""Dish repository for database operations."""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dish import Dish


class DishRepository:
    """Repository for Dish database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        category_id: uuid.UUID,
        name: str,
        price: Decimal,
        description: str | None = None,
        sale_price: Decimal | None = None,
        image_url: str | None = None,
        available: bool = True,
        featured: bool = False,
        tags: list[str] | None = None,
        position: int | None = None,
    ) -> Dish:
        """Create a new dish."""
        if position is None:
            position = await self.get_next_position(category_id)
        
        dish = Dish(
            category_id=category_id,
            name=name,
            description=description,
            price=price,
            sale_price=sale_price,
            image_url=image_url,
            available=available,
            featured=featured,
            tags=tags,
            position=position,
        )
        self.session.add(dish)
        await self.session.commit()
        await self.session.refresh(dish)
        return dish
    
    async def get_by_id(self, dish_id: uuid.UUID, include_deleted: bool = False) -> Dish | None:
        """Get dish by ID."""
        query = select(Dish).where(Dish.id == dish_id)
        
        if not include_deleted:
            query = query.where(Dish.deleted_at.is_(None))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_dishes(
        self,
        category_id: uuid.UUID | None = None,
        available: bool | None = None,
        featured: bool | None = None,
        search_query: str | None = None,
        tag: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        limit: int = 20,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> tuple[list[Dish], int]:
        """List dishes with filters and pagination."""
        query = select(Dish)
        count_query = select(func.count(Dish.id))
        
        # Apply filters
        if not include_deleted:
            query = query.where(Dish.deleted_at.is_(None))
            count_query = count_query.where(Dish.deleted_at.is_(None))
        
        if category_id is not None:
            query = query.where(Dish.category_id == category_id)
            count_query = count_query.where(Dish.category_id == category_id)
        
        if available is not None:
            query = query.where(Dish.available.is_(available))
            count_query = count_query.where(Dish.available.is_(available))
        
        if featured is not None:
            query = query.where(Dish.featured.is_(featured))
            count_query = count_query.where(Dish.featured.is_(featured))
        
        if search_query:
            search_filter = or_(
                Dish.name.ilike(f"%{search_query}%"),
                Dish.description.ilike(f"%{search_query}%"),
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        if tag:
            # PostgreSQL array contains operator
            query = query.where(Dish.tags.contains([tag]))
            count_query = count_query.where(Dish.tags.contains([tag]))
        
        if min_price is not None:
            query = query.where(Dish.price >= min_price)
            count_query = count_query.where(Dish.price >= min_price)
        
        if max_price is not None:
            query = query.where(Dish.price <= max_price)
            count_query = count_query.where(Dish.price <= max_price)
        
        # Get total count
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()
        
        # Apply ordering and pagination
        query = query.order_by(Dish.position.asc(), Dish.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        dishes = list(result.scalars().all())
        
        return dishes, total
    
    async def update(self, dish: Dish, **kwargs) -> Dish:
        """Update dish fields."""
        for key, value in kwargs.items():
            if hasattr(dish, key):
                setattr(dish, key, value)
        
        await self.session.commit()
        await self.session.refresh(dish)
        return dish
    
    async def soft_delete(self, dish: Dish) -> Dish:
        """Soft delete a dish by setting deleted_at timestamp."""
        dish.deleted_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(dish)
        return dish
    
    async def toggle_availability(self, dish: Dish) -> Dish:
        """Toggle dish availability."""
        dish.available = not dish.available
        await self.session.commit()
        await self.session.refresh(dish)
        return dish
    
    async def get_next_position(self, category_id: uuid.UUID) -> int:
        """Get the next available position for a new dish."""
        result = await self.session.execute(
            select(func.max(Dish.position))
            .where(Dish.category_id == category_id)
            .where(Dish.deleted_at.is_(None))
        )
        max_position = result.scalar_one_or_none()
        return (max_position or -1) + 1

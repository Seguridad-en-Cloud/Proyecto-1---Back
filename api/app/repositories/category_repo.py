"""Category repository for database operations."""
import uuid

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


class CategoryRepository:
    """Repository for Category database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        restaurant_id: uuid.UUID,
        name: str,
        description: str | None = None,
        position: int | None = None,
        active: bool = True,
    ) -> Category:
        """Create a new category."""
        # If position not provided, set to end of list
        if position is None:
            position = await self.get_next_position(restaurant_id)
        
        category = Category(
            restaurant_id=restaurant_id,
            name=name,
            description=description,
            position=position,
            active=active,
        )
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category
    
    async def get_by_id(self, category_id: uuid.UUID) -> Category | None:
        """Get category by ID."""
        result = await self.session.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalar_one_or_none()
    
    async def list_by_restaurant(
        self, 
        restaurant_id: uuid.UUID,
        active_only: bool = False
    ) -> list[Category]:
        """List categories for a restaurant, ordered by position."""
        query = select(Category).where(Category.restaurant_id == restaurant_id)
        
        if active_only:
            query = query.where(Category.active.is_(True))
        
        query = query.order_by(Category.position.asc(), Category.created_at.asc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update(self, category: Category, **kwargs) -> Category:
        """Update category fields."""
        for key, value in kwargs.items():
            if hasattr(category, key):
                setattr(category, key, value)
        
        await self.session.commit()
        await self.session.refresh(category)
        return category
    
    async def delete(self, category: Category) -> None:
        """Delete a category."""
        await self.session.delete(category)
        await self.session.commit()
    
    async def has_active_dishes(self, category_id: uuid.UUID) -> bool:
        """Check if category has any active (non-deleted) dishes."""
        from app.models.dish import Dish
        
        result = await self.session.execute(
            select(func.count(Dish.id))
            .where(Dish.category_id == category_id)
            .where(Dish.deleted_at.is_(None))
        )
        count = result.scalar_one()
        return count > 0
    
    async def get_next_position(self, restaurant_id: uuid.UUID) -> int:
        """Get the next available position for a new category."""
        result = await self.session.execute(
            select(func.max(Category.position))
            .where(Category.restaurant_id == restaurant_id)
        )
        max_position = result.scalar_one_or_none()
        return (max_position or -1) + 1
    
    async def reorder_categories(
        self, 
        restaurant_id: uuid.UUID, 
        ordered_ids: list[uuid.UUID]
    ) -> None:
        """Reorder categories based on provided ID list."""
        # Update positions in a single transaction
        for position, category_id in enumerate(ordered_ids):
            await self.session.execute(
                update(Category)
                .where(Category.id == category_id)
                .where(Category.restaurant_id == restaurant_id)
                .values(position=position)
            )
        await self.session.commit()

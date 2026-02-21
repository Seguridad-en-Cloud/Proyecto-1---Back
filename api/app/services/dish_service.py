"""Dish service with business logic."""
import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dish import Dish
from app.repositories.category_repo import CategoryRepository
from app.repositories.dish_repo import DishRepository
from app.repositories.restaurant_repo import RestaurantRepository
from app.schemas.dish import DishCreate, DishListResponse, DishResponse, DishUpdate


class DishService:
    """Service for dish operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = DishRepository(session)
        self.category_repo = CategoryRepository(session)
        self.restaurant_repo = RestaurantRepository(session)
    
    async def _verify_category_ownership(
        self, 
        category_id: uuid.UUID, 
        owner_user_id: uuid.UUID
    ) -> None:
        """Verify that the category belongs to the user's restaurant.
        
        Raises:
            HTTPException: If category not found or not owned by user
        """
        category = await self.category_repo.get_by_id(category_id)
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )
        
        restaurant = await self.restaurant_repo.get_by_id(category.restaurant_id)
        
        if not restaurant or restaurant.owner_user_id != owner_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this category",
            )
    
    async def list_dishes(
        self,
        owner_user_id: uuid.UUID,
        category_id: uuid.UUID | None = None,
        available: bool | None = None,
        featured: bool | None = None,
        q: str | None = None,
        tag: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> DishListResponse:
        """List dishes with filters.
        
        Args:
            owner_user_id: Owner's user ID
            category_id: Filter by category
            available: Filter by availability
            featured: Filter by featured status
            q: Search query for name/description
            tag: Filter by tag
            min_price: Minimum price filter
            max_price: Maximum price filter
            limit: Page size
            offset: Offset for pagination
            
        Returns:
            Paginated dish list
        """
        # Get user's restaurant
        restaurant = await self.restaurant_repo.get_by_owner_id(owner_user_id)
        
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restaurant not found",
            )
        
        # If category_id filter is provided, verify it belongs to the restaurant
        if category_id:
            await self._verify_category_ownership(category_id, owner_user_id)
        
        dishes, total = await self.repo.list_dishes(
            category_id=category_id,
            available=available,
            featured=featured,
            search_query=q,
            tag=tag,
            min_price=min_price,
            max_price=max_price,
            limit=limit,
            offset=offset,
        )
        
        # Convert to response models
        dish_responses = [DishResponse.model_validate(dish) for dish in dishes]
        
        return DishListResponse(
            items=dish_responses,
            total=total,
            limit=limit,
            offset=offset,
        )
    
    async def get_dish(
        self, 
        dish_id: uuid.UUID, 
        owner_user_id: uuid.UUID
    ) -> Dish:
        """Get a single dish by ID.
        
        Args:
            dish_id: Dish ID
            owner_user_id: Owner's user ID
            
        Returns:
            Dish instance
            
        Raises:
            HTTPException: If dish not found or not authorized
        """
        dish = await self.repo.get_by_id(dish_id)
        
        if not dish:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dish not found",
            )
        
        # Verify ownership through category -> restaurant
        await self._verify_category_ownership(dish.category_id, owner_user_id)
        
        return dish
    
    async def create(
        self, 
        owner_user_id: uuid.UUID, 
        data: DishCreate
    ) -> Dish:
        """Create a new dish.
        
        Args:
            owner_user_id: Owner's user ID
            data: Dish creation data
            
        Returns:
            Created dish
        """
        # Verify category ownership
        await self._verify_category_ownership(data.category_id, owner_user_id)
        
        return await self.repo.create(
            category_id=data.category_id,
            name=data.name,
            description=data.description,
            price=data.price,
            sale_price=data.sale_price,
            image_url=data.image_url,
            available=data.available,
            featured=data.featured,
            tags=data.tags,
        )
    
    async def update(
        self,
        dish_id: uuid.UUID,
        owner_user_id: uuid.UUID,
        data: DishUpdate,
    ) -> Dish:
        """Update a dish.
        
        Args:
            dish_id: Dish ID
            owner_user_id: Owner's user ID
            data: Dish update data
            
        Returns:
            Updated dish
        """
        dish = await self.get_dish(dish_id, owner_user_id)
        
        update_data = data.model_dump(exclude_unset=True)
        
        # If category is being changed, verify new category ownership
        if "category_id" in update_data:
            await self._verify_category_ownership(update_data["category_id"], owner_user_id)
        
        return await self.repo.update(dish, **update_data)
    
    async def delete(
        self, 
        dish_id: uuid.UUID, 
        owner_user_id: uuid.UUID
    ) -> Dish:
        """Soft delete a dish.
        
        Args:
            dish_id: Dish ID
            owner_user_id: Owner's user ID
            
        Returns:
            Deleted dish
        """
        dish = await self.get_dish(dish_id, owner_user_id)
        return await self.repo.soft_delete(dish)
    
    async def toggle_availability(
        self, 
        dish_id: uuid.UUID, 
        owner_user_id: uuid.UUID
    ) -> Dish:
        """Toggle dish availability.
        
        Args:
            dish_id: Dish ID
            owner_user_id: Owner's user ID
            
        Returns:
            Updated dish
        """
        dish = await self.get_dish(dish_id, owner_user_id)
        return await self.repo.toggle_availability(dish)

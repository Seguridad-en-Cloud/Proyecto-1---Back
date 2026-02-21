"""Category service with business logic."""
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.repositories.category_repo import CategoryRepository
from app.repositories.restaurant_repo import RestaurantRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    """Service for category operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = CategoryRepository(session)
        self.restaurant_repo = RestaurantRepository(session)
    
    async def _verify_restaurant_ownership(
        self, 
        restaurant_id: uuid.UUID, 
        owner_user_id: uuid.UUID
    ) -> None:
        """Verify that the restaurant belongs to the user.
        
        Raises:
            HTTPException: If restaurant not found or not owned by user
        """
        restaurant = await self.restaurant_repo.get_by_id(restaurant_id)
        
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restaurant not found",
            )
        
        if restaurant.owner_user_id != owner_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this restaurant",
            )
    
    async def list_categories(
        self, 
        owner_user_id: uuid.UUID,
        active_only: bool = False
    ) -> list[Category]:
        """List categories for user's restaurant.
        
        Args:
            owner_user_id: Owner's user ID
            active_only: Only return active categories
            
        Returns:
            List of categories
            
        Raises:
            HTTPException: If restaurant not found
        """
        restaurant = await self.restaurant_repo.get_by_owner_id(owner_user_id)
        
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restaurant not found",
            )
        
        return await self.repo.list_by_restaurant(restaurant.id, active_only)
    
    async def create(
        self, 
        owner_user_id: uuid.UUID, 
        data: CategoryCreate
    ) -> Category:
        """Create a new category.
        
        Args:
            owner_user_id: Owner's user ID
            data: Category creation data
            
        Returns:
            Created category
        """
        restaurant = await self.restaurant_repo.get_by_owner_id(owner_user_id)
        
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restaurant not found",
            )
        
        return await self.repo.create(
            restaurant_id=restaurant.id,
            name=data.name,
            description=data.description,
            active=data.active,
        )
    
    async def update(
        self,
        category_id: uuid.UUID,
        owner_user_id: uuid.UUID,
        data: CategoryUpdate,
    ) -> Category:
        """Update a category.
        
        Args:
            category_id: Category ID
            owner_user_id: Owner's user ID
            data: Category update data
            
        Returns:
            Updated category
            
        Raises:
            HTTPException: If category not found or not authorized
        """
        category = await self.repo.get_by_id(category_id)
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )
        
        # Verify ownership
        await self._verify_restaurant_ownership(category.restaurant_id, owner_user_id)
        
        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update(category, **update_data)
    
    async def delete(
        self, 
        category_id: uuid.UUID, 
        owner_user_id: uuid.UUID
    ) -> None:
        """Delete a category.
        
        Args:
            category_id: Category ID
            owner_user_id: Owner's user ID
            
        Raises:
            HTTPException: If category not found, not authorized, or has active dishes
        """
        category = await self.repo.get_by_id(category_id)
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )
        
        # Verify ownership
        await self._verify_restaurant_ownership(category.restaurant_id, owner_user_id)
        
        # Check if category has active dishes
        if await self.repo.has_active_dishes(category_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete category with active dishes",
            )
        
        await self.repo.delete(category)
    
    async def reorder(
        self,
        owner_user_id: uuid.UUID,
        ordered_ids: list[uuid.UUID],
    ) -> None:
        """Reorder categories.
        
        Args:
            owner_user_id: Owner's user ID
            ordered_ids: List of category IDs in new order
            
        Raises:
            HTTPException: If restaurant not found or categories don't belong to restaurant
        """
        restaurant = await self.restaurant_repo.get_by_owner_id(owner_user_id)
        
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restaurant not found",
            )
        
        # Verify all categories belong to the restaurant
        for category_id in ordered_ids:
            category = await self.repo.get_by_id(category_id)
            if not category or category.restaurant_id != restaurant.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category {category_id} does not belong to restaurant",
                )
        
        await self.repo.reorder_categories(restaurant.id, ordered_ids)

"""Restaurant service with business logic."""
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.restaurant import Restaurant
from app.repositories.restaurant_repo import RestaurantRepository
from app.schemas.restaurant import RestaurantCreate, RestaurantUpdate
from app.utils.slug import generate_slug, make_unique_slug


class RestaurantService:
    """Service for restaurant operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = RestaurantRepository(session)
    
    async def get_by_owner(self, owner_user_id: uuid.UUID) -> Restaurant:
        """Get restaurant by owner user ID.
        
        Args:
            owner_user_id: Owner's user ID
            
        Returns:
            Restaurant instance
            
        Raises:
            HTTPException: If restaurant not found
        """
        restaurant = await self.repo.get_by_owner_id(owner_user_id)
        
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restaurant not found",
            )
        
        return restaurant
    
    async def create(
        self, 
        owner_user_id: uuid.UUID, 
        data: RestaurantCreate
    ) -> Restaurant:
        """Create a new restaurant.
        
        Args:
            owner_user_id: Owner's user ID
            data: Restaurant creation data
            
        Returns:
            Created restaurant
            
        Raises:
            HTTPException: If user already has a restaurant
        """
        # Check if user already has a restaurant
        existing = await self.repo.get_by_owner_id(owner_user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already has a restaurant",
            )
        
        # Generate unique slug
        base_slug = generate_slug(data.name)
        slug = await self._ensure_unique_slug(base_slug)
        
        # Create restaurant
        restaurant = await self.repo.create(
            owner_user_id=owner_user_id,
            name=data.name,
            slug=slug,
            description=data.description,
            logo_url=data.logo_url,
            phone=data.phone,
            address=data.address,
            hours=data.hours,
        )
        
        return restaurant
    
    async def update(
        self, 
        owner_user_id: uuid.UUID, 
        data: RestaurantUpdate
    ) -> Restaurant:
        """Update restaurant.
        
        Args:
            owner_user_id: Owner's user ID
            data: Restaurant update data
            
        Returns:
            Updated restaurant
            
        Raises:
            HTTPException: If restaurant not found
        """
        restaurant = await self.get_by_owner(owner_user_id)
        
        update_data = data.model_dump(exclude_unset=True)
        
        # If name is updated, regenerate slug
        if "name" in update_data:
            base_slug = generate_slug(update_data["name"])
            # Exclude current restaurant's slug from uniqueness check
            slug = await self._ensure_unique_slug(base_slug, exclude_id=restaurant.id)
            update_data["slug"] = slug
        
        restaurant = await self.repo.update(restaurant, **update_data)
        return restaurant
    
    async def delete(self, owner_user_id: uuid.UUID) -> None:
        """Delete restaurant.
        
        Args:
            owner_user_id: Owner's user ID
            
        Raises:
            HTTPException: If restaurant not found
        """
        restaurant = await self.get_by_owner(owner_user_id)
        await self.repo.delete(restaurant)
    
    async def _ensure_unique_slug(
        self, 
        base_slug: str,
        exclude_id: uuid.UUID | None = None
    ) -> str:
        """Ensure slug is unique.
        
        Args:
            base_slug: Base slug to make unique
            exclude_id: Restaurant ID to exclude from check (for updates)
            
        Returns:
            Unique slug
        """
        existing = await self.repo.get_by_slug(base_slug)
        
        # If no existing or it's the same restaurant being updated
        if not existing or (exclude_id and existing.id == exclude_id):
            return base_slug
        
        # Generate unique slug with suffix
        counter = 1
        while True:
            candidate = f"{base_slug}-{counter}"
            existing = await self.repo.get_by_slug(candidate)
            if not existing or (exclude_id and existing.id == exclude_id):
                return candidate
            counter += 1

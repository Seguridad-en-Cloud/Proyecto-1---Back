"""Menu service with business logic and in-memory cache."""
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.core.cache import cache_get, cache_set
from app.models.category import Category
from app.repositories.restaurant_repo import RestaurantRepository
from app.schemas.menu import MenuCategoryResponse, MenuDishResponse, MenuResponse

MENU_CACHE_TTL = 300  # 5 minutes


class MenuService:
    """Service for public menu operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = RestaurantRepository(session)
    
    async def get_menu_by_slug(self, slug: str) -> MenuResponse:
        """Get complete menu by restaurant slug (with cache).
        
        Args:
            slug: Restaurant slug
            
        Returns:
            MenuResponse with restaurant info, categories and dishes
            
        Raises:
            HTTPException: If restaurant not found
        """
        # Check cache first
        cache_key = f"menu:{slug}"
        cached = cache_get(cache_key)
        if cached is not None:
            return cached

        # Get restaurant by slug
        restaurant = await self.repo.get_by_slug(slug)
        
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Restaurant with slug '{slug}' not found",
            )
        
        # Get active categories with their dishes, ordered by position
        query = (
            select(Category)
            .where(Category.restaurant_id == restaurant.id)
            .where(Category.active.is_(True))
            .options(selectinload(Category.dishes))
            .order_by(Category.position.asc(), Category.created_at.asc())
        )
        
        result = await self.session.execute(query)
        categories = result.scalars().all()
        
        # Build category responses with filtered dishes
        category_responses = []
        for category in categories:
            # Filter only available, non-deleted dishes, ordered by position
            available_dishes = [
                dish for dish in category.dishes
                if dish.available and dish.deleted_at is None
            ]
            available_dishes.sort(key=lambda d: (d.position, d.created_at))
            
            # Map dishes to response model
            dish_responses = [
                MenuDishResponse(
                    id=dish.id,
                    name=dish.name,
                    description=dish.description,
                    price=dish.price,
                    sale_price=dish.sale_price,
                    image_url=dish.image_url,
                    tags=dish.tags,
                    featured=dish.featured,
                    position=dish.position,
                )
                for dish in available_dishes
            ]
            
            # Only include categories that have at least one available dish
            if dish_responses:
                category_responses.append(
                    MenuCategoryResponse(
                        id=category.id,
                        name=category.name,
                        description=category.description,
                        position=category.position,
                        dishes=dish_responses,
                    )
                )
        
        # Build and return menu response
        menu_response = MenuResponse(
            restaurant_id=restaurant.id,
            restaurant_name=restaurant.name,
            restaurant_slug=restaurant.slug,
            description=restaurant.description,
            logo_url=restaurant.logo_url,
            phone=restaurant.phone,
            address=restaurant.address,
            hours=restaurant.hours,
            categories=category_responses,
        )

        # Store in cache
        cache_set(cache_key, menu_response, ttl=MENU_CACHE_TTL)

        return menu_response

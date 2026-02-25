"""Menu schemas."""
import uuid
from decimal import Decimal

from pydantic import BaseModel


class MenuDishResponse(BaseModel):
    """Dish response for public menu."""
    
    id: uuid.UUID
    name: str
    description: str | None
    price: Decimal
    sale_price: Decimal | None
    image_url: str | None
    tags: list[str] | None
    featured: bool
    position: int
    
    model_config = {"from_attributes": True}


class MenuCategoryResponse(BaseModel):
    """Category response for public menu with dishes."""
    
    id: uuid.UUID
    name: str
    description: str | None
    position: int
    dishes: list[MenuDishResponse]
    
    model_config = {"from_attributes": True}


class MenuResponse(BaseModel):
    """Complete menu response."""
    
    restaurant_id: uuid.UUID
    restaurant_name: str
    restaurant_slug: str
    description: str | None
    logo_url: str | None
    phone: str | None
    address: str | None
    hours: dict | None
    categories: list[MenuCategoryResponse]

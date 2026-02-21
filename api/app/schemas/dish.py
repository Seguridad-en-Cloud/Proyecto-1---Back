"""Dish schemas."""
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.utils.pagination import PaginatedResponse


class DishCreate(BaseModel):
    """Dish creation request."""
    
    category_id: uuid.UUID
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=300)
    price: Decimal = Field(gt=0, decimal_places=2)
    sale_price: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    image_url: str | None = None
    available: bool = True
    featured: bool = False
    tags: list[str] | None = None


class DishUpdate(BaseModel):
    """Dish update request."""
    
    category_id: uuid.UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=300)
    price: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    sale_price: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    image_url: str | None = None
    available: bool | None = None
    featured: bool | None = None
    tags: list[str] | None = None
    position: int | None = None


class DishResponse(BaseModel):
    """Dish response model."""
    
    id: uuid.UUID
    category_id: uuid.UUID
    name: str
    description: str | None
    price: Decimal
    sale_price: Decimal | None
    image_url: str | None
    available: bool
    featured: bool
    tags: list[str] | None
    position: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    
    model_config = {"from_attributes": True}


class DishListResponse(PaginatedResponse[DishResponse]):
    """Paginated dish list response."""
    pass

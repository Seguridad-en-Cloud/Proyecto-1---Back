"""Restaurant schemas."""
import uuid
from typing import Any

from pydantic import BaseModel, Field


class RestaurantCreate(BaseModel):
    """Restaurant creation request."""
    
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    logo_url: str | None = None
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = None
    hours: dict[str, Any] | None = None


class RestaurantUpdate(BaseModel):
    """Restaurant update request."""
    
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    logo_url: str | None = None
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = None
    hours: dict[str, Any] | None = None


class RestaurantResponse(BaseModel):
    """Restaurant response model."""
    
    id: uuid.UUID
    owner_user_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    logo_url: str | None
    phone: str | None
    address: str | None
    hours: dict[str, Any] | None
    created_at: str
    updated_at: str
    
    model_config = {"from_attributes": True}

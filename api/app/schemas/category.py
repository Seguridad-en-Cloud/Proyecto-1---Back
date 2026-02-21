"""Category schemas."""
import uuid

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    """Category creation request."""
    
    name: str = Field(min_length=1, max_length=50)
    description: str | None = None
    active: bool = True


class CategoryUpdate(BaseModel):
    """Category update request."""
    
    name: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = None
    active: bool | None = None
    position: int | None = None


class CategoryReorderRequest(BaseModel):
    """Category reorder request."""
    
    ordered_ids: list[uuid.UUID] = Field(min_length=1)


class CategoryResponse(BaseModel):
    """Category response model."""
    
    id: uuid.UUID
    restaurant_id: uuid.UUID
    name: str
    description: str | None
    position: int
    active: bool
    created_at: str
    updated_at: str
    
    model_config = {"from_attributes": True}

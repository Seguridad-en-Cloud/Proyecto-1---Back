"""Pagination utilities."""
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model."""
    
    items: list[T]
    total: int
    limit: int
    offset: int
    
    @property
    def has_more(self) -> bool:
        """Check if there are more items beyond the current page."""
        return (self.offset + self.limit) < self.total
    
    @property
    def page(self) -> int:
        """Current page number (1-indexed)."""
        if self.limit == 0:
            return 1
        return (self.offset // self.limit) + 1
    
    @property
    def total_pages(self) -> int:
        """Total number of pages."""
        if self.limit == 0:
            return 1
        return (self.total + self.limit - 1) // self.limit

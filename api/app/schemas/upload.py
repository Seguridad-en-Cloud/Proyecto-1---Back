"""Upload schemas."""
from pydantic import BaseModel


class UploadResponse(BaseModel):
    """Response after successful image upload."""

    thumbnail: str
    medium: str
    large: str


class DeleteResponse(BaseModel):
    """Response after successful image deletion."""

    detail: str = "Image deleted successfully"

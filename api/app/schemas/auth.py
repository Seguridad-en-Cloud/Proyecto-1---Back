"""Authentication schemas."""
import re
import uuid
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """User registration request."""
    
    email: EmailStr
    password: Annotated[str, Field(min_length=8)]
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password has at least 1 letter and 1 number."""
        if not re.search(r"[a-zA-Z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v


class LoginRequest(BaseModel):
    """User login request."""
    
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Token refresh request."""
    
    refresh_token: str


class TokenResponse(BaseModel):
    """Token response with access and refresh tokens."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    """Authentication response with user info and tokens."""
    
    user: "UserResponse"
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User response model."""
    
    id: uuid.UUID
    email: str
    created_at: str
    
    model_config = {"from_attributes": True}

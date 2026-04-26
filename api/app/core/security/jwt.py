"""JWT token creation and validation utilities."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings


def create_access_token(user_id: uuid.UUID, email: str) -> str:
    """Create a JWT access token.

    Args:
        user_id: User's UUID
        email: User's email

    Returns:
        Encoded JWT token
    """
    now = datetime.now(timezone.utc)
    expires_delta = timedelta(minutes=settings.jwt_access_ttl_min)
    
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": "access",
        "iat": now,
        "nbf": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),  # Unique JWT ID
    }
    
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: uuid.UUID, email: str) -> str:
    """Create a JWT refresh token.
    
    Args:
        user_id: User's UUID
        email: User's email
        
    Returns:
        Encoded JWT token
    """
    now = datetime.now(timezone.utc)
    expires_delta = timedelta(days=settings.jwt_refresh_ttl_days)
    
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": "refresh",
        "iat": now,
        "nbf": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),  # Unique JWT ID to prevent duplicates
    }
    
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token.
    
    Args:
        token: JWT token to decode
        
    Returns:
        Token payload as dictionary
        
    Raises:
        JWTError: If token is invalid, expired, or malformed
    """
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def verify_access_token(token: str) -> dict[str, Any]:
    """Verify an access token and return its payload.
    
    Args:
        token: JWT access token
        
    Returns:
        Token payload
        
    Raises:
        JWTError: If token is invalid or not an access token
    """
    payload = decode_token(token)
    
    if payload.get("type") != "access":
        raise JWTError("Invalid token type")
    
    return payload


def verify_refresh_token(token: str) -> dict[str, Any]:
    """Verify a refresh token and return its payload.
    
    Args:
        token: JWT refresh token
        
    Returns:
        Token payload
        
    Raises:
        JWTError: If token is invalid or not a refresh token
    """
    payload = decode_token(token)
    
    if payload.get("type") != "refresh":
        raise JWTError("Invalid token type")
    
    return payload

"""API dependencies for dependency injection."""
import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.jwt import verify_access_token
from database.session import get_session

# Security scheme for Bearer token
security = HTTPBearer()


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> uuid.UUID:
    """Get current user ID from JWT access token.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        User UUID
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    try:
        payload = verify_access_token(token)
        user_id = uuid.UUID(payload["sub"])
        return user_id
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token_expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# Type aliases for cleaner dependency injection
CurrentUserId = Annotated[uuid.UUID, Depends(get_current_user_id)]
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]

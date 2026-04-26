"""Authentication service with business logic."""
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security.jwt import create_access_token, create_refresh_token, verify_refresh_token
from app.core.security.passwords import hash_password, verify_password
from app.models.user import User
from app.repositories.refresh_token_repo import RefreshTokenRepository
from app.repositories.user_repo import UserRepository


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.refresh_token_repo = RefreshTokenRepository(session)
    
    async def register(self, email: str, password: str) -> tuple[User, str, str]:
        """Register a new user.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Tuple of (user, access_token, refresh_token)
            
        Raises:
            HTTPException: If email already exists
        """
        # Check if user already exists
        if await self.user_repo.exists_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        
        # Hash password and create user
        password_hash = hash_password(password)
        user = await self.user_repo.create(email=email, password_hash=password_hash)
        
        # Generate tokens
        access_token = create_access_token(user.id, user.email)
        refresh_token = create_refresh_token(user.id, user.email)
        
        # Store refresh token in database
        await self.refresh_token_repo.create(
            user_id=user.id,
            token=refresh_token,
            expires_in_days=settings.jwt_refresh_ttl_days,
        )
        
        return user, access_token, refresh_token
    
    async def login(self, email: str, password: str) -> tuple[User, str, str]:
        """Authenticate user and return tokens.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Tuple of (user, access_token, refresh_token)
            
        Raises:
            HTTPException: If credentials are invalid
        """
        user = await self.user_repo.get_by_email(email)
        
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        
        # Generate tokens
        access_token = create_access_token(user.id, user.email)
        refresh_token = create_refresh_token(user.id, user.email)
        
        # Store refresh token in database
        await self.refresh_token_repo.create(
            user_id=user.id,
            token=refresh_token,
            expires_in_days=settings.jwt_refresh_ttl_days,
        )
        
        return user, access_token, refresh_token
    
    async def refresh(self, refresh_token: str) -> tuple[str, str]:
        """Refresh access token using refresh token.
        
        Args:
            refresh_token: Current refresh token
            
        Returns:
            Tuple of (new_access_token, new_refresh_token)
            
        Raises:
            HTTPException: If refresh token is invalid or expired
        """
        try:
            # Verify JWT
            payload = verify_refresh_token(refresh_token)
            user_id = uuid.UUID(payload["sub"])
            email = payload["email"]
            
            # Check if token is valid in database
            if not await self.refresh_token_repo.is_valid(refresh_token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired refresh token",
                )
            
            # Revoke old refresh token (token rotation)
            await self.refresh_token_repo.revoke(refresh_token)
            
            # Generate new tokens
            new_access_token = create_access_token(user_id, email)
            new_refresh_token = create_refresh_token(user_id, email)
            
            # Store new refresh token
            await self.refresh_token_repo.create(
                user_id=user_id,
                token=new_refresh_token,
                expires_in_days=settings.jwt_refresh_ttl_days,
            )
            
            return new_access_token, new_refresh_token
            
        except HTTPException:
            raise
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            ) from err
    
    async def logout(self, user_id: uuid.UUID) -> None:
        """Logout user by revoking all refresh tokens.
        
        Args:
            user_id: User ID to logout
        """
        await self.refresh_token_repo.revoke_all_for_user(user_id)

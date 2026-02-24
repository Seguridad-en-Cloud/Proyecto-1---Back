"""Refresh token repository for database operations."""
import hashlib
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    """Repository for RefreshToken database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a refresh token using SHA256."""
        return hashlib.sha256(token.encode()).hexdigest()
    
    async def create(
        self,
        user_id: uuid.UUID,
        token: str,
        expires_in_days: int,
    ) -> RefreshToken:
        """Create a new refresh token record."""
        token_hash = self.hash_token(token)
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(refresh_token)
        await self.session.commit()
        await self.session.refresh(refresh_token)
        return refresh_token
    
    async def get_by_token(self, token: str) -> RefreshToken | None:
        """Get refresh token by the actual token value."""
        token_hash = self.hash_token(token)
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()
    
    async def is_valid(self, token: str) -> bool:
        """Check if a refresh token is valid (exists, not revoked, not expired)."""
        refresh_token = await self.get_by_token(token)
        
        if not refresh_token:
            return False
        
        if refresh_token.revoked_at is not None:
            return False
        
        if refresh_token.expires_at < datetime.utcnow():
            return False
        
        return True
    
    async def revoke(self, token: str) -> None:
        """Revoke a refresh token."""
        refresh_token = await self.get_by_token(token)
        if refresh_token:
            refresh_token.revoked_at = datetime.utcnow()
            await self.session.commit()
    
    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        """Revoke all active refresh tokens for a user."""
        result = await self.session.execute(
            select(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.revoked_at.is_(None))
        )
        tokens = result.scalars().all()
        
        now = datetime.utcnow()
        for token in tokens:
            token.revoked_at = now
        
        await self.session.commit()

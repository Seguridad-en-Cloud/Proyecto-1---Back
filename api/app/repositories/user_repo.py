"""User repository for database operations."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Repository for User database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, email: str, password_hash: str) -> User:
        """Create a new user."""
        user = User(email=email.lower(), password_hash=password_hash)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> User | None:
        """Get user by email (case-insensitive)."""
        result = await self.session.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()
    
    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists with given email."""
        user = await self.get_by_email(email)
        return user is not None

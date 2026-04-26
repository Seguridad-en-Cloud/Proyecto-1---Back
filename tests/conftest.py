"""Pytest configuration and fixtures."""
import asyncio
from typing import AsyncGenerator
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from database.base import Base
from database.session import get_session
from app.main import app

# Test database URL (use in-memory SQLite or separate test database)
TEST_DATABASE_URL = "postgresql+asyncpg://livemenu:livemenu@localhost:5432/livemenu_test"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
)

# Create test session factory
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session (keep it open during the test)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        await session.close()
        # Drop tables after test
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database session override."""
    
    async def override_get_session():
        yield db_session
    
    app.dependency_overrides[get_session] = override_get_session
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Create authenticated user and return auth headers."""
    # Register user
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 201
    
    data = response.json()
    access_token = data["access_token"]
    
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(autouse=True)
def reset_storage_backend():
    """Reset and mock storage backend to avoid connecting to MinIO/GCS."""
    import app.core.storage
    
    # Reset the global _backend variable
    app.core.storage._backend = None
    
    # Create mock backend
    mock_backend = MagicMock()
    mock_backend.upload.return_value = "http://mock-storage/bucket/test-image.webp"
    mock_backend.delete.return_value = None
    mock_backend.public_prefix.return_value = "http://mock-storage/bucket"
    
    with patch("app.core.storage.get_storage", return_value=mock_backend):
        yield mock_backend
    
    # Reset again after test
    app.core.storage._backend = None

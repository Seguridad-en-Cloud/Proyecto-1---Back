"""Database session configuration for async SQLAlchemy.

Two modes:

* **Local / dev** – use ``DATABASE_URL`` directly (dsn-based, asyncpg driver).
* **Cloud SQL** – when ``CLOUD_SQL_CONNECTION_NAME`` is set, the engine is
  built using the official ``cloud-sql-python-connector`` so that traffic
  flows over an encrypted Google-managed channel and authenticates via the
  service account assigned to the Cloud Run revision (IAM auth optional).
  Credentials live in Secret Manager — never in the connection string.
"""
from __future__ import annotations

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, AsyncEngine, create_async_engine

from app.core.config import settings
from app.core.secrets import get_secret

logger = logging.getLogger(__name__)

engine: AsyncEngine | None = None
AsyncSessionLocal: async_sessionmaker | None = None
_connector = None

async def _init_db_if_needed():
    global engine, AsyncSessionLocal, _connector
    if engine is not None:
        return

    db_user = settings.db_user or get_secret("DB_USER") or "livemenu"
    db_pass = get_secret("DB_PASSWORD") or ""
    db_name = settings.db_name or get_secret("DB_NAME") or "livemenu"

    if settings.cloud_sql_connection_name:
        try:
            from google.cloud.sql.connector import create_async_connector, IPTypes  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "CLOUD_SQL_CONNECTION_NAME is set but cloud-sql-python-connector "
                "is not installed."
            ) from exc

        _connector = await create_async_connector()

        async def _getconn():
            return await _connector.connect_async(
                settings.cloud_sql_connection_name,
                "asyncpg",
                user=db_user,
                password=db_pass,
                db=db_name,
                ip_type=IPTypes.PRIVATE,
            )

        engine = create_async_engine(
            "postgresql+asyncpg://",
            async_creator=_getconn,
            echo=settings.debug,
            pool_size=5,
            max_overflow=2,
            pool_recycle=1800,
        )
    else:
        # Local development
        engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
        )

    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

async def close_connector():
    """Close the Cloud SQL Connector cleanly."""
    global engine, _connector
    if engine:
        await engine.dispose()
    if _connector:
        await _connector.close()

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a managed async session."""
    await _init_db_if_needed()
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized")
        
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

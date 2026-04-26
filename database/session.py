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

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.secrets import get_secret

logger = logging.getLogger(__name__)


def _build_engine():
    """Build the async SQLAlchemy engine.

    When ``CLOUD_SQL_CONNECTION_NAME`` is configured we delegate connection
    establishment to the Cloud SQL Connector (TLS + IAM-aware), otherwise we
    fall back to the regular DSN-based engine for docker-compose / dev.
    """
    if settings.cloud_sql_connection_name:
        return _build_cloud_sql_engine()
    return create_async_engine(
        str(settings.database_url),
        echo=settings.debug,
        future=True,
        pool_pre_ping=True,
    )


def _build_cloud_sql_engine():
    """Build an engine that talks to Cloud SQL through the official connector."""
    try:
        from google.cloud.sql.connector import Connector, IPTypes  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "CLOUD_SQL_CONNECTION_NAME is set but cloud-sql-python-connector "
            "is not installed. Add 'cloud-sql-python-connector[asyncpg]' to "
            "requirements."
        ) from exc

    connector = Connector(refresh_strategy="lazy")

    db_user = settings.db_user or get_secret("DB_USER") or "livemenu"
    db_pass = get_secret("DB_PASSWORD") or ""
    db_name = settings.db_name or get_secret("DB_NAME") or "livemenu"

    async def _getconn():
        return await connector.connect_async(
            settings.cloud_sql_connection_name,
            "asyncpg",
            user=db_user,
            password=db_pass,
            db=db_name,
            ip_type=IPTypes.PRIVATE,  # routed through the VPC, not over the public internet
        )

    return create_async_engine(
        "postgresql+asyncpg://",
        async_creator=_getconn,
        echo=settings.debug,
        future=True,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=2,
        pool_recycle=1800,
    )


engine = _build_engine()

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a managed async session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

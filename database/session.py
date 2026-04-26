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

import asyncio
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
    """Build an engine that talks to Cloud SQL through the official connector.

    The ``Connector`` instance MUST be constructed in the same event loop that
    will later call ``connect_async()`` — the connector captures the loop on
    ``__init__`` and refuses requests from any other loop. If we built it at
    module-import time, it would attach to whatever default loop existed
    before uvicorn started; the first real request would then fail with::

        google.cloud.sql.connector.exceptions.ConnectorLoopError:
        Running event loop does not match 'connector._loop'.

    To avoid that, we build the connector lazily inside ``_getconn``, which
    SQLAlchemy invokes from the running uvicorn loop on first connection
    request and reuses thereafter.
    """
    try:
        from google.cloud.sql.connector import Connector, IPTypes  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "CLOUD_SQL_CONNECTION_NAME is set but cloud-sql-python-connector "
            "is not installed. Add 'cloud-sql-python-connector[asyncpg]' to "
            "requirements."
        ) from exc

    db_user = settings.db_user or get_secret("DB_USER") or "livemenu"
    db_pass = get_secret("DB_PASSWORD") or ""
    db_name = settings.db_name or get_secret("DB_NAME") or "livemenu"

    global _connector
    _connector = None

    async def _getconn():
        global _connector
        if _connector is None:
            # Initialize exactly once, in the active uvicorn event loop.
            _connector = Connector()
            
        return await _connector.connect_async(
            settings.cloud_sql_connection_name,
            "asyncpg",
            user=db_user,
            password=db_pass,
            db=db_name,
            ip_type=IPTypes.PRIVATE,
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

"""Scan event model for analytics."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from app.utils.datetime_utils import utcnow

if TYPE_CHECKING:
    from app.models.restaurant import Restaurant


class ScanEvent(Base):
    """QR code scan event model for analytics tracking."""
    
    __tablename__ = "scan_events"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
        index=True
    )
    user_agent: Mapped[str] = mapped_column(Text, nullable=False)
    ip_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA256 hash
    referrer: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Relationships
    restaurant: Mapped[Restaurant] = relationship("Restaurant", back_populates="scan_events")

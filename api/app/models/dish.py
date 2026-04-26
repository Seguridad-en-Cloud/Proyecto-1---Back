"""Dish model."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from app.utils.datetime_utils import utcnow

if TYPE_CHECKING:
    from app.models.category import Category


class Dish(Base):
    """Menu dish/item model."""
    
    __tablename__ = "dishes"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(300), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    sale_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )
    
    # Relationships
    category: Mapped[Category] = relationship("Category", back_populates="dishes")

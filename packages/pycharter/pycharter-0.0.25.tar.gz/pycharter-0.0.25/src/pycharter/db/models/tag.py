"""
SQLAlchemy model for tags table.

Represents tags for flexible categorization.
"""

import uuid

from sqlalchemy import Column, DateTime, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from pycharter.db.models.base import Base


class TagModel(Base):
    """Represents tags for flexible categorization."""

    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # e.g., "classification", "department", "technology"
    color = Column(String(7), nullable=True)  # Hex color code for UI
    additional_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("name", name="uq_tags_name"),
        {"schema": "pycharter"},
    )

    # Relationships
    data_contracts = relationship(
        "DataContractTag", back_populates="tag", cascade="all, delete-orphan"
    )

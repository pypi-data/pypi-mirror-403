"""
SQLAlchemy model for data_feeds table.

Represents operational data feeds.
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from pycharter.db.models.base import Base


class DataFeedModel(Base):
    """Represents operational data feeds."""

    __tablename__ = "data_feeds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    title = Column(String(255), nullable=True)
    feed_type = Column(String(50), nullable=True)  # e.g., "operational", "batch", "streaming"
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    additional_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("name", name="uq_data_feeds_name"),
        {"schema": "pycharter"},
    )

    # Relationships
    metadata_records = relationship(
        "MetadataRecordDataFeed", back_populates="data_feed", cascade="all, delete-orphan"
    )

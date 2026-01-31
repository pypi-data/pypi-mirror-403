"""
SQLAlchemy model for api_endpoints table.

Represents API endpoints for data access.
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from pycharter.db.models.base import Base


class APIEndpointModel(Base):
    """Represents API endpoints for data access."""

    __tablename__ = "api_endpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    path = Column(String(500), nullable=False)  # e.g., "/v1/aircraft-configuration"
    method = Column(String(10), nullable=False)  # e.g., "GET", "POST"
    metadata_record_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.metadata_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    rate_limit = Column(String(50), nullable=True)  # e.g., "120/min"
    cache_ttl = Column(Integer, nullable=True)  # Cache TTL in seconds
    documentation_url = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    additional_metadata = Column(JSON, nullable=True)  # Additional API config

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("path", "method", "metadata_record_id", name="uq_api_endpoints"),
        {"schema": "pycharter"},
    )

    # Relationships
    metadata_record = relationship("MetadataRecordModel", back_populates="api_endpoints")

"""
SQLAlchemy model for environments table.

Represents deployment environments for data contracts.
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from pycharter.db.models.base import Base


class EnvironmentModel(Base):
    """Represents deployment environments for data contracts."""

    __tablename__ = "environments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(
        String(50), nullable=False, unique=True
    )  # e.g., "production", "staging", "development"
    description = Column(Text, nullable=True)
    environment_type = Column(String(50), nullable=True)  # e.g., "production", "non_production"
    is_production = Column(Boolean, nullable=False, default=False)
    additional_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("name", name="uq_environments_name"),
        {"schema": "pycharter"},
    )

    # Relationships
    metadata_records = relationship(
        "MetadataRecordEnvironment", back_populates="environment", cascade="all, delete-orphan"
    )

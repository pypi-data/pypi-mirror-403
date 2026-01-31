"""
SQLAlchemy model for storage_locations table.

Represents physical storage locations for data.
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from pycharter.db.models.base import Base


class StorageLocationModel(Base):
    """Represents physical storage locations for data."""

    __tablename__ = "storage_locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    location_type = Column(
        String(50), nullable=True
    )  # e.g., "database", "data_lake", "warehouse", "object_storage"
    cluster = Column(String(255), nullable=True)  # e.g., "ioc-de-prod"
    database = Column(String(255), nullable=True)
    collection = Column(String(255), nullable=True)  # For MongoDB/NoSQL
    schema_name = Column(String(255), nullable=True)  # For SQL databases
    table_name = Column(String(255), nullable=True)
    connection_string = Column(Text, nullable=True)  # Encrypted connection info
    system_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.systems.id", ondelete="SET NULL"),
        nullable=True,
    )
    environment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.environments.id", ondelete="SET NULL"),
        nullable=True,
    )
    additional_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("name", name="uq_storage_locations_name"),
        {"schema": "pycharter"},
    )

    # Relationships
    system = relationship("SystemModel")
    environment = relationship("EnvironmentModel")
    metadata_records = relationship(
        "MetadataRecordStorageLocation",
        back_populates="storage_location",
        cascade="all, delete-orphan",
    )

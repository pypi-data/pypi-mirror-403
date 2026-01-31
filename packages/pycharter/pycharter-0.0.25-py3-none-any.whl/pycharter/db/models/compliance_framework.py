"""
SQLAlchemy model for compliance_frameworks table.

Represents compliance frameworks and regulations.
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from pycharter.db.models.base import Base


class ComplianceFrameworkModel(Base):
    """Represents compliance frameworks and regulations."""

    __tablename__ = "compliance_frameworks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)  # e.g., "GDPR", "HIPAA", "SOC2"
    code = Column(String(50), nullable=True, unique=True)  # e.g., "GDPR", "HIPAA"
    description = Column(Text, nullable=True)
    framework_type = Column(
        String(50), nullable=True
    )  # e.g., "regulation", "standard", "certification"
    is_active = Column(Boolean, nullable=False, default=True)
    additional_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("name", name="uq_compliance_frameworks_name"),
        {"schema": "pycharter"},
    )

    # Relationships
    metadata_records = relationship(
        "MetadataRecordComplianceFramework",
        back_populates="compliance_framework",
        cascade="all, delete-orphan",
    )

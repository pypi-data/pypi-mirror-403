"""
SQLAlchemy model for data_dependencies table.

Represents dependency relationships between data contracts.
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from pycharter.db.models.base import Base


class DataDependencyModel(Base):
    """Represents a dependency relationship between data contracts."""

    __tablename__ = "data_dependencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Source contract (the one that depends on another)
    source_contract_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.data_contracts.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Target contract (the one being depended upon)
    target_contract_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.data_contracts.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Dependency metadata
    dependency_type = Column(String(50), nullable=True)  # e.g., "required", "optional", "soft"
    description = Column(Text, nullable=True)
    is_critical = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            "source_contract_id", "target_contract_id", name="uq_data_dependencies_source_target"
        ),
        {"schema": "pycharter"},
    )

    # Relationships
    source_contract = relationship(
        "DataContractModel", foreign_keys=[source_contract_id], backref="dependencies"
    )
    target_contract = relationship(
        "DataContractModel", foreign_keys=[target_contract_id], backref="dependents"
    )

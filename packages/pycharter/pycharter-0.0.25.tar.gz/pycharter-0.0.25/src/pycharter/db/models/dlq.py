"""
SQLAlchemy model for dead_letter_queue table.

Stores failed ETL records that could not be processed, allowing for later analysis,
debugging, and potential retry.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from pycharter.db.models.base import Base


class DeadLetterQueueModel(Base):
    """
    SQLAlchemy model for dead_letter_queue table.
    
    Note: Schema is hardcoded to "pycharter".
    For applications using different schemas, use the schema_name parameter
    in DeadLetterQueue class, which uses raw SQL queries instead of this model.
    """

    __tablename__ = "dead_letter_queue"
    __table_args__ = {"schema": "pycharter"}  # Default schema for pycharter's own use

    # Primary key - 16 character hash
    id = Column(String(16), primary_key=True, comment="Unique record identifier (hash)")

    # Pipeline information
    pipeline_name = Column(String(255), nullable=False, index=True, comment="Name of the pipeline that failed")

    # Record data
    record_data = Column(JSON, nullable=False, comment="The actual record data that failed")

    # Error information
    reason = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Reason for DLQ placement (extraction_error, transformation_error, etc.)",
    )
    error_message = Column(Text, nullable=False, comment="Full error message")
    error_type = Column(String(100), nullable=False, index=True, comment="Error type (exception class name)")

    # ETL stage information
    stage = Column(String(20), nullable=False, index=True, comment="ETL stage where failure occurred (extract, transform, load)")

    # Metadata
    additional_metadata = Column(JSON, nullable=True, comment="Additional metadata (batch_num, run_id, etc.)")

    # Retry tracking
    retry_count = Column(Integer, default=0, nullable=False, comment="Number of retry attempts")
    status = Column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
        comment="Record status (pending, retrying, resolved, ignored)",
    )

    # Timestamps
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="When the record was added to DLQ",
    )
    resolved_at = Column(DateTime(timezone=True), nullable=True, comment="When the record was resolved")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Record creation timestamp")
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Record update timestamp",
    )

    def __repr__(self):
        return f"<DeadLetterQueueModel(id={self.id}, pipeline={self.pipeline_name}, reason={self.reason}, stage={self.stage})>"


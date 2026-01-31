"""
Shared utilities for API routes.

This module provides common helper functions used across API endpoints,
including UUID handling, database queries, and error handling.
"""

import logging
import uuid
from typing import Optional, TypeVar, Union

from fastapi import HTTPException, status
from sqlalchemy import cast, String
from sqlalchemy.orm import Session
from sqlalchemy.orm.decl_api import DeclarativeMeta

logger = logging.getLogger(__name__)

T = TypeVar("T")


def safe_uuid_to_str(value: Optional[Union[uuid.UUID, str]]) -> Optional[str]:
    """
    Safely convert a UUID or string to a string representation.
    
    Handles both UUID objects and string representations, including
    cases where SQLite might store UUIDs as strings.
    
    Args:
        value: UUID object, string, or None
        
    Returns:
        String representation of UUID, or None if value is None
    """
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, str):
        # If it's already a string, validate it's a valid UUID format
        try:
            # Validate and normalize the UUID string
            uuid_obj = uuid.UUID(value)
            return str(uuid_obj)
        except (ValueError, AttributeError):
            # If it's not a valid UUID, return as-is (might be a schema name)
            return value
    # Fallback: convert to string
    return str(value)


def ensure_uuid(value: Optional[Union[uuid.UUID, str, bytes]]) -> Optional[uuid.UUID]:
    """
    Ensure a value is a UUID object, converting from string or bytes if needed.
    
    Args:
        value: UUID object, string, bytes, or None
        
    Returns:
        UUID object, or None if value is None
        
    Raises:
        ValueError: If value cannot be converted to UUID
    """
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    if isinstance(value, str):
        # Handle empty strings
        if not value.strip():
            return None
        return uuid.UUID(value)
    if isinstance(value, bytes):
        # Handle bytes (sometimes database drivers return UUIDs as bytes)
        return uuid.UUID(value.decode('utf-8'))
    # Try to convert to string first, then to UUID
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Cannot convert {type(value)} ({value}) to UUID: {e}")


def get_by_id_with_fallback(
    db: Session,
    model: DeclarativeMeta,
    id_value: Union[uuid.UUID, str],
    error_message: Optional[str] = None,
) -> Optional[T]:
    """
    Get a database record by ID with fallback strategies for UUID compatibility.
    
    This function tries multiple strategies to find a record:
    1. Direct UUID comparison
    2. String comparison (for SQLite compatibility)
    3. Query all and compare by string (final fallback)
    
    Args:
        db: Database session
        model: SQLAlchemy model class
        id_value: UUID or string ID to search for
        error_message: Optional custom error message if not found
        
    Returns:
        Model instance if found, None otherwise
    """
    # Try UUID comparison first
    try:
        if isinstance(id_value, str):
            id_uuid = uuid.UUID(id_value)
        else:
            id_uuid = id_value
        
        record = db.query(model).filter(model.id == id_uuid).first()
        if record:
            return record
    except (ValueError, TypeError):
        pass
    
    # Try string comparison (for SQLite compatibility)
    id_str = safe_uuid_to_str(id_value)
    if id_str:
        try:
            record = db.query(model).filter(
                cast(model.id, String) == id_str
            ).first()
            if record:
                return record
        except Exception:
            pass
    
    # Final fallback: query all and compare by string
    try:
        all_records = db.query(model).all()
        for record in all_records:
            record_id_str = safe_uuid_to_str(record.id)
            if record_id_str and id_str:
                if (record_id_str == id_str or 
                    record_id_str.lower() == id_str.lower()):
                    return record
    except Exception as e:
        logger.debug(f"Fallback query failed: {e}")
    
    return None


def get_by_id_or_404(
    db: Session,
    model: DeclarativeMeta,
    id_value: Union[uuid.UUID, str],
    error_message: Optional[str] = None,
    model_name: Optional[str] = None,
) -> T:
    """
    Get a database record by ID or raise 404 if not found.
    
    Args:
        db: Database session
        model: SQLAlchemy model class
        id_value: UUID or string ID to search for
        error_message: Optional custom error message
        model_name: Optional model name for error message
        
    Returns:
        Model instance
        
    Raises:
        HTTPException: 404 if record not found
    """
    record = get_by_id_with_fallback(db, model, id_value, error_message)
    
    if not record:
        id_str = safe_uuid_to_str(id_value)
        model_display = model_name or model.__name__
        default_message = f"{model_display} with ID {id_str} not found"
        message = error_message or default_message
        
        # Log diagnostic info
        total = db.query(model).count()
        logger.error(
            f"{model_display} not found: {id_str}. "
            f"Total {model_display.lower()}s: {total}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message,
        )
    
    return record


def model_to_dict(model_instance) -> dict:
    """
    Convert SQLAlchemy model instance to dictionary.
    
    Handles UUIDs, datetimes, and JSON fields appropriately.
    
    Args:
        model_instance: SQLAlchemy model instance
        
    Returns:
        Dictionary representation of the model
    """
    if model_instance is None:
        return {}
    
    result = {}
    for column in model_instance.__table__.columns:
        value = getattr(model_instance, column.name, None)
        if value is None:
            result[column.name] = None
        # Convert UUID to string
        elif hasattr(value, 'hex'):
            result[column.name] = str(value)
        # Convert datetime to ISO format string
        elif hasattr(value, 'isoformat'):
            result[column.name] = value.isoformat()
        # Keep JSON fields as-is
        elif isinstance(value, (dict, list)):
            result[column.name] = value
        else:
            result[column.name] = value
    return result

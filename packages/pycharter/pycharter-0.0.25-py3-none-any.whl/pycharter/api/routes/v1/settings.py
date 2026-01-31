"""
Route handlers for settings and configuration testing.
"""

import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from pycharter.config import get_database_url
from pycharter.api.dependencies.database import get_db_session

router = APIRouter()


class DatabaseConfigResponse(BaseModel):
    """Response model for database configuration info."""
    configured_url: Optional[str]
    actual_url: str
    database_type: str
    is_default: bool
    contract_count: int
    message: str


class DatabaseTestRequest(BaseModel):
    connection_string: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class DatabaseTestResponse(BaseModel):
    success: bool
    message: str


class DlqTestRequest(BaseModel):
    connection_string: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    table_name: Optional[str] = None


class DlqTestResponse(BaseModel):
    success: bool
    message: str


class DlqStatsRequest(BaseModel):
    connection_string: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    table_name: Optional[str] = None


class DlqStatsResponse(BaseModel):
    total_messages: int
    by_reason: dict[str, int]
    by_stage: dict[str, int]
    by_status: dict[str, int]


@router.get(
    "/settings/database-config",
    response_model=DatabaseConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current database configuration",
    description="Get information about the currently configured database connection",
)
async def get_database_config(
    db: Session = Depends(get_db_session),
) -> DatabaseConfigResponse:
    """
    Get current database configuration and connection info.
    
    Shows which database is actually being used, which helps diagnose
    issues where SQLite might be used instead of PostgreSQL.
    """
    from pycharter.db.models import DataContractModel
    
    configured_url = get_database_url()
    
    # Get actual URL from the session
    actual_url = str(db.bind.url) if hasattr(db, 'bind') and db.bind else "unknown"
    
    # Determine database type
    if actual_url.startswith("sqlite"):
        database_type = "SQLite"
        is_default = configured_url is None
    elif actual_url.startswith(("postgresql", "postgres")):
        database_type = "PostgreSQL"
        is_default = False
    else:
        database_type = "Unknown"
        is_default = False
    
    # Count contracts in current database
    try:
        contract_count = db.query(DataContractModel).count()
    except Exception:
        contract_count = -1
    
    # Build message
    if is_default:
        message = (
            f"⚠️ No database URL configured. Using default SQLite database.\n"
            f"To use PostgreSQL, set the PYCHARTER_DATABASE_URL environment variable:\n"
            f"  export PYCHARTER_DATABASE_URL='postgresql://user:password@localhost:5432/pycharter'"
        )
    else:
        # Mask password in configured URL
        masked_configured = configured_url
        if configured_url and "@" in configured_url:
            parts = configured_url.split("@", 1)
            if ":" in parts[0] and "://" in parts[0]:
                scheme_user = parts[0].split("://", 1)[0]
                user_pass = parts[0].split("://", 1)[1]
                if ":" in user_pass:
                    user, _ = user_pass.split(":", 1)
                    masked_configured = f"{scheme_user}://{user}:****@{parts[1]}"
        
        message = f"✓ Using {database_type} database"
    
    return DatabaseConfigResponse(
        configured_url=masked_configured if 'masked_configured' in locals() else configured_url,
        actual_url=actual_url.split("@")[-1] if "@" in actual_url else actual_url,  # Show only host/db part
        database_type=database_type,
        is_default=is_default,
        contract_count=contract_count,
        message=message,
    )


def _build_connection_string(
    connection_string: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    database: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> str:
    """Build database connection string from components."""
    if connection_string:
        return connection_string
    
    if not all([host, database]):
        raise ValueError("Either connection_string or (host and database) must be provided")
    
    # Default to PostgreSQL if port not specified
    if port is None:
        port = 5432
    
    if username and password:
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    elif username:
        return f"postgresql://{username}@{host}:{port}/{database}"
    else:
        return f"postgresql://{host}:{port}/{database}"


@router.post(
    "/settings/test-database",
    response_model=DatabaseTestResponse,
    status_code=status.HTTP_200_OK,
    summary="Test database connection",
    description="Test a database connection using provided credentials",
)
async def test_database(request: DatabaseTestRequest) -> DatabaseTestResponse:
    """Test database connection."""
    try:
        connection_string = _build_connection_string(
            connection_string=request.connection_string,
            host=request.host,
            port=request.port,
            database=request.database,
            username=request.username,
            password=request.password,
        )
        
        engine = create_engine(connection_string, pool_pre_ping=True)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return DatabaseTestResponse(
            success=True,
            message="Database connection successful",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except SQLAlchemyError as e:
        return DatabaseTestResponse(
            success=False,
            message=f"Database connection failed: {str(e)}",
        )
    except Exception as e:
        return DatabaseTestResponse(
            success=False,
            message=f"Unexpected error: {str(e)}",
        )


@router.post(
    "/settings/test-dlq",
    response_model=DlqTestResponse,
    status_code=status.HTTP_200_OK,
    summary="Test DLQ connection",
    description="Test a DLQ (Dead Letter Queue) database connection and verify table exists",
)
async def test_dlq(request: DlqTestRequest) -> DlqTestResponse:
    """Test DLQ connection and table existence."""
    try:
        connection_string = _build_connection_string(
            connection_string=request.connection_string,
            host=request.host,
            port=request.port,
            database=request.database,
            username=request.username,
            password=request.password,
        )
        
        if not request.table_name:
            raise ValueError("table_name is required")
        
        engine = create_engine(connection_string, pool_pre_ping=True)
        
        # Test connection and table existence
        with engine.connect() as conn:
            # Check if table exists
            if engine.dialect.name == 'postgresql':
                result = conn.execute(
                    text(
                        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table_name)"
                    ),
                    {"table_name": request.table_name},
                )
            elif engine.dialect.name == 'sqlite':
                result = conn.execute(
                    text(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"
                    ),
                    {"table_name": request.table_name},
                )
            else:
                # Generic check
                result = conn.execute(
                    text(f"SELECT 1 FROM {request.table_name} LIMIT 1")
                )
            
            if engine.dialect.name == 'postgresql':
                exists = result.scalar()
                if not exists:
                    return DlqTestResponse(
                        success=False,
                        message=f"Table '{request.table_name}' does not exist",
                    )
        
        return DlqTestResponse(
            success=True,
            message=f"DLQ connection successful. Table '{request.table_name}' exists.",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except SQLAlchemyError as e:
        return DlqTestResponse(
            success=False,
            message=f"DLQ connection failed: {str(e)}",
        )
    except Exception as e:
        return DlqTestResponse(
            success=False,
            message=f"Unexpected error: {str(e)}",
        )


@router.post(
    "/settings/dlq-stats",
    response_model=DlqStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get DLQ statistics",
    description="Get statistics from the DLQ table grouped by reason, stage, and status",
)
async def get_dlq_stats(request: DlqStatsRequest) -> DlqStatsResponse:
    """Get DLQ statistics."""
    try:
        connection_string = _build_connection_string(
            connection_string=request.connection_string,
            host=request.host,
            port=request.port,
            database=request.database,
            username=request.username,
            password=request.password,
        )
        
        if not request.table_name:
            raise ValueError("table_name is required")
        
        engine = create_engine(connection_string, pool_pre_ping=True)
        
        with engine.connect() as conn:
            # Get total count
            total_result = conn.execute(
                text(f"SELECT COUNT(*) FROM {request.table_name}")
            )
            total_messages = total_result.scalar() or 0
            
            # Get counts by reason
            by_reason = {}
            try:
                reason_result = conn.execute(
                    text(
                        f"SELECT reason, COUNT(*) as count FROM {request.table_name} GROUP BY reason"
                    )
                )
                for row in reason_result:
                    by_reason[row[0] or 'unknown'] = row[1]
            except Exception:
                # Column might not exist
                pass
            
            # Get counts by stage
            by_stage = {}
            try:
                stage_result = conn.execute(
                    text(
                        f"SELECT stage, COUNT(*) as count FROM {request.table_name} GROUP BY stage"
                    )
                )
                for row in stage_result:
                    by_stage[row[0] or 'unknown'] = row[1]
            except Exception:
                # Column might not exist
                pass
            
            # Get counts by status
            by_status = {}
            try:
                status_result = conn.execute(
                    text(
                        f"SELECT status, COUNT(*) as count FROM {request.table_name} GROUP BY status"
                    )
                )
                for row in status_result:
                    by_status[row[0] or 'unknown'] = row[1]
            except Exception:
                # Column might not exist
                pass
        
        return DlqStatsResponse(
            total_messages=total_messages,
            by_reason=by_reason,
            by_stage=by_stage,
            by_status=by_status,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )

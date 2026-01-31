"""
Database session dependency for API routes.
"""

import os
from pathlib import Path
from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from pycharter.config import get_database_url, set_database_url
from pycharter.db.models.base import Base, get_session


def _get_migrations_dir() -> Path:
    """Find migrations directory relative to installed package."""
    try:
        import pycharter
        migrations_dir = Path(pycharter.__file__).parent / "db" / "migrations"
    except (ImportError, AttributeError):
        # Fallback for development
        migrations_dir = Path(__file__).resolve().parent.parent.parent / "pycharter" / "db" / "migrations"
    
    if not migrations_dir.exists():
        cwd_migrations = Path(os.getcwd()) / "pycharter" / "db" / "migrations"
        if cwd_migrations.exists():
            return cwd_migrations
        # If migrations dir doesn't exist, return a path anyway (create_all will still work)
        return migrations_dir
    return migrations_dir


def _ensure_sqlite_initialized(db_url: str) -> None:
    """
    Ensure SQLite database is initialized with all tables.
    
    Auto-initializes SQLite database if it doesn't exist or is uninitialized.
    """
    if not db_url.startswith("sqlite://"):
        return
    
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        db_path = db_url[10:] if db_url.startswith("sqlite:///") else db_url
        if db_path == ":memory:":
            return
        
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        engine = create_engine(db_url)
        inspector = inspect(engine)
        
        if "data_contracts" not in inspector.get_table_names():
            logger.info(f"Auto-initializing SQLite database: {db_url}")
            
            # Import all models
            from pycharter.db.models import (  # noqa: F401
                CoercionRuleModel,
                DataContractModel,
                DomainModel,
                MetadataRecordModel,
                OwnerModel,
                QualityMetricModel,
                QualityViolationModel,
                SchemaModel,
                SystemModel,
                ValidationRuleModel,
            )
            
            # Remove schema prefix for SQLite
            for table in Base.metadata.tables.values():
                if table.schema == "pycharter":
                    table.schema = None
            
            Base.metadata.create_all(engine)
            
            # Try to run migrations
            try:
                from alembic import command
                from alembic.config import Config
                
                versions_dir = _get_migrations_dir() / "versions"
                if versions_dir.exists() and any(versions_dir.iterdir()):
                    set_database_url(db_url)
                    config = Config()
                    config.set_main_option("script_location", str(_get_migrations_dir()))
                    config.set_main_option("sqlalchemy.url", db_url)
                    command.upgrade(config, "head")
                    logger.info("✓ SQLite database initialized with migrations")
                else:
                    logger.info("✓ SQLite database initialized with base tables")
            except Exception:
                logger.info("✓ SQLite database initialized with base tables")
    except Exception as e:
        logger.warning(f"Could not auto-initialize SQLite database: {e}")


def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency to get database session.
    
    Defaults to SQLite (sqlite:///pycharter.db) if no database URL is configured.
    Automatically initializes SQLite database if it doesn't exist or is uninitialized.
    
    **Important**: This dependency properly manages session lifecycle using yield,
    ensuring sessions are closed after request completion.
    
    Yields:
        SQLAlchemy session
        
    Raises:
        HTTPException: If database connection fails
    """
    import logging
    
    logger = logging.getLogger(__name__)
    
    db_url = get_database_url()
    
    # Default to SQLite if no database URL is configured
    if not db_url:
        default_db_path = Path.cwd() / "pycharter.db"
        db_url = f"sqlite:///{default_db_path}"
        logger.warning(
            f"No database URL configured. Using default SQLite: {db_url}\n"
            f"To use PostgreSQL, set PYCHARTER_DATABASE_URL environment variable:\n"
            f"  export PYCHARTER_DATABASE_URL='postgresql://user:password@localhost:5432/pycharter'"
        )
    else:
        # Mask password in logs
        masked_url = db_url
        if "@" in db_url and "://" in db_url:
            parts = db_url.split("@", 1)
            if ":" in parts[0]:
                user_pass = parts[0].split("://", 1)[1]
                if ":" in user_pass:
                    user, _ = user_pass.split(":", 1)
                    masked_url = db_url.split(":", 2)[0] + "://" + user + ":****@" + parts[1]
        logger.info(f"Using database: {masked_url}")
    
    # Auto-initialize SQLite if needed
    _ensure_sqlite_initialized(db_url)
    
    session = None
    try:
        session = get_session(db_url)
        # Test the connection by executing a simple query
        from sqlalchemy import text
        session.execute(text("SELECT 1"))
        yield session
    except Exception as e:
        if session:
            try:
                session.rollback()
            except Exception:
                pass
        logger.error(f"Database session error: {e}", exc_info=True)
        
        # Provide more helpful error messages
        error_detail = "Failed to connect to database"
        error_msg = str(e).lower()
        
        # Check for common issues
        if "no such table" in error_msg or "table" in error_msg and "doesn't exist" in error_msg:
            error_detail = (
                "Database tables not found. Please initialize the database:\n"
                f"  pycharter db init {db_url}"
            )
        elif "database is locked" in error_msg:
            error_detail = (
                "Database is locked. Another process may be using it.\n"
                "Close other connections or wait a moment and try again."
            )
        elif "permission denied" in error_msg or "access denied" in error_msg:
            error_detail = (
                "Database permission denied. Check file permissions:\n"
                f"  chmod 644 {db_url.split(':///')[-1] if 'sqlite' in db_url else 'database file'}"
            )
        else:
            # Show detailed error in development mode
            is_development = os.getenv("ENVIRONMENT") == "development" or not os.getenv("ENVIRONMENT")
            if is_development:
                error_detail = f"Failed to connect to database: {str(e)}"
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail,
        )
    finally:
        if session:
            try:
                session.close()
            except Exception:
                pass



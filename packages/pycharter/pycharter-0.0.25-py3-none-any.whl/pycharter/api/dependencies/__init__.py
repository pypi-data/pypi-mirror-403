"""
Dependencies for API routes.

This module provides FastAPI dependency injection for shared resources.
"""

from pycharter.api.dependencies.database import get_db_session
from pycharter.api.dependencies.store import get_metadata_store

__all__ = ["get_db_session", "get_metadata_store"]

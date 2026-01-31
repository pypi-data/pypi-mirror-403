"""
Database loaders for ETL pipelines.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from pycharter.etl_generator.database import (
    detect_database_type,
    create_ssh_tunnel,
    modify_url_for_tunnel,
    load_data_postgresql,
    load_data_mysql,
    load_data_sqlite,
    load_data_mssql,
    DEFAULT_TUNNEL_LOCAL_PORT,
    DB_POSTGRESQL,
    DB_MYSQL,
    DB_SQLITE,
    DB_MSSQL,
)
from pycharter.etl_generator.loaders.base import BaseLoader
from pycharter.etl_generator.result import LoadResult

logger = logging.getLogger(__name__)


class PostgresLoader(BaseLoader):
    """
    Loader for PostgreSQL databases.
    
    Supports:
    - Insert, upsert, replace, update, delete, truncate_and_load
    - Bulk operations for efficiency
    - SSH tunneling
    
    Example:
        >>> loader = PostgresLoader(
        ...     connection_string="postgresql://user:pass@localhost/db",
        ...     table="users",
        ...     write_method="upsert",
        ...     primary_key="id",
        ... )
        >>> result = await loader.load(data)
    """
    
    def __init__(
        self,
        connection_string: str,
        table: str,
        schema: str = "public",
        write_method: str = "upsert",
        primary_key: Optional[Union[str, List[str]]] = None,
        batch_size: int = 1000,
        ssh_tunnel: Optional[Dict[str, Any]] = None,
    ):
        self.connection_string = connection_string
        self.table = table
        self.schema = schema
        self.write_method = write_method
        self.primary_key = primary_key
        self.batch_size = batch_size
        self.ssh_tunnel = ssh_tunnel
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "PostgresLoader":
        """Create loader from configuration dict."""
        db_config = config.get("database", {})
        return cls(
            connection_string=db_config.get("url") or config.get("connection_string"),
            table=db_config.get("table") or config.get("table"),
            schema=db_config.get("schema", config.get("schema", "public")),
            write_method=db_config.get("write_method", config.get("write_method", "upsert")),
            primary_key=db_config.get("primary_key") or config.get("primary_key"),
            batch_size=config.get("batch_size", 1000),
            ssh_tunnel=db_config.get("ssh_tunnel"),
        )
    
    async def load(self, data: List[Dict[str, Any]], **params) -> LoadResult:
        """Load data to PostgreSQL."""
        start_time = time.time()
        
        if not data:
            return LoadResult(success=True, rows_loaded=0)
        
        # Handle SSH tunnel if configured
        tunnel = None
        connection_string = self.connection_string
        
        if self.ssh_tunnel and self.ssh_tunnel.get("enabled"):
            tunnel = create_ssh_tunnel(self.ssh_tunnel)
            if tunnel:
                local_port = int(self.ssh_tunnel.get("local_port", DEFAULT_TUNNEL_LOCAL_PORT))
                connection_string = modify_url_for_tunnel(
                    connection_string, local_port, DB_POSTGRESQL
                )
        
        try:
            # Use async engine for PostgreSQL
            # Convert sync URL to async if needed
            if "+asyncpg" not in connection_string:
                async_url = connection_string.replace("postgresql://", "postgresql+asyncpg://")
            else:
                async_url = connection_string
            
            engine = create_async_engine(async_url, echo=False)
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            async with async_session() as session:
                result = await load_data_postgresql(
                    data=data,
                    session=session,
                    schema_name=self.schema,
                    table_name=self.table,
                    write_method=self.write_method,
                    primary_key=self.primary_key,
                    batch_size=self.batch_size,
                )
            
            await engine.dispose()
            
            duration = time.time() - start_time
            logger.info(f"Loaded {result['total']} records to {self.schema}.{self.table} in {duration:.2f}s")
            
            return LoadResult(
                success=True,
                rows_loaded=result.get("inserted", 0) + result.get("updated", 0),
                duration_seconds=duration,
            )
        
        except Exception as e:
            logger.error(f"PostgreSQL load failed: {e}", exc_info=True)
            return LoadResult(
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )
        finally:
            if tunnel:
                tunnel.stop()


class DatabaseLoader(BaseLoader):
    """
    Generic database loader that auto-detects database type.
    
    Supports PostgreSQL, MySQL, SQLite, and MSSQL.
    
    Example:
        >>> loader = DatabaseLoader(
        ...     connection_string="mysql://user:pass@localhost/db",
        ...     table="users",
        ... )
        >>> result = await loader.load(data)
    """
    
    def __init__(
        self,
        connection_string: str,
        table: str,
        schema: Optional[str] = None,
        write_method: str = "upsert",
        primary_key: Optional[Union[str, List[str]]] = None,
        batch_size: int = 1000,
        ssh_tunnel: Optional[Dict[str, Any]] = None,
    ):
        self.connection_string = connection_string
        self.table = table
        self.schema = schema
        self.write_method = write_method
        self.primary_key = primary_key
        self.batch_size = batch_size
        self.ssh_tunnel = ssh_tunnel
        self.db_type = detect_database_type(connection_string)
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "DatabaseLoader":
        """Create loader from configuration dict."""
        db_config = config.get("database", {})
        return cls(
            connection_string=db_config.get("url") or config.get("connection_string"),
            table=db_config.get("table") or config.get("table"),
            schema=db_config.get("schema") or config.get("schema"),
            write_method=db_config.get("write_method", config.get("write_method", "upsert")),
            primary_key=db_config.get("primary_key") or config.get("primary_key"),
            batch_size=config.get("batch_size", 1000),
            ssh_tunnel=db_config.get("ssh_tunnel"),
        )
    
    async def load(self, data: List[Dict[str, Any]], **params) -> LoadResult:
        """Load data using appropriate database loader."""
        if self.db_type == DB_POSTGRESQL:
            loader = PostgresLoader(
                connection_string=self.connection_string,
                table=self.table,
                schema=self.schema or "public",
                write_method=self.write_method,
                primary_key=self.primary_key,
                batch_size=self.batch_size,
                ssh_tunnel=self.ssh_tunnel,
            )
            return await loader.load(data, **params)
        else:
            # For non-PostgreSQL databases, use sync loading
            return await self._load_sync(data, **params)
    
    async def _load_sync(self, data: List[Dict[str, Any]], **params) -> LoadResult:
        """Load data using sync database operations."""
        start_time = time.time()
        
        if not data:
            return LoadResult(success=True, rows_loaded=0)
        
        # Handle SSH tunnel if configured
        tunnel = None
        connection_string = self.connection_string
        
        if self.ssh_tunnel and self.ssh_tunnel.get("enabled"):
            tunnel = create_ssh_tunnel(self.ssh_tunnel)
            if tunnel:
                local_port = int(self.ssh_tunnel.get("local_port", DEFAULT_TUNNEL_LOCAL_PORT))
                connection_string = modify_url_for_tunnel(
                    connection_string, local_port, self.db_type
                )
        
        try:
            engine = create_engine(connection_string, echo=False)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Select appropriate load function
            if self.db_type == DB_MYSQL:
                result = load_data_mysql(
                    data, session, self.schema or "", self.table,
                    self.write_method, self.primary_key, self.batch_size
                )
            elif self.db_type == DB_SQLITE:
                result = load_data_sqlite(
                    data, session, "", self.table,
                    self.write_method, self.primary_key, self.batch_size
                )
            elif self.db_type == DB_MSSQL:
                result = load_data_mssql(
                    data, session, self.schema or "dbo", self.table,
                    self.write_method, self.primary_key, self.batch_size
                )
            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")
            
            session.close()
            engine.dispose()
            
            duration = time.time() - start_time
            return LoadResult(
                success=True,
                rows_loaded=result.get("inserted", 0) + result.get("updated", 0),
                duration_seconds=duration,
            )
        
        except Exception as e:
            logger.error(f"Database load failed: {e}", exc_info=True)
            return LoadResult(
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )
        finally:
            if tunnel:
                tunnel.stop()

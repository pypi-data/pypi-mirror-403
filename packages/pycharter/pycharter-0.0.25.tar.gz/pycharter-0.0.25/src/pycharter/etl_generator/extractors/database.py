"""
Database extractor for ETL orchestrator.

Supports extracting data from databases:
- PostgreSQL
- MySQL
- SQLite
- MSSQL
- Oracle
"""

import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from pycharter.etl_generator.database import (
    create_ssh_tunnel,
    detect_database_type,
    modify_url_for_tunnel,
    DEFAULT_TUNNEL_LOCAL_PORT,
)
from pycharter.etl_generator.extractors.base import BaseExtractor
from pycharter.utils.value_injector import resolve_values

logger = logging.getLogger(__name__)


class DatabaseExtractor(BaseExtractor):
    """
    Extractor for database data sources.
    
    Supports two modes:
    1. Programmatic API:
        >>> extractor = DatabaseExtractor(connection_string="...", query="SELECT * FROM users")
        >>> async for batch in extractor.extract():
        ...     process(batch)
    
    2. Config-driven:
        >>> extractor = DatabaseExtractor()
        >>> async for batch in extractor.extract_streaming(config, params, headers):
        ...     process(batch)
    """
    
    def __init__(
        self,
        connection_string: Optional[str] = None,
        query: Optional[str] = None,
        query_params: Optional[Dict[str, Any]] = None,
        batch_size: int = 1000,
        max_records: Optional[int] = None,
        ssh_tunnel: Optional[Dict[str, Any]] = None,
    ):
        self.connection_string = connection_string
        self.query = query
        self.query_params = query_params or {}
        self.batch_size = batch_size
        self.max_records = max_records
        self.ssh_tunnel = ssh_tunnel
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "DatabaseExtractor":
        """Create extractor from configuration dict."""
        db_config = config.get("database", {})
        return cls(
            connection_string=db_config.get("url") or config.get("connection_string"),
            query=config.get("query"),
            query_params=config.get("query_params", {}),
            batch_size=config.get("batch_size", 1000),
            max_records=config.get("max_records"),
            ssh_tunnel=db_config.get("ssh_tunnel"),
        )
    
    async def extract(self, **params) -> AsyncIterator[List[Dict[str, Any]]]:
        """
        Extract data from database.
        
        Yields:
            Batches of records
        """
        if not self.connection_string:
            raise ValueError("Connection string is required")
        if not self.query:
            raise ValueError("SQL query is required")
        
        extract_config = {
            "database": {
                "url": self.connection_string,
                "ssh_tunnel": self.ssh_tunnel,
            },
            "query": self.query,
            "query_params": {**self.query_params, **params},
        }
        
        async for batch in self.extract_streaming(
            extract_config, {}, {},
            batch_size=self.batch_size,
            max_records=self.max_records,
        ):
            yield batch
    
    def validate_config(self, extract_config: Dict[str, Any]) -> None:
        """Validate database extractor configuration."""
        if 'source_type' in extract_config and extract_config['source_type'] != 'database':
            raise ValueError(f"DatabaseExtractor requires source_type='database', got '{extract_config.get('source_type')}'")
        
        db_config = extract_config.get('database', {})
        if not db_config.get('url'):
            raise ValueError("Database extractor requires 'database.url' in extract_config")
        
        if not extract_config.get('query'):
            raise ValueError("Database extractor requires 'query' in extract_config")
    
    async def extract_streaming(
        self,
        extract_config: Dict[str, Any],
        params: Dict[str, Any],
        headers: Dict[str, Any],
        contract_dir: Optional[Any] = None,
        batch_size: int = 1000,
        max_records: Optional[int] = None,
        config_context: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """
        Extract data from database using SQL query.
        
        Supports parameterized queries and streaming results for large datasets.
        """
        # Get database configuration
        db_config = extract_config.get('database', {})
        query = extract_config.get('query')
        
        if not query:
            raise ValueError("Database extractor requires 'query' in extract_config")
        
        # Resolve variables
        source_file = str(contract_dir / "extract.yaml") if contract_dir else None
        db_url = resolve_values(db_config.get('url'), context=config_context, source_file=source_file)
        query = resolve_values(query, context=config_context, source_file=source_file)
        
        # Resolve query parameters (merge params from config and kwargs)
        query_params = extract_config.get('query_params', {})
        query_params.update(params)  # params from kwargs override config params
        
        # Handle SSH tunnel if configured
        ssh_config = db_config.get('ssh_tunnel', {})
        tunnel = None
        if ssh_config:
            ssh_config = resolve_values(ssh_config, context=config_context, source_file=source_file)
            enabled_value = ssh_config.get('enabled', False)
            if isinstance(enabled_value, str):
                enabled_lower = enabled_value.lower()
                ssh_config['enabled'] = enabled_lower in ('true', '1', 'yes', 'on')
            elif not isinstance(enabled_value, bool):
                ssh_config['enabled'] = bool(enabled_value)
            
            if ssh_config.get('enabled', False):
                tunnel = create_ssh_tunnel(ssh_config)
                if tunnel:
                    db_type_from_url = detect_database_type(db_url)
                    local_port = int(ssh_config.get('local_port', DEFAULT_TUNNEL_LOCAL_PORT))
                    db_url = modify_url_for_tunnel(db_url, local_port, db_type_from_url)
        
        # Detect database type
        db_type = db_config.get('type')
        if not db_type:
            db_type = detect_database_type(db_url)
        
        # Create engine and session
        engine = create_engine(db_url, echo=False)
        SessionClass = sessionmaker(bind=engine)
        session = SessionClass()
        
        try:
            # Execute query with streaming
            logger.info(f"Executing database query (db_type: {db_type})")
            logger.debug(f"Query: {query[:200]}...")
            
            result = session.execute(text(query), query_params)
            
            # Stream results in batches
            current_batch = []
            total_extracted = 0
            
            for row in result:
                if max_records and total_extracted >= max_records:
                    break
                
                # Convert row to dict
                if hasattr(row, '_asdict'):
                    # Named tuple-like row
                    record = row._asdict()
                elif hasattr(row, '_mapping'):
                    # Row mapping
                    record = dict(row._mapping)
                else:
                    # Fallback: use column names
                    record = {col: getattr(row, col) for col in row.keys()}
                
                current_batch.append(record)
                total_extracted += 1
                
                if len(current_batch) >= batch_size:
                    yield current_batch
                    current_batch = []
            
            # Yield remaining records
            if current_batch:
                yield current_batch
            
            logger.info(f"Database extraction completed: {total_extracted} records extracted")
            
        except Exception as e:
            logger.error(f"Database extraction error: {e}", exc_info=True)
            raise RuntimeError(f"Database extraction failed: {e}") from e
        finally:
            session.close()
            engine.dispose()
            if tunnel:
                tunnel.stop()

"""
Streaming extraction entry point for the ETL orchestrator.

Delegates to the appropriate extractor via ExtractorFactory.
"""

from typing import Any, AsyncIterator, Dict, List, Optional

from pycharter.etl_generator.extractors.factory import ExtractorFactory


async def extract_with_pagination_streaming(
    extract_config: Dict[str, Any],
    params: Dict[str, Any],
    headers: Dict[str, Any],
    contract_dir: Optional[Any] = None,
    batch_size: int = 1000,
    max_records: Optional[int] = None,
    config_context: Optional[Dict[str, Any]] = None,
) -> AsyncIterator[List[Dict[str, Any]]]:
    """
    Extract data with pagination support, yielding batches for memory-efficient processing.

    This is the main entry point for data extraction. It supports multiple source types:
    - HTTP/API (default when base_url/api_endpoint present)
    - File-based (CSV, JSON, Parquet, Excel, TSV, XML)
    - Database (PostgreSQL, MySQL, SQLite, MSSQL, Oracle)
    - Cloud storage (S3, GCS, Azure Blob)

    The source type is auto-detected from extract_config or can be explicitly set
    via 'source_type' field.

    Yields batches as they are extracted, preventing memory exhaustion for large datasets.

    Args:
        extract_config: Extract configuration dictionary
        params: Request/query parameters (source-specific)
        headers: Request headers (source-specific, mainly for HTTP)
        contract_dir: Contract directory (for variable resolution)
        batch_size: Number of records to yield per batch
        max_records: Maximum total records to extract (None = all)
        config_context: Optional context dictionary for value injection

    Yields:
        Batches of extracted records (lists of dictionaries)
    """
    extractor = ExtractorFactory.get_extractor(extract_config)
    async for batch in extractor.extract_streaming(
        extract_config,
        params,
        headers,
        contract_dir=contract_dir,
        batch_size=batch_size,
        max_records=max_records,
        config_context=config_context,
    ):
        yield batch

"""
Extractors module for ETL orchestrator.

This module provides a modular architecture for data extraction from various sources:
- HTTP/API extraction
- File-based extraction (CSV, JSON, Parquet, Excel, TSV, XML)
- Database extraction (PostgreSQL, MySQL, SQLite, MSSQL, Oracle)
- Cloud storage extraction (S3, GCS, Azure Blob)

Entry point for orchestration: extract_with_pagination_streaming().
"""

from pycharter.etl_generator.extractors.base import BaseExtractor
from pycharter.etl_generator.extractors.cloud_storage import CloudStorageExtractor
from pycharter.etl_generator.extractors.database import DatabaseExtractor
from pycharter.etl_generator.extractors.file import FileExtractor
from pycharter.etl_generator.extractors.factory import ExtractorFactory, get_extractor
from pycharter.etl_generator.extractors.http import HTTPExtractor
from pycharter.etl_generator.extractors.streaming import extract_with_pagination_streaming

__all__ = [
    "BaseExtractor",
    "ExtractorFactory",
    "get_extractor",
    "HTTPExtractor",
    "FileExtractor",
    "DatabaseExtractor",
    "CloudStorageExtractor",
    "extract_with_pagination_streaming",
]

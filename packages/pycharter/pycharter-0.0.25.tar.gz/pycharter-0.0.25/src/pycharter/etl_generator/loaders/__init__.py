"""
Load (destination) backends for ETL pipelines.

Two APIs:
1. Class-based: PostgresLoader(...).load(data) - for programmatic use
2. Function-based: load_to_file(data, config) - for config-driven use

Supports:
- Database (PostgreSQL, MySQL, SQLite, MSSQL)
- File (local JSON, CSV, Parquet, JSONL)
- Cloud storage (AWS S3, Google Cloud Storage, Azure Blob)
"""

# Class-based loaders (new API)
from pycharter.etl_generator.loaders.base import BaseLoader
from pycharter.etl_generator.loaders.database import PostgresLoader, DatabaseLoader
from pycharter.etl_generator.loaders.file import FileLoader
from pycharter.etl_generator.loaders.cloud import CloudStorageLoader

# Factory
from pycharter.etl_generator.loaders.factory import LoaderFactory, get_loader

# Function-based loaders (config-driven)
from pycharter.etl_generator.loaders.file_loader import load_to_file
from pycharter.etl_generator.loaders.cloud_storage_loader import load_to_cloud_storage

__all__ = [
    # Base class
    "BaseLoader",
    # Factory
    "LoaderFactory",
    "get_loader",
    # Class-based loaders
    "PostgresLoader",
    "DatabaseLoader",
    "FileLoader",
    "CloudStorageLoader",
    # Function-based loaders
    "load_to_file",
    "load_to_cloud_storage",
]

"""
Cloud storage extractor for ETL orchestrator.

Supports extracting data from cloud storage:
- AWS S3
- Google Cloud Storage (GCS)
- Azure Blob Storage
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from pycharter.etl_generator.extractors.base import BaseExtractor
from pycharter.etl_generator.extractors.file import FileExtractor
from pycharter.utils.value_injector import resolve_values

logger = logging.getLogger(__name__)

# Try to import cloud storage libraries
try:
    import boto3
    from botocore.exceptions import ClientError
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False
    boto3 = None
    ClientError = None

try:
    from google.cloud import storage as gcs_storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    gcs_storage = None

try:
    from azure.storage.blob import BlobServiceClient
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    BlobServiceClient = None


class CloudStorageExtractor(BaseExtractor):
    """
    Extractor for cloud storage data sources.
    
    Supports two modes:
    1. Programmatic API:
        >>> extractor = CloudStorageExtractor(provider="s3", bucket="my-bucket", path="data/")
        >>> async for batch in extractor.extract():
        ...     process(batch)
    
    2. Config-driven:
        >>> extractor = CloudStorageExtractor()
        >>> async for batch in extractor.extract_streaming(config, params, headers):
        ...     process(batch)
    """
    
    def __init__(
        self,
        provider: Optional[str] = None,
        bucket: Optional[str] = None,
        path: Optional[str] = None,
        credentials: Optional[Dict[str, Any]] = None,
        file_format: Optional[str] = None,
        batch_size: int = 1000,
        max_records: Optional[int] = None,
    ):
        self.provider = provider
        self.bucket = bucket
        self.path = path
        self.credentials = credentials
        self.file_format = file_format
        self.batch_size = batch_size
        self.max_records = max_records
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "CloudStorageExtractor":
        """Create extractor from configuration dict."""
        storage_config = config.get("storage", {})
        return cls(
            provider=storage_config.get("provider") or config.get("provider"),
            bucket=storage_config.get("bucket") or config.get("bucket"),
            path=storage_config.get("path") or config.get("path"),
            credentials=storage_config.get("credentials") or config.get("credentials"),
            file_format=config.get("format"),
            batch_size=config.get("batch_size", 1000),
            max_records=config.get("max_records"),
        )
    
    async def extract(self, **params) -> AsyncIterator[List[Dict[str, Any]]]:
        """
        Extract data from cloud storage.
        
        Yields:
            Batches of records
        """
        if not self.provider:
            raise ValueError("Provider is required (s3, gcs, azure)")
        if not self.bucket:
            raise ValueError("Bucket is required")
        if not self.path:
            raise ValueError("Path is required")
        
        extract_config = {
            "storage": {
                "provider": self.provider,
                "bucket": self.bucket,
                "path": self.path,
                "credentials": self.credentials,
            },
            "format": self.file_format,
        }
        
        async for batch in self.extract_streaming(
            extract_config, {}, {},
            batch_size=self.batch_size,
            max_records=self.max_records,
        ):
            yield batch
    
    def validate_config(self, extract_config: Dict[str, Any]) -> None:
        """Validate cloud storage extractor configuration."""
        if 'source_type' in extract_config and extract_config['source_type'] != 'cloud_storage':
            raise ValueError(
                f"CloudStorageExtractor requires source_type='cloud_storage', "
                f"got '{extract_config.get('source_type')}'"
            )
        
        storage_config = extract_config.get('storage', {})
        provider = storage_config.get('provider', '').lower()
        
        if provider not in ['s3', 'gcs', 'azure']:
            raise ValueError(
                f"Cloud storage provider must be 's3', 'gcs', or 'azure', got '{provider}'"
            )
        
        if not storage_config.get('bucket'):
            raise ValueError("Cloud storage extractor requires 'storage.bucket' in extract_config")
        
        if not storage_config.get('path'):
            raise ValueError("Cloud storage extractor requires 'storage.path' in extract_config")
    
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
        Extract data from cloud storage.
        
        Downloads files from cloud storage and processes them using FileExtractor.
        Supports single files and prefixes (for multiple files).
        """
        storage_config = extract_config.get('storage', {})
        provider = storage_config.get('provider', '').lower()
        
        # Resolve variables
        source_file = str(contract_dir / "extract.yaml") if contract_dir else None
        bucket = resolve_values(storage_config.get('bucket'), context=config_context, source_file=source_file)
        path = resolve_values(storage_config.get('path'), context=config_context, source_file=source_file)
        credentials = storage_config.get('credentials')
        
        # Detect format
        file_format = extract_config.get('format')
        if not file_format:
            # Try to detect from path
            path_obj = Path(path)
            file_format = self._detect_format_from_path(path_obj)
        
        logger.info(f"Extracting from {provider.upper()}: {bucket}/{path}")
        
        # Download and process files
        if provider == 's3':
            async for batch in self._extract_from_s3(
                bucket, path, credentials, file_format, batch_size, max_records, config_context, source_file
            ):
                yield batch
        elif provider == 'gcs':
            async for batch in self._extract_from_gcs(
                bucket, path, credentials, file_format, batch_size, max_records, config_context, source_file
            ):
                yield batch
        elif provider == 'azure':
            async for batch in self._extract_from_azure(
                bucket, path, credentials, file_format, batch_size, max_records, config_context, source_file
            ):
                yield batch
        else:
            raise ValueError(f"Unsupported cloud storage provider: {provider}")
    
    async def _extract_from_s3(
        self,
        bucket: str,
        path: str,
        credentials: Optional[Dict[str, Any]],
        file_format: Optional[str],
        batch_size: int,
        max_records: Optional[int],
        config_context: Optional[Dict[str, Any]],
        source_file: Optional[str],
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """Extract data from AWS S3."""
        if not S3_AVAILABLE:
            raise ImportError(
                "boto3 is required for S3 extraction. "
                "Install with: pip install boto3 or pip install pycharter[etl]"
            )
        
        # Initialize S3 client
        s3_client = boto3.client('s3')
        
        # Handle credentials if provided
        if credentials:
            if isinstance(credentials, dict):
                aws_access_key_id = credentials.get('aws_access_key_id')
                aws_secret_access_key = credentials.get('aws_secret_access_key')
                region = credentials.get('region', 'us-east-1')
                
                if aws_access_key_id and aws_secret_access_key:
                    s3_client = boto3.client(
                        's3',
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key,
                        region_name=region,
                    )
        
        # Check if path is a prefix (ends with / or contains *)
        if path.endswith('/') or '*' in path:
            # List objects with prefix
            prefix = path.rstrip('/')
            if '*' in prefix:
                # Convert glob pattern to prefix
                prefix = prefix.split('*')[0]
            
            paginator = s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket, Prefix=prefix)
            
            total_extracted = 0
            for page in pages:
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    if max_records and total_extracted >= max_records:
                        break
                    
                    key = obj['Key']
                    logger.info(f"Processing S3 object: {bucket}/{key}")
                    
                    # Download file to temp location
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(key).suffix) as tmp_file:
                        try:
                            s3_client.download_fileobj(bucket, key, tmp_file)
                            tmp_path = Path(tmp_file.name)
                            
                            # Use FileExtractor to process the file
                            file_extractor = FileExtractor()
                            file_config = {
                                'source_type': 'file',
                                'file_path': str(tmp_path),
                                'format': file_format,
                            }
                            
                            async for batch in file_extractor.extract_streaming(
                                file_config, {}, {}, None, batch_size, max_records, config_context
                            ):
                                total_extracted += len(batch)
                                yield batch
                                if max_records and total_extracted >= max_records:
                                    break
                        finally:
                            # Cleanup temp file
                            if tmp_path.exists():
                                tmp_path.unlink()
        else:
            # Single file
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(path).suffix) as tmp_file:
                try:
                    s3_client.download_fileobj(bucket, path, tmp_file)
                    tmp_path = Path(tmp_file.name)
                    
                    # Use FileExtractor to process the file
                    file_extractor = FileExtractor()
                    file_config = {
                        'source_type': 'file',
                        'file_path': str(tmp_path),
                        'format': file_format,
                    }
                    
                    async for batch in file_extractor.extract_streaming(
                        file_config, {}, {}, None, batch_size, max_records, config_context
                    ):
                        yield batch
                finally:
                    if tmp_path.exists():
                        tmp_path.unlink()
    
    async def _extract_from_gcs(
        self,
        bucket: str,
        path: str,
        credentials: Optional[Dict[str, Any]],
        file_format: Optional[str],
        batch_size: int,
        max_records: Optional[int],
        config_context: Optional[Dict[str, Any]],
        source_file: Optional[str],
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """Extract data from Google Cloud Storage."""
        if not GCS_AVAILABLE:
            raise ImportError(
                "google-cloud-storage is required for GCS extraction. "
                "Install with: pip install google-cloud-storage"
            )
        
        # Initialize GCS client
        if credentials:
            # Use provided credentials (path to JSON key file or dict)
            if isinstance(credentials, str):
                client = gcs_storage.Client.from_service_account_json(credentials)
            elif isinstance(credentials, dict):
                # Create temporary JSON file
                import json
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                    json.dump(credentials, tmp)
                    tmp_path = tmp.name
                try:
                    client = gcs_storage.Client.from_service_account_json(tmp_path)
                finally:
                    Path(tmp_path).unlink()
            else:
                client = gcs_storage.Client()
        else:
            client = gcs_storage.Client()
        
        bucket_obj = client.bucket(bucket)
        
        # Check if path is a prefix
        if path.endswith('/') or '*' in path:
            prefix = path.rstrip('/')
            if '*' in prefix:
                prefix = prefix.split('*')[0]
            
            blobs = bucket_obj.list_blobs(prefix=prefix)
            
            total_extracted = 0
            for blob in blobs:
                if max_records and total_extracted >= max_records:
                    break
                
                logger.info(f"Processing GCS blob: {bucket}/{blob.name}")
                
                # Download to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(blob.name).suffix) as tmp_file:
                    try:
                        blob.download_to_filename(tmp_file.name)
                        tmp_path = Path(tmp_file.name)
                        
                        # Use FileExtractor
                        file_extractor = FileExtractor()
                        file_config = {
                            'source_type': 'file',
                            'file_path': str(tmp_path),
                            'format': file_format,
                        }
                        
                        async for batch in file_extractor.extract_streaming(
                            file_config, {}, {}, None, batch_size, max_records, config_context
                        ):
                            total_extracted += len(batch)
                            yield batch
                            if max_records and total_extracted >= max_records:
                                break
                    finally:
                        if tmp_path.exists():
                            tmp_path.unlink()
        else:
            # Single file
            blob = bucket_obj.blob(path)
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(path).suffix) as tmp_file:
                try:
                    blob.download_to_filename(tmp_file.name)
                    tmp_path = Path(tmp_file.name)
                    
                    # Use FileExtractor
                    file_extractor = FileExtractor()
                    file_config = {
                        'source_type': 'file',
                        'file_path': str(tmp_path),
                        'format': file_format,
                    }
                    
                    async for batch in file_extractor.extract_streaming(
                        file_config, {}, {}, None, batch_size, max_records, config_context
                    ):
                        yield batch
                finally:
                    if tmp_path.exists():
                        tmp_path.unlink()
    
    async def _extract_from_azure(
        self,
        container: str,
        path: str,
        credentials: Optional[Dict[str, Any]],
        file_format: Optional[str],
        batch_size: int,
        max_records: Optional[int],
        config_context: Optional[Dict[str, Any]],
        source_file: Optional[str],
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """Extract data from Azure Blob Storage."""
        if not AZURE_AVAILABLE:
            raise ImportError(
                "azure-storage-blob is required for Azure extraction. "
                "Install with: pip install azure-storage-blob"
            )
        
        # Initialize Azure client
        if credentials:
            connection_string = credentials.get('connection_string')
            account_name = credentials.get('account_name')
            account_key = credentials.get('account_key')
            
            if connection_string:
                blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            elif account_name and account_key:
                account_url = f"https://{account_name}.blob.core.windows.net"
                blob_service_client = BlobServiceClient(account_url, credential=account_key)
            else:
                raise ValueError("Azure credentials must include 'connection_string' or ('account_name', 'account_key')")
        else:
            # Use default credentials (environment variables)
            blob_service_client = BlobServiceClient.from_connection_string(
                os.environ.get('AZURE_STORAGE_CONNECTION_STRING', '')
            )
        
        container_client = blob_service_client.get_container_client(container)
        
        # Check if path is a prefix
        if path.endswith('/') or '*' in path:
            prefix = path.rstrip('/')
            if '*' in prefix:
                prefix = prefix.split('*')[0]
            
            blobs = container_client.list_blobs(name_starts_with=prefix)
            
            total_extracted = 0
            for blob in blobs:
                if max_records and total_extracted >= max_records:
                    break
                
                logger.info(f"Processing Azure blob: {container}/{blob.name}")
                
                # Download to temp file
                blob_client = container_client.get_blob_client(blob.name)
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(blob.name).suffix) as tmp_file:
                    try:
                        blob_data = blob_client.download_blob()
                        blob_data.download_to_stream(tmp_file)
                        tmp_path = Path(tmp_file.name)
                        
                        # Use FileExtractor
                        file_extractor = FileExtractor()
                        file_config = {
                            'source_type': 'file',
                            'file_path': str(tmp_path),
                            'format': file_format,
                        }
                        
                        async for batch in file_extractor.extract_streaming(
                            file_config, {}, {}, None, batch_size, max_records, config_context
                        ):
                            total_extracted += len(batch)
                            yield batch
                            if max_records and total_extracted >= max_records:
                                break
                    finally:
                        if tmp_path.exists():
                            tmp_path.unlink()
        else:
            # Single file
            blob_client = container_client.get_blob_client(path)
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(path).suffix) as tmp_file:
                try:
                    blob_data = blob_client.download_blob()
                    blob_data.download_to_stream(tmp_file)
                    tmp_path = Path(tmp_file.name)
                    
                    # Use FileExtractor
                    file_extractor = FileExtractor()
                    file_config = {
                        'source_type': 'file',
                        'file_path': str(tmp_path),
                        'format': file_format,
                    }
                    
                    async for batch in file_extractor.extract_streaming(
                        file_config, {}, {}, None, batch_size, max_records, config_context
                    ):
                        yield batch
                finally:
                    if tmp_path.exists():
                        tmp_path.unlink()
    
    def _detect_format_from_path(self, path: Path) -> Optional[str]:
        """Detect file format from path extension."""
        suffix = path.suffix.lower()
        format_map = {
            '.csv': 'csv',
            '.tsv': 'tsv',
            '.json': 'json',
            '.jsonl': 'jsonl',
            '.ndjson': 'jsonl',
            '.parquet': 'parquet',
            '.xlsx': 'excel',
            '.xls': 'excel',
            '.xml': 'xml',
        }
        return format_map.get(suffix)

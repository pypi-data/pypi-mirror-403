"""
File-based extractor for ETL orchestrator.

Supports reading from local files in various formats:
- CSV, TSV
- JSON (single file or newline-delimited JSON)
- Parquet
- Excel (xlsx, xls)
- XML
"""

import gzip
import json
import logging
import zipfile
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

import pandas as pd

from pycharter.etl_generator.extractors.base import BaseExtractor
from pycharter.utils.value_injector import resolve_values

logger = logging.getLogger(__name__)

# Supported file formats
SUPPORTED_FORMATS = {
    '.csv': 'csv',
    '.tsv': 'tsv',
    '.json': 'json',
    '.jsonl': 'jsonl',  # Newline-delimited JSON
    '.ndjson': 'jsonl',
    '.parquet': 'parquet',
    '.xlsx': 'excel',
    '.xls': 'excel',
    '.xml': 'xml',
}


class FileExtractor(BaseExtractor):
    """
    Extractor for file-based data sources.
    
    Supports two modes:
    1. Programmatic API:
        >>> extractor = FileExtractor(path="data.csv")
        >>> async for batch in extractor.extract():
        ...     process(batch)
    
    2. Config-driven:
        >>> extractor = FileExtractor()
        >>> async for batch in extractor.extract_streaming(config, params, headers):
        ...     process(batch)
    """
    
    def __init__(
        self,
        path: Optional[str] = None,
        file_format: Optional[str] = None,
        batch_size: int = 1000,
        max_records: Optional[int] = None,
    ):
        self.path = path
        self.file_format = file_format
        self.batch_size = batch_size
        self.max_records = max_records
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "FileExtractor":
        """Create extractor from configuration dict."""
        return cls(
            path=config.get("file_path") or config.get("path"),
            file_format=config.get("format"),
            batch_size=config.get("batch_size", 1000),
            max_records=config.get("max_records"),
        )
    
    async def extract(self, **params) -> AsyncIterator[List[Dict[str, Any]]]:
        """
        Extract data from file.
        
        Yields:
            Batches of records
        """
        if not self.path:
            raise ValueError("File path is required")
        
        extract_config = {
            "file_path": self.path,
            "format": self.file_format,
        }
        
        async for batch in self.extract_streaming(
            extract_config, {}, {},
            batch_size=self.batch_size,
            max_records=self.max_records,
        ):
            yield batch
    
    def validate_config(self, extract_config: Dict[str, Any]) -> None:
        """Validate file extractor configuration."""
        if 'source_type' in extract_config and extract_config['source_type'] != 'file':
            raise ValueError(f"FileExtractor requires source_type='file', got '{extract_config.get('source_type')}'")
        
        file_path = extract_config.get('file_path')
        if not file_path:
            raise ValueError("File extractor requires 'file_path' in extract_config")
    
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
        Extract data from file(s) in batches.
        
        Supports:
        - Single files
        - Glob patterns for multiple files
        - Compressed files (gzip, zip)
        """
        # Resolve file_path with variable injection
        source_file = str(contract_dir / "extract.yaml") if contract_dir else None
        file_path = extract_config.get('file_path')
        if not file_path:
            raise ValueError("File extractor requires 'file_path' in extract_config")
        
        file_path = resolve_values(file_path, context=config_context, source_file=source_file)
        
        # Detect format
        file_format = extract_config.get('format')
        if not file_format:
            file_format = self._detect_format(file_path)
        
        # Handle glob patterns
        path = Path(file_path)
        if '*' in str(path) or '?' in str(path):
            # Glob pattern - process multiple files
            files = list(path.parent.glob(path.name))
            if not files:
                raise FileNotFoundError(f"No files found matching pattern: {file_path}")
            logger.info(f"Found {len(files)} files matching pattern: {file_path}")
            
            total_extracted = 0
            for file in sorted(files):
                if max_records and total_extracted >= max_records:
                    break
                
                logger.info(f"Processing file: {file}")
                async for batch in self._extract_from_file(
                    file, file_format, batch_size, max_records, total_extracted
                ):
                    total_extracted += len(batch)
                    yield batch
                    if max_records and total_extracted >= max_records:
                        break
        else:
            # Single file
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            async for batch in self._extract_from_file(
                path, file_format, batch_size, max_records, 0
            ):
                yield batch
    
    async def _extract_from_file(
        self,
        file_path: Path,
        file_format: str,
        batch_size: int,
        max_records: Optional[int],
        offset: int = 0,
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """Extract data from a single file."""
        extracted_file = None
        original_path = file_path
        
        # Handle compressed files
        if file_path.suffix == '.gz':
            # Gzip compressed - pandas can handle this directly
            # No need to decompress manually
            pass
        elif file_path.suffix == '.zip':
            # Zip file - extract first file
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                if not file_list:
                    raise ValueError(f"Zip file is empty: {file_path}")
                # Use first file in zip
                extracted_file = zip_ref.extract(file_list[0])
                file_path = Path(extracted_file)
        
        try:
            if file_format == 'csv' or file_format == 'tsv':
                async for batch in self._extract_csv(file_path, batch_size, max_records, offset, file_format):
                    yield batch
            elif file_format == 'json':
                async for batch in self._extract_json(file_path, batch_size, max_records, offset):
                    yield batch
            elif file_format == 'jsonl':
                async for batch in self._extract_jsonl(file_path, batch_size, max_records, offset):
                    yield batch
            elif file_format == 'parquet':
                async for batch in self._extract_parquet(file_path, batch_size, max_records, offset):
                    yield batch
            elif file_format == 'excel':
                async for batch in self._extract_excel(file_path, batch_size, max_records, offset):
                    yield batch
            elif file_format == 'xml':
                async for batch in self._extract_xml(file_path, batch_size, max_records, offset):
                    yield batch
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
        finally:
            # Cleanup if we extracted from zip
            if extracted_file and Path(extracted_file).exists():
                Path(extracted_file).unlink()
    
    async def _extract_csv(
        self,
        file_path: Path,
        batch_size: int,
        max_records: Optional[int],
        offset: int,
        format_type: str,
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """Extract data from CSV/TSV file."""
        delimiter = '\t' if format_type == 'tsv' else ','
        
        # Use pandas for efficient CSV reading
        chunk_size = batch_size
        total_read = 0
        
        try:
            for chunk in pd.read_csv(
                file_path,
                delimiter=delimiter,
                chunksize=chunk_size,
                skiprows=offset if offset > 0 else None,
            ):
                records = chunk.to_dict('records')
                
                # Convert pandas types to native Python types
                records = [self._convert_pandas_types(record) for record in records]
                
                if max_records and total_read + len(records) > max_records:
                    records = records[:max_records - total_read]
                
                total_read += len(records)
                yield records
                
                if max_records and total_read >= max_records:
                    break
        except Exception as e:
            raise RuntimeError(f"Error reading CSV file {file_path}: {e}") from e
    
    async def _extract_json(
        self,
        file_path: Path,
        batch_size: int,
        max_records: Optional[int],
        offset: int,
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """Extract data from JSON file."""
        try:
            # Handle gzip compressed JSON
            if file_path.suffix == ".gz":
                with gzip.open(file_path, "rt", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                # Try to find array in common keys
                for key in ['data', 'results', 'items', 'records', 'values']:
                    if key in data and isinstance(data[key], list):
                        records = data[key]
                        break
                else:
                    # Single object
                    records = [data]
            else:
                raise ValueError(f"JSON file must contain a list or dict, got {type(data)}")
            
            # Apply offset and max_records
            if offset > 0:
                records = records[offset:]
            if max_records:
                records = records[:max_records]
            
            # Yield in batches
            for i in range(0, len(records), batch_size):
                yield records[i:i + batch_size]
        except Exception as e:
            raise RuntimeError(f"Error reading JSON file {file_path}: {e}") from e
    
    async def _extract_jsonl(
        self,
        file_path: Path,
        batch_size: int,
        max_records: Optional[int],
        offset: int,
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """Extract data from newline-delimited JSON file."""
        try:
            current_batch = []
            total_read = 0
            skipped = 0
            
            # Handle gzip compressed JSONL
            if file_path.suffix == '.gz':
                import gzip
                file_handle = gzip.open(file_path, 'rt', encoding='utf-8')
            else:
                file_handle = open(file_path, 'r', encoding='utf-8')
            
            with file_handle as f:
                for line in f:
                    # Skip lines until offset
                    if skipped < offset:
                        skipped += 1
                        continue
                    
                    if max_records and total_read >= max_records:
                        break
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        record = json.loads(line)
                        current_batch.append(record)
                        total_read += 1
                        
                        if len(current_batch) >= batch_size:
                            yield current_batch
                            current_batch = []
                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping invalid JSON line in {file_path}: {e}")
                        continue
                
                # Yield remaining records
                if current_batch:
                    yield current_batch
        except Exception as e:
            raise RuntimeError(f"Error reading JSONL file {file_path}: {e}") from e
    
    async def _extract_parquet(
        self,
        file_path: Path,
        batch_size: int,
        max_records: Optional[int],
        offset: int,
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """Extract data from Parquet file."""
        try:
            # Read parquet file
            df = pd.read_parquet(file_path)
            
            # Apply offset
            if offset > 0:
                df = df.iloc[offset:]
            
            # Apply max_records
            if max_records:
                df = df.head(max_records)
            
            # Yield in batches
            for i in range(0, len(df), batch_size):
                chunk = df.iloc[i:i + batch_size]
                records = chunk.to_dict('records')
                records = [self._convert_pandas_types(record) for record in records]
                yield records
        except Exception as e:
            raise RuntimeError(f"Error reading Parquet file {file_path}: {e}") from e
    
    async def _extract_excel(
        self,
        file_path: Path,
        batch_size: int,
        max_records: Optional[int],
        offset: int,
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """Extract data from Excel file."""
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Apply offset
            if offset > 0:
                df = df.iloc[offset:]
            
            # Apply max_records
            if max_records:
                df = df.head(max_records)
            
            # Yield in batches
            for i in range(0, len(df), batch_size):
                chunk = df.iloc[i:i + batch_size]
                records = chunk.to_dict('records')
                records = [self._convert_pandas_types(record) for record in records]
                yield records
        except Exception as e:
            raise RuntimeError(f"Error reading Excel file {file_path}: {e}") from e
    
    async def _extract_xml(
        self,
        file_path: Path,
        batch_size: int,
        max_records: Optional[int],
        offset: int,
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """Extract data from XML file."""
        try:
            # Use pandas to read XML (requires lxml)
            df = pd.read_xml(file_path)
            
            # Apply offset
            if offset > 0:
                df = df.iloc[offset:]
            
            # Apply max_records
            if max_records:
                df = df.head(max_records)
            
            # Yield in batches
            for i in range(0, len(df), batch_size):
                chunk = df.iloc[i:i + batch_size]
                records = chunk.to_dict('records')
                records = [self._convert_pandas_types(record) for record in records]
                yield records
        except Exception as e:
            raise RuntimeError(f"Error reading XML file {file_path}: {e}") from e
    
    def _detect_format(self, file_path: str) -> str:
        """Detect file format from extension."""
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        if suffix in SUPPORTED_FORMATS:
            return SUPPORTED_FORMATS[suffix]
        
        # Check for compressed files
        if suffix == '.gz':
            # Remove .gz and check again
            stem_suffix = path.stem.split('.')[-1] if '.' in path.stem else ''
            if f'.{stem_suffix}' in SUPPORTED_FORMATS:
                return SUPPORTED_FORMATS[f'.{stem_suffix}']
        
        raise ValueError(f"Could not detect file format from extension: {suffix}")
    
    def _convert_pandas_types(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Convert pandas types to native Python types."""
        converted = {}
        for key, value in record.items():
            if pd.isna(value):
                converted[key] = None
            elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                converted[key] = value.isoformat()
            elif isinstance(value, pd.Timedelta):
                converted[key] = str(value)
            else:
                converted[key] = value
        return converted

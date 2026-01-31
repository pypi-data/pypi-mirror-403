"""
Tests for modular extractor architecture.

These tests verify that the extractor factory and individual extractors
work correctly with different source types.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from pycharter.etl_generator.extractors.factory import ExtractorFactory
from pycharter.etl_generator.extractors.http import HTTPExtractor
from pycharter.etl_generator.extractors.file import FileExtractor
from pycharter.etl_generator.extractors.database import DatabaseExtractor
from pycharter.etl_generator.extractors.cloud_storage import CloudStorageExtractor


class TestExtractorFactory:
    """Tests for ExtractorFactory."""
    
    def test_get_http_extractor(self):
        """Test getting HTTP extractor."""
        config = {
            'source_type': 'http',
            'base_url': 'https://api.example.com',
            'api_endpoint': '/v1/data',
        }
        extractor = ExtractorFactory.get_extractor(config)
        assert isinstance(extractor, HTTPExtractor)
    
    def test_get_file_extractor(self):
        """Test getting file extractor."""
        config = {
            'source_type': 'file',
            'file_path': '/path/to/data.csv',
        }
        extractor = ExtractorFactory.get_extractor(config)
        assert isinstance(extractor, FileExtractor)
    
    def test_get_database_extractor(self):
        """Test getting database extractor."""
        config = {
            'source_type': 'database',
            'database': {'url': 'postgresql://localhost/db'},
            'query': 'SELECT * FROM table',
        }
        extractor = ExtractorFactory.get_extractor(config)
        assert isinstance(extractor, DatabaseExtractor)
    
    def test_get_cloud_storage_extractor(self):
        """Test getting cloud storage extractor."""
        config = {
            'source_type': 'cloud_storage',
            'storage': {
                'provider': 's3',
                'bucket': 'my-bucket',
                'path': 'data/file.csv',
            },
        }
        extractor = ExtractorFactory.get_extractor(config)
        assert isinstance(extractor, CloudStorageExtractor)
    
    def test_auto_detect_http(self):
        """Test auto-detection of HTTP source type."""
        config = {
            'base_url': 'https://api.example.com',
            'api_endpoint': '/v1/data',
        }
        extractor = ExtractorFactory.get_extractor(config)
        assert isinstance(extractor, HTTPExtractor)
    
    def test_auto_detect_file(self):
        """Test auto-detection of file source type."""
        config = {
            'file_path': '/path/to/data.csv',
        }
        extractor = ExtractorFactory.get_extractor(config)
        assert isinstance(extractor, FileExtractor)
    
    def test_auto_detect_database(self):
        """Test auto-detection of database source type."""
        config = {
            'database': {'url': 'postgresql://localhost/db'},
            'query': 'SELECT * FROM table',
        }
        extractor = ExtractorFactory.get_extractor(config)
        assert isinstance(extractor, DatabaseExtractor)
    
    def test_auto_detect_cloud_storage(self):
        """Test auto-detection of cloud storage source type."""
        config = {
            'storage': {
                'provider': 's3',
                'bucket': 'my-bucket',
                'path': 'data/file.csv',
            },
        }
        extractor = ExtractorFactory.get_extractor(config)
        assert isinstance(extractor, CloudStorageExtractor)
    
    def test_unknown_source_type(self):
        """Test error handling for unknown source type."""
        config = {
            'source_type': 'unknown',
        }
        with pytest.raises(ValueError, match="Unknown source_type"):
            ExtractorFactory.get_extractor(config)
    
    def test_register_custom_extractor(self):
        """Test registering a custom extractor."""
        from pycharter.etl_generator.extractors.base import BaseExtractor
        
        class CustomExtractor(BaseExtractor):
            async def extract_streaming(self, *args, **kwargs):
                yield []
        
        ExtractorFactory.register_extractor('custom', CustomExtractor)
        
        config = {'source_type': 'custom'}
        extractor = ExtractorFactory.get_extractor(config)
        assert isinstance(extractor, CustomExtractor)


class TestHTTPExtractor:
    """Tests for HTTPExtractor."""
    
    def test_validate_config(self):
        """Test HTTP extractor config validation."""
        extractor = HTTPExtractor()
        
        # Valid config
        config = {
            'source_type': 'http',
            'base_url': 'https://api.example.com',
            'api_endpoint': '/v1/data',
        }
        extractor.validate_config(config)  # Should not raise
        
        # Invalid source type
        config['source_type'] = 'file'
        with pytest.raises(ValueError):
            extractor.validate_config(config)
        
        # Missing required fields
        config = {'source_type': 'http'}
        with pytest.raises(ValueError):
            extractor.validate_config(config)


class TestFileExtractor:
    """Tests for FileExtractor."""
    
    def test_validate_config(self):
        """Test file extractor config validation."""
        extractor = FileExtractor()
        
        # Valid config
        config = {
            'source_type': 'file',
            'file_path': '/path/to/data.csv',
        }
        extractor.validate_config(config)  # Should not raise
        
        # Invalid source type
        config['source_type'] = 'http'
        with pytest.raises(ValueError):
            extractor.validate_config(config)
        
        # Missing file_path
        config = {'source_type': 'file'}
        with pytest.raises(ValueError):
            extractor.validate_config(config)
    
    def test_detect_format(self):
        """Test file format detection."""
        extractor = FileExtractor()
        
        assert extractor._detect_format('/path/to/data.csv') == 'csv'
        assert extractor._detect_format('/path/to/data.json') == 'json'
        assert extractor._detect_format('/path/to/data.parquet') == 'parquet'
        assert extractor._detect_format('/path/to/data.xlsx') == 'excel'
        
        with pytest.raises(ValueError):
            extractor._detect_format('/path/to/data.unknown')


class TestDatabaseExtractor:
    """Tests for DatabaseExtractor."""
    
    def test_validate_config(self):
        """Test database extractor config validation."""
        extractor = DatabaseExtractor()
        
        # Valid config
        config = {
            'source_type': 'database',
            'database': {'url': 'postgresql://localhost/db'},
            'query': 'SELECT * FROM table',
        }
        extractor.validate_config(config)  # Should not raise
        
        # Invalid source type
        config['source_type'] = 'http'
        with pytest.raises(ValueError):
            extractor.validate_config(config)
        
        # Missing database URL
        config = {
            'source_type': 'database',
            'query': 'SELECT * FROM table',
        }
        with pytest.raises(ValueError):
            extractor.validate_config(config)
        
        # Missing query
        config = {
            'source_type': 'database',
            'database': {'url': 'postgresql://localhost/db'},
        }
        with pytest.raises(ValueError):
            extractor.validate_config(config)


class TestCloudStorageExtractor:
    """Tests for CloudStorageExtractor."""
    
    def test_validate_config(self):
        """Test cloud storage extractor config validation."""
        extractor = CloudStorageExtractor()
        
        # Valid config
        config = {
            'source_type': 'cloud_storage',
            'storage': {
                'provider': 's3',
                'bucket': 'my-bucket',
                'path': 'data/file.csv',
            },
        }
        extractor.validate_config(config)  # Should not raise
        
        # Invalid source type
        config['source_type'] = 'http'
        with pytest.raises(ValueError):
            extractor.validate_config(config)
        
        # Invalid provider
        config = {
            'source_type': 'cloud_storage',
            'storage': {
                'provider': 'unknown',
                'bucket': 'my-bucket',
                'path': 'data/file.csv',
            },
        }
        with pytest.raises(ValueError):
            extractor.validate_config(config)
        
        # Missing bucket
        config = {
            'source_type': 'cloud_storage',
            'storage': {
                'provider': 's3',
                'path': 'data/file.csv',
            },
        }
        with pytest.raises(ValueError):
            extractor.validate_config(config)
        
        # Missing path
        config = {
            'source_type': 'cloud_storage',
            'storage': {
                'provider': 's3',
                'bucket': 'my-bucket',
            },
        }
        with pytest.raises(ValueError):
            extractor.validate_config(config)

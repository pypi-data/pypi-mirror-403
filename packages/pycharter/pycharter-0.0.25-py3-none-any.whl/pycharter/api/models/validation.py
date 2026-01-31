"""
Request/Response models for validation endpoints.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ValidationRequest(BaseModel):
    """Request model for validating data."""
    
    schema_id: Optional[str] = Field(None, description="Schema identifier (for store-based validation)")
    contract: Optional[Dict[str, Any]] = Field(None, description="Contract dictionary (for contract-based validation)")
    data: Dict[str, Any] = Field(..., description="Data to validate")
    version: Optional[str] = Field(None, description="Schema version (default: latest)")
    strict: bool = Field(False, description="If True, raise exceptions on validation errors")
    include_quality: bool = Field(False, description="If True, include quality metrics in response")
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema_id": "user_schema",
                "data": {
                    "name": "Alice",
                    "age": 30
                },
                "version": "1.0.0",
                "strict": False,
                "include_quality": False
            }
        }


class ValidationErrorDetail(BaseModel):
    """Detail model for validation errors."""
    
    field: str = Field(..., description="Field name with error")
    message: str = Field(..., description="Error message")
    input_value: Any = Field(..., description="Input value that caused the error")
    
    class Config:
        json_schema_extra = {
            "example": {
                "field": "age",
                "message": "Input should be greater than or equal to 0",
                "input_value": -5
            }
        }


class ValidationQualityMetrics(BaseModel):
    """Quality metrics for validated data."""
    
    completeness: float = Field(..., description="Ratio of non-null fields (0.0 to 1.0)")
    field_completeness: Dict[str, float] = Field(default_factory=dict, description="Per-field completeness ratios")
    record_count: int = Field(0, description="Number of records validated")
    valid_count: int = Field(0, description="Number of valid records")
    error_count: int = Field(0, description="Number of records with errors")
    validity_rate: float = Field(..., description="Ratio of valid records")
    
    class Config:
        json_schema_extra = {
            "example": {
                "completeness": 0.95,
                "field_completeness": {"name": 1.0, "age": 0.9, "email": 0.85},
                "record_count": 100,
                "valid_count": 95,
                "error_count": 5,
                "validity_rate": 0.95
            }
        }


class ValidationResponse(BaseModel):
    """Response model for validation result."""
    
    is_valid: bool = Field(..., description="Whether validation passed")
    data: Optional[Dict[str, Any]] = Field(None, description="Validated data (if valid)")
    errors: List[ValidationErrorDetail] = Field(default_factory=list, description="Validation errors (if invalid)")
    error_count: int = Field(0, description="Number of validation errors")
    quality: Optional[ValidationQualityMetrics] = Field(None, description="Quality metrics (if requested)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_valid": True,
                "data": {
                    "name": "Alice",
                    "age": 30
                },
                "errors": [],
                "error_count": 0,
                "quality": None
            }
        }


class ValidationBatchRequest(BaseModel):
    """Request model for batch validation."""
    
    schema_id: Optional[str] = Field(None, description="Schema identifier (for store-based validation)")
    contract: Optional[Dict[str, Any]] = Field(None, description="Contract dictionary (for contract-based validation)")
    data_list: List[Dict[str, Any]] = Field(..., description="List of data dictionaries to validate")
    version: Optional[str] = Field(None, description="Schema version (default: latest)")
    strict: bool = Field(False, description="If True, raise exceptions on validation errors")
    include_quality: bool = Field(False, description="If True, include quality metrics in response")
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema_id": "user_schema",
                "data_list": [
                    {"name": "Alice", "age": 30},
                    {"name": "Bob", "age": 25}
                ],
                "version": "1.0.0",
                "strict": False,
                "include_quality": False
            }
        }


class ValidationBatchResponse(BaseModel):
    """Response model for batch validation results."""
    
    results: List[ValidationResponse] = Field(..., description="List of validation results")
    total_count: int = Field(..., description="Total number of items validated")
    valid_count: int = Field(..., description="Number of valid items")
    invalid_count: int = Field(..., description="Number of invalid items")
    quality: Optional[ValidationQualityMetrics] = Field(None, description="Aggregate quality metrics (if requested)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "results": [
                    {
                        "is_valid": True,
                        "data": {"name": "Alice", "age": 30},
                        "errors": [],
                        "error_count": 0,
                        "quality": None
                    },
                    {
                        "is_valid": False,
                        "data": None,
                        "errors": [
                            {
                                "field": "age",
                                "message": "Input should be greater than or equal to 0",
                                "input_value": -5
                            }
                        ],
                        "error_count": 1,
                        "quality": None
                    }
                ],
                "total_count": 2,
                "valid_count": 1,
                "invalid_count": 1,
                "quality": {
                    "completeness": 0.95,
                    "field_completeness": {"name": 1.0, "age": 0.9},
                    "record_count": 2,
                    "valid_count": 1,
                    "error_count": 1,
                    "validity_rate": 0.5
                }
            }
        }


"""
Route handlers for runtime validation.

Supports the new ValidatorBuilder API with quality metrics.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from pycharter import Validator, ValidatorBuilder
from pycharter.api.dependencies.store import get_metadata_store
from pycharter.api.models.validation import (
    ValidationBatchRequest,
    ValidationBatchResponse,
    ValidationErrorDetail,
    ValidationQualityMetrics,
    ValidationRequest,
    ValidationResponse,
)
from pycharter.metadata_store import MetadataStoreClient

router = APIRouter()


def _parse_validation_errors(errors: list) -> list:
    """
    Parse validation errors from ValidationResult into ValidationErrorDetail objects.
    
    Args:
        errors: List of error strings or dicts from ValidationResult
        
    Returns:
        List of ValidationErrorDetail objects
    """
    parsed_errors = []
    for error in errors:
        if isinstance(error, dict):
            parsed_errors.append(
                ValidationErrorDetail(
                    field=error.get("field", "unknown"),
                    message=error.get("message", "Validation error"),
                    input_value=error.get("input_value"),
                )
            )
        else:
            # Parse string format: "('field_name',): error message"
            error_str = str(error)
            field = "unknown"
            message = error_str
            
            if ": " in error_str:
                parts = error_str.split(": ", 1)
                if len(parts) == 2:
                    field_part = parts[0].strip()
                    message = parts[1].strip()
                    
                    # Extract field name from tuple-like string
                    if field_part.startswith("(") and field_part.endswith(")"):
                        field_content = field_part[1:-1].strip()
                        if field_content.startswith(("'", '"')) and field_content.endswith(("'", '"')):
                            field = field_content[1:-1]
                        else:
                            field = field_content
                    else:
                        field = field_part
            
            parsed_errors.append(
                ValidationErrorDetail(
                    field=field,
                    message=message,
                    input_value=None,
                )
            )
    return parsed_errors


def _build_quality_metrics(quality) -> ValidationQualityMetrics | None:
    """Convert pycharter QualityMetrics to API model."""
    if not quality:
        return None
    return ValidationQualityMetrics(
        completeness=quality.completeness,
        field_completeness=quality.field_completeness,
        record_count=quality.record_count,
        valid_count=quality.valid_count,
        error_count=quality.error_count,
        validity_rate=quality.validity_rate,
    )


@router.post(
    "/validation/validate",
    response_model=ValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate data",
    description="Validate data against a schema from the metadata store or a contract dictionary",
    response_description="Validation result",
)
async def validate_data(
    request: ValidationRequest,
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> ValidationResponse:
    """
    Validate data against a schema.
    
    This endpoint supports two validation modes:
    1. **Store-based**: Use `schema_id` to retrieve schema from metadata store
    2. **Contract-based**: Use `contract` dictionary directly
    
    The validation applies coercion rules (if available) and validation rules
    (if available) in addition to JSON Schema validation.
    
    Optionally includes quality metrics (completeness, validity rate) when
    `include_quality=True`.
    
    Args:
        request: Validation request containing data and either schema_id or contract
        store: Metadata store dependency
        
    Returns:
        Validation result with validated data or errors
        
    Raises:
        HTTPException: If validation fails or required parameters are missing
    """
    # Build validator using ValidatorBuilder
    builder = ValidatorBuilder()
    
    if request.schema_id:
        builder = builder.from_store(store, request.schema_id, request.version)
    elif request.contract:
        builder = builder.from_dict(request.contract)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either schema_id or contract must be provided",
        )
    
    # Configure strict mode and quality checks
    if request.strict:
        builder = builder.strict()
    else:
        builder = builder.lenient()
    
    if request.include_quality:
        builder = builder.with_quality_checks()
    
    # Build and validate
    validator = builder.build()
    result = validator.validate(request.data, include_quality=request.include_quality)
    
    errors = []
    if not result.is_valid and result.errors:
        errors = _parse_validation_errors(result.errors)
    
    return ValidationResponse(
        is_valid=result.is_valid,
        data=result.data.model_dump() if result.data else None,
        errors=errors,
        error_count=len(errors),
        quality=_build_quality_metrics(result.quality),
    )


@router.post(
    "/validation/validate-batch",
    response_model=ValidationBatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate batch of data",
    description="Validate a batch of data records against a schema from the metadata store or a contract dictionary",
    response_description="Batch validation results",
)
async def validate_batch_data(
    request: ValidationBatchRequest,
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> ValidationBatchResponse:
    """
    Validate a batch of data records.
    
    This endpoint validates multiple data records in a single request. It supports
    the same two validation modes as the single validation endpoint:
    1. **Store-based**: Use `schema_id` to retrieve schema from metadata store
    2. **Contract-based**: Use `contract` dictionary directly
    
    Optionally includes aggregate quality metrics when `include_quality=True`.
    
    Args:
        request: Batch validation request containing data_list and either schema_id or contract
        store: Metadata store dependency
        
    Returns:
        Batch validation results with counts and individual results
        
    Raises:
        HTTPException: If batch validation fails or required parameters are missing
    """
    # Build validator using ValidatorBuilder
    builder = ValidatorBuilder()
    
    if request.schema_id:
        builder = builder.from_store(store, request.schema_id, request.version)
    elif request.contract:
        builder = builder.from_dict(request.contract)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either schema_id or contract must be provided",
        )
    
    # Configure strict mode and quality checks
    if request.strict:
        builder = builder.strict()
    else:
        builder = builder.lenient()
    
    if request.include_quality:
        builder = builder.with_quality_checks()
    
    # Build and validate batch
    validator = builder.build()
    results = validator.validate_batch(request.data_list, include_quality=request.include_quality)
    
    response_results = []
    valid_count = 0
    invalid_count = 0
    aggregate_quality = None
    
    for i, result in enumerate(results):
        errors = []
        if not result.is_valid and result.errors:
            errors = _parse_validation_errors(result.errors)
        
        if result.is_valid:
            valid_count += 1
        else:
            invalid_count += 1
        
        # Get aggregate quality from last result
        if i == len(results) - 1 and result.quality:
            aggregate_quality = result.quality
        
        response_results.append(
            ValidationResponse(
                is_valid=result.is_valid,
                data=result.data.model_dump() if result.data else None,
                errors=errors,
                error_count=len(errors),
                quality=None,  # Individual quality not included to keep response size reasonable
            )
        )
    
    return ValidationBatchResponse(
        results=response_results,
        total_count=len(results),
        valid_count=valid_count,
        invalid_count=invalid_count,
        quality=_build_quality_metrics(aggregate_quality),
    )

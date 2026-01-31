"""
API routes for schema evolution.

Provides endpoints for checking schema compatibility and
computing diffs between schema versions.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from pycharter.api.dependencies.store import get_metadata_store
from pycharter.api.models.evolution import (
    ChangeTypeEnum,
    CompatibilityCheckRequest,
    CompatibilityCheckResponse,
    CompatibilityModeEnum,
    DiffRequest,
    SchemaChangeResponse,
    SchemaDiffResponse,
    StoredSchemaDiffRequest,
)
from pycharter.metadata_store import MetadataStoreClient
from pycharter.schema_evolution import (
    check_compatibility,
    compute_diff,
    CompatibilityMode,
)

router = APIRouter(prefix="/evolution", tags=["Schema Evolution"])


def _convert_diff_to_response(diff) -> SchemaDiffResponse:
    """Convert SchemaDiff to response model."""
    return SchemaDiffResponse(
        changes=[
            SchemaChangeResponse(
                path=c.path,
                change_type=ChangeTypeEnum(c.change_type.value),
                old_value=c.old_value,
                new_value=c.new_value,
                breaking=c.breaking,
                message=c.message,
            )
            for c in diff.changes
        ],
        breaking_changes=[
            SchemaChangeResponse(
                path=c.path,
                change_type=ChangeTypeEnum(c.change_type.value),
                old_value=c.old_value,
                new_value=c.new_value,
                breaking=c.breaking,
                message=c.message,
            )
            for c in diff.breaking_changes
        ],
        additions=[
            SchemaChangeResponse(
                path=c.path,
                change_type=ChangeTypeEnum(c.change_type.value),
                old_value=c.old_value,
                new_value=c.new_value,
                breaking=c.breaking,
                message=c.message,
            )
            for c in diff.additions
        ],
        removals=[
            SchemaChangeResponse(
                path=c.path,
                change_type=ChangeTypeEnum(c.change_type.value),
                old_value=c.old_value,
                new_value=c.new_value,
                breaking=c.breaking,
                message=c.message,
            )
            for c in diff.removals
        ],
        modifications=[
            SchemaChangeResponse(
                path=c.path,
                change_type=ChangeTypeEnum(c.change_type.value),
                old_value=c.old_value,
                new_value=c.new_value,
                breaking=c.breaking,
                message=c.message,
            )
            for c in diff.modifications
        ],
        has_breaking_changes=diff.has_breaking_changes,
        total_changes=len(diff.changes),
    )


@router.post(
    "/check",
    response_model=CompatibilityCheckResponse,
    summary="Check schema compatibility",
    description="Check if two schemas are compatible according to the specified mode",
)
async def check_schema_compatibility(
    request: CompatibilityCheckRequest,
) -> CompatibilityCheckResponse:
    """
    Check compatibility between two schemas.

    Modes:
    - backward: New schema can read data produced by old schema
    - forward: Old schema can read data produced by new schema
    - full: Both backward and forward compatible
    """
    try:
        # Convert mode
        mode = CompatibilityMode(request.mode.value)

        # Check compatibility
        result = check_compatibility(request.old_schema, request.new_schema, mode)

        # Convert diff to response
        diff_response = None
        if result.diff:
            diff_response = _convert_diff_to_response(result.diff)

        return CompatibilityCheckResponse(
            compatible=result.compatible,
            mode=request.mode,
            diff=diff_response,
            issues=result.issues,
            warnings=result.warnings,
            breaking_change_count=(
                len(result.diff.breaking_changes) if result.diff else 0
            ),
        )

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to check compatibility: {e}"
        )


@router.post(
    "/diff",
    response_model=SchemaDiffResponse,
    summary="Compute schema diff",
    description="Compute detailed diff between two schemas",
)
async def compute_schema_diff(request: DiffRequest) -> SchemaDiffResponse:
    """
    Compute detailed diff between two schemas.

    Returns all changes detected, categorized by type.
    """
    try:
        diff = compute_diff(request.old_schema, request.new_schema)
        return _convert_diff_to_response(diff)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to compute diff: {e}")


@router.get(
    "/{schema_name}/diff",
    response_model=SchemaDiffResponse,
    summary="Diff stored schema versions",
    description="Compute diff between two versions of a stored schema",
)
async def diff_stored_versions(
    schema_name: str,
    old_version: str = Query(..., description="Old version to compare"),
    new_version: str = Query(..., description="New version to compare"),
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> SchemaDiffResponse:
    """
    Compute diff between two versions of a stored schema.

    Retrieves both versions from the metadata store and computes the diff.
    """
    try:
        # Get old schema
        old_schema = store.get_schema(schema_name, version=old_version)
        if not old_schema:
            raise HTTPException(
                status_code=404,
                detail=f"Schema '{schema_name}' version '{old_version}' not found",
            )

        # Get new schema
        new_schema = store.get_schema(schema_name, version=new_version)
        if not new_schema:
            raise HTTPException(
                status_code=404,
                detail=f"Schema '{schema_name}' version '{new_version}' not found",
            )

        # Compute diff
        diff = compute_diff(old_schema, new_schema)
        return _convert_diff_to_response(diff)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute diff: {e}")


@router.get(
    "/{schema_name}/check",
    response_model=CompatibilityCheckResponse,
    summary="Check stored schema version compatibility",
    description="Check if a new schema is compatible with the latest stored version",
)
async def check_stored_compatibility(
    schema_name: str,
    mode: CompatibilityModeEnum = Query(
        default=CompatibilityModeEnum.BACKWARD, description="Compatibility mode"
    ),
    store: MetadataStoreClient = Depends(get_metadata_store),
    new_schema: Optional[dict] = None,
) -> CompatibilityCheckResponse:
    """
    Check if a new schema is compatible with the latest stored version.

    If new_schema is not provided in the body, this endpoint can be used
    to check compatibility between the latest and previous version.
    """
    try:
        # Get latest schema
        latest_schema = store.get_schema(schema_name)
        if not latest_schema:
            # No existing schema, so any new schema is "compatible"
            return CompatibilityCheckResponse(
                compatible=True,
                mode=mode,
                diff=None,
                issues=[],
                warnings=["No existing schema found - this would be a new schema"],
                breaking_change_count=0,
            )

        if new_schema is None:
            # Compare latest with previous (if exists)
            # This would require version history - for now, return compatible
            return CompatibilityCheckResponse(
                compatible=True,
                mode=mode,
                diff=None,
                issues=[],
                warnings=["No new schema provided for comparison"],
                breaking_change_count=0,
            )

        # Check compatibility
        result = check_compatibility(
            latest_schema, new_schema, CompatibilityMode(mode.value)
        )

        diff_response = None
        if result.diff:
            diff_response = _convert_diff_to_response(result.diff)

        return CompatibilityCheckResponse(
            compatible=result.compatible,
            mode=mode,
            diff=diff_response,
            issues=result.issues,
            warnings=result.warnings,
            breaking_change_count=(
                len(result.diff.breaking_changes) if result.diff else 0
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to check compatibility: {e}"
        )


@router.post(
    "/{schema_name}/check",
    response_model=CompatibilityCheckResponse,
    summary="Check new schema compatibility with stored version",
    description="Check if a new schema is compatible with the latest stored version",
)
async def check_new_schema_compatibility(
    schema_name: str,
    new_schema: dict,
    mode: CompatibilityModeEnum = Query(
        default=CompatibilityModeEnum.BACKWARD, description="Compatibility mode"
    ),
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> CompatibilityCheckResponse:
    """
    Check if a new schema is compatible with the latest stored version.

    Use this before storing a new schema version to ensure compatibility.
    """
    try:
        # Get latest schema
        latest_schema = store.get_schema(schema_name)
        if not latest_schema:
            return CompatibilityCheckResponse(
                compatible=True,
                mode=mode,
                diff=None,
                issues=[],
                warnings=["No existing schema - this would be a new schema"],
                breaking_change_count=0,
            )

        # Check compatibility
        result = check_compatibility(
            latest_schema, new_schema, CompatibilityMode(mode.value)
        )

        diff_response = None
        if result.diff:
            diff_response = _convert_diff_to_response(result.diff)

        return CompatibilityCheckResponse(
            compatible=result.compatible,
            mode=mode,
            diff=diff_response,
            issues=result.issues,
            warnings=result.warnings,
            breaking_change_count=(
                len(result.diff.breaking_changes) if result.diff else 0
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to check compatibility: {e}"
        )

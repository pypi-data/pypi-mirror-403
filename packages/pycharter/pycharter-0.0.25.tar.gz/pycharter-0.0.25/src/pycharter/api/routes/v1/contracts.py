"""
Route handlers for contract parsing and building.
"""

import logging
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from pycharter import build_contract, build_contract_from_store, parse_contract, parse_contract_file
from pycharter.contract_builder.builder import ContractArtifacts
from pycharter.db.models import DataContractModel
from pycharter.metadata_store import MetadataStoreClient

from pycharter.api.dependencies.database import get_db_session
from pycharter.api.dependencies.store import get_metadata_store
from pycharter.api.models.contracts import (
    ContractBuildRequest,
    ContractBuildResponse,
    ContractCreateFromArtifactsRequest,
    ContractCreateMixedRequest,
    ContractListResponse,
    ContractListItem,
    ContractParseRequest,
    ContractParseResponse,
    ContractUpdateRequest,
)
from pycharter.api.utils import ensure_uuid, get_by_id_or_404, safe_uuid_to_str

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/contracts/parse",
    response_model=ContractParseResponse,
    status_code=status.HTTP_200_OK,
    summary="Parse a data contract",
    description="Parse a data contract dictionary into its component parts (schema, metadata, ownership, governance rules, etc.)",
    response_description="Parsed contract components",
)
async def parse_contract_endpoint(
    request: ContractParseRequest,
) -> ContractParseResponse:
    """
    Parse a data contract into its components.
    
    This endpoint takes a complete data contract dictionary and breaks it down
    into its constituent parts: schema, metadata, ownership, governance rules,
    coercion rules, and validation rules.
    
    Args:
        request: Contract parse request containing contract data
        
    Returns:
        Parsed contract components
        
    Raises:
        HTTPException: If contract parsing fails
    """
    # Handle potential double-wrapping
    contract_data = request.contract
    if isinstance(contract_data, dict) and "contract" in contract_data and len(contract_data) == 1:
        contract_data = contract_data["contract"]
    
    if not isinstance(contract_data, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid contract format: expected dict, got {type(contract_data)}",
        )
    
    if "schema" not in contract_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contract must contain a 'schema' field at the top level",
        )
    
    try:
        contract_metadata = parse_contract(contract_data)
        return ContractParseResponse(
            schema=contract_metadata.schema,
            metadata=contract_metadata.metadata,
            ownership=contract_metadata.ownership,
            governance_rules=contract_metadata.governance_rules,
            coercion_rules=contract_metadata.coercion_rules,
            validation_rules=contract_metadata.validation_rules,
            versions=contract_metadata.versions,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/contracts/parse/upload",
    response_model=ContractParseResponse,
    status_code=status.HTTP_200_OK,
    summary="Parse a data contract from file upload",
    description="Parse a data contract file (YAML or JSON) uploaded via multipart/form-data into its component parts (schema, metadata, ownership, governance rules, etc.)",
    response_description="Parsed contract components",
)
async def parse_contract_file_endpoint(
    file: UploadFile = File(..., description="Contract file (YAML or JSON)"),
    should_validate: bool = Form(True, alias="validate", description="Validate contract against schema before parsing"),
) -> ContractParseResponse:
    """
    Parse a data contract from an uploaded file.
    
    This endpoint accepts a contract file (YAML or JSON) and breaks it down
    into its constituent parts: schema, metadata, ownership, governance rules,
    coercion rules, and validation rules.
    
    Args:
        file: Uploaded contract file (YAML or JSON)
        validate: Whether to validate contract against schema before parsing
        
    Returns:
        Parsed contract components
        
    Raises:
        HTTPException: If contract parsing fails or file format is unsupported
    """
    # Validate file format
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ['.yaml', '.yml', '.json']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format: {file_extension}. Only YAML (.yaml, .yml) and JSON (.json) files are supported.",
        )
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
        # Read file content
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        # Parse contract file
        contract_metadata = parse_contract_file(tmp_file_path, validate=should_validate)
        
        return ContractParseResponse(
            schema=contract_metadata.schema,
            metadata=contract_metadata.metadata,
            ownership=contract_metadata.ownership,
            governance_rules=contract_metadata.governance_rules,
            coercion_rules=contract_metadata.coercion_rules,
            validation_rules=contract_metadata.validation_rules,
            versions=contract_metadata.versions,
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error parsing contract file: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse contract file: {str(e)}",
        )
    finally:
        # Clean up temporary file
        try:
            Path(tmp_file_path).unlink()
        except Exception:
            pass


@router.post(
    "/contracts/{contract_id}/build",
    response_model=ContractBuildResponse,
    status_code=status.HTTP_200_OK,
    summary="Build a contract from contract ID",
    description="Reconstruct a complete data contract from a contract ID by fetching its linked artifacts",
    response_description="Complete contract dictionary",
)
async def build_contract_from_id_endpoint(
    contract_id: str,
    include_metadata: bool = Query(True, description="Include metadata in contract"),
    include_ownership: bool = Query(True, description="Include ownership in contract"),
    include_governance: bool = Query(True, description="Include governance rules in contract"),
    store: MetadataStoreClient = Depends(get_metadata_store),
    db: Session = Depends(get_db_session),
) -> ContractBuildResponse:
    """
    Build a contract from contract ID.
    
    This endpoint retrieves a contract by ID and reconstructs the complete
    data contract dictionary from its linked artifacts (schema, coercion rules,
    validation rules, metadata). You can optionally include metadata, ownership,
    and governance rules.
    
    Args:
        contract_id: Contract ID (UUID)
        include_metadata: Whether to include metadata in contract
        include_ownership: Whether to include ownership in contract
        include_governance: Whether to include governance rules in contract
        store: Metadata store dependency
        db: Database session dependency
        
    Returns:
        Complete contract dictionary
        
    Raises:
        HTTPException: If contract not found or building fails
    """
    from pycharter.db.models import (
        CoercionRuleModel,
        MetadataRecordModel,
        SchemaModel,
        ValidationRuleModel,
    )
    
    # Parse and validate contract ID
    try:
        ensure_uuid(contract_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid contract ID format: {contract_id}",
        )
    
    # Get contract from database
    contract = get_by_id_or_404(
        db, DataContractModel, contract_id, 
        error_message=f"Contract not found: {contract_id}",
        model_name="Contract"
    )
    
    # Get schema - required
    if not contract.schema_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Contract '{contract.name}' (ID: {contract_id}) does not have a linked schema. "
                f"Cannot build contract without a schema. "
                f"Please link a schema to this contract or create a new contract with a schema."
            ),
        )
    
    # Get schema - required
    schema = get_by_id_or_404(
        db, SchemaModel, contract.schema_id,
        error_message=f"Schema with ID {safe_uuid_to_str(contract.schema_id)} not found",
        model_name="Schema"
    )
    
    # Get schema data and ensure it has a version
    schema_data = dict(schema.schema_data) if schema.schema_data else {}
    if "version" not in schema_data:
        schema_data["version"] = schema.version
    
    # Get coercion rules (optional)
    coercion_rules_data = None
    if contract.coercion_rules_id:
        coercion_rules = get_by_id_or_404(
            db, CoercionRuleModel, contract.coercion_rules_id,
            model_name="CoercionRule"
        )
        if coercion_rules and coercion_rules.rules:
            # Format coercion rules - the rules dict itself, with version if needed
            # The builder will extract the "rules" key if present, otherwise uses the whole dict
            coercion_rules_data = dict(coercion_rules.rules) if coercion_rules.rules else {}
            coercion_rules_data["version"] = coercion_rules.version
    
    # Get validation rules (optional)
    validation_rules_data = None
    if contract.validation_rules_id:
        validation_rules = get_by_id_or_404(
            db, ValidationRuleModel, contract.validation_rules_id,
            model_name="ValidationRule"
        )
        if validation_rules and validation_rules.rules:
            # Format validation rules - the rules dict itself, with version if needed
            # The builder will extract the "rules" key if present, otherwise uses the whole dict
            validation_rules_data = dict(validation_rules.rules) if validation_rules.rules else {}
            validation_rules_data["version"] = validation_rules.version
    
    # Get metadata (optional)
    metadata_data = None
    ownership_data = None
    governance_rules_data = None
    if contract.metadata_record_id:
        metadata_record = get_by_id_or_404(
            db, MetadataRecordModel, contract.metadata_record_id,
            model_name="MetadataRecord"
        )
        if metadata_record:
            # Build metadata dict from metadata record
            metadata_data = {
                "version": metadata_record.version,
            }
            
            # Add description if available
            if metadata_record.description:
                metadata_data["description"] = metadata_record.description
            
            # Add status if available
            if metadata_record.status:
                metadata_data["status"] = metadata_record.status
            
            # Extract ownership from relationships if include_ownership is True
            if include_ownership:
                ownership_data = {}
                try:
                    # Get business owners
                    if hasattr(metadata_record, 'business_owners_rel') and metadata_record.business_owners_rel:
                        business_owners = []
                        for owner_rel in metadata_record.business_owners_rel:
                            if hasattr(owner_rel, 'owner') and owner_rel.owner:
                                business_owners.append({
                                    "name": getattr(owner_rel.owner, 'name', ''),
                                    "email": getattr(owner_rel.owner, 'email', ''),
                                })
                        if business_owners:
                            ownership_data["business_owners"] = business_owners
                except Exception:
                    # If ownership extraction fails, just continue without it
                    pass
            
            # Get governance rules if include_governance is True
            if include_governance and metadata_record.governance_rules:
                governance_rules_data = metadata_record.governance_rules
    
    # Build contract directly from database artifacts
    artifacts = ContractArtifacts(
        schema=schema_data,
        coercion_rules=coercion_rules_data,
        validation_rules=validation_rules_data,
        metadata=metadata_data if include_metadata else None,
        ownership=ownership_data,
        governance_rules=governance_rules_data,
    )
    
    try:
        built_contract = build_contract(
            artifacts,
            include_metadata=include_metadata,
            include_ownership=include_ownership,
            include_governance=include_governance,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to build contract: {str(e)}",
        )
    
    return ContractBuildResponse(contract=built_contract)


@router.post(
    "/contracts/build",
    response_model=ContractBuildResponse,
    status_code=status.HTTP_200_OK,
    summary="Build a contract from metadata store",
    description="Reconstruct a complete data contract from components stored in the metadata store",
    response_description="Complete contract dictionary",
)
async def build_contract_endpoint(
    request: ContractBuildRequest,
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> ContractBuildResponse:
    """
    Build a contract from metadata store.
    
    This endpoint reconstructs a complete data contract dictionary from
    components stored in the metadata store. You can optionally include
    metadata, ownership, and governance rules.
    
    Args:
        request: Contract build request with schema_id and options
        store: Metadata store dependency
        
    Returns:
        Complete contract dictionary
        
    Raises:
        HTTPException: If contract building fails or schema not found
    """
    contract = build_contract_from_store(
        store=store,
        schema_title=request.schema_title,
        schema_version=request.schema_version,
        coercion_rules_title=request.coercion_rules_title,
        coercion_rules_version=request.coercion_rules_version,
        validation_rules_title=request.validation_rules_title,
        validation_rules_version=request.validation_rules_version,
        metadata_title=request.metadata_title,
        metadata_version=request.metadata_version,
        include_metadata=request.include_metadata,
        include_ownership=request.include_ownership,
        include_governance=request.include_governance,
    )
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema not found: {request.schema_title}",
        )
    
    return ContractBuildResponse(contract=contract)


@router.post(
    "/contracts/create-from-artifacts",
    response_model=ContractListItem,
    status_code=status.HTTP_201_CREATED,
    summary="Create a data contract from existing artifacts",
    description="Create a new data contract by linking to existing artifacts (schemas, coercion rules, validation rules, metadata) identified by title and version",
    response_description="Created contract information",
)
async def create_contract_from_artifacts(
    request: ContractCreateFromArtifactsRequest,
    db: Session = Depends(get_db_session),
) -> ContractListItem:
    """
    Create a new data contract from existing artifacts.
    
    This endpoint creates a new data contract by linking to existing artifacts
    (schemas, coercion rules, validation rules, metadata) that are identified
    by their title and version. This allows reusing artifacts across multiple contracts.
    
    Args:
        request: Contract creation request with contract name/version and artifact titles/versions
        db: Database session dependency
        
    Returns:
        Created contract information
        
    Raises:
        HTTPException: If contract creation fails or artifacts not found
    """
    from pycharter.db.models import (
        CoercionRuleModel,
        MetadataRecordModel,
        SchemaModel,
        ValidationRuleModel,
    )
    
    # Check if contract with same name and version already exists
    existing = db.query(DataContractModel).filter(
        DataContractModel.name == request.name,
        DataContractModel.version == request.version,
    ).first()
    
    if existing:
        # Log diagnostic information
        total_contracts = db.query(DataContractModel).count()
        logger.warning(
            f"Contract '{request.name}' v'{request.version}' already exists. "
            f"Total contracts in DB: {total_contracts}. "
            f"Existing contract ID: {safe_uuid_to_str(existing.id)}"
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Contract '{request.name}' with version '{request.version}' already exists (ID: {safe_uuid_to_str(existing.id)})",
        )
    
    # Find schema by title and version
    schema = db.query(SchemaModel).filter(
        SchemaModel.title == request.schema_title,
        SchemaModel.version == request.schema_version,
    ).first()
    
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema not found: title='{request.schema_title}', version='{request.schema_version}'",
        )
    
    # Find coercion rules by title and version (if provided)
    coercion_rules_id = None
    if request.coercion_rules_title and request.coercion_rules_version:
        coercion_rules = db.query(CoercionRuleModel).filter(
            CoercionRuleModel.title == request.coercion_rules_title,
            CoercionRuleModel.version == request.coercion_rules_version,
        ).first()
        
        if not coercion_rules:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Coercion rules not found: title='{request.coercion_rules_title}', version='{request.coercion_rules_version}'",
            )
        coercion_rules_id = ensure_uuid(coercion_rules.id)
    
    # Find validation rules by title and version (if provided)
    validation_rules_id = None
    if request.validation_rules_title and request.validation_rules_version:
        validation_rules = db.query(ValidationRuleModel).filter(
            ValidationRuleModel.title == request.validation_rules_title,
            ValidationRuleModel.version == request.validation_rules_version,
        ).first()
        
        if not validation_rules:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Validation rules not found: title='{request.validation_rules_title}', version='{request.validation_rules_version}'",
            )
        validation_rules_id = ensure_uuid(validation_rules.id)
    
    # Find metadata by title and version (if provided)
    metadata_record_id = None
    if request.metadata_title and request.metadata_version:
        metadata_record = db.query(MetadataRecordModel).filter(
            MetadataRecordModel.title == request.metadata_title,
            MetadataRecordModel.version == request.metadata_version,
        ).first()
        
        if not metadata_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Metadata not found: title='{request.metadata_title}', version='{request.metadata_version}'",
            )
        metadata_record_id = ensure_uuid(metadata_record.id)
    
    # Create new data contract
    new_contract = DataContractModel(
        name=request.name,
        version=request.version,
        status=request.status or "active",
        description=request.description,
        schema_id=ensure_uuid(schema.id),
        coercion_rules_id=coercion_rules_id,
        validation_rules_id=validation_rules_id,
        metadata_record_id=metadata_record_id,
    )
    
    try:
        db.add(new_contract)
        db.commit()
        db.refresh(new_contract)
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating contract from artifacts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create contract: {str(e)}",
        )
    
    return ContractListItem(
        id=safe_uuid_to_str(new_contract.id),
        name=new_contract.name,
        version=new_contract.version,
        status=new_contract.status,
        description=new_contract.description,
        schema_id=safe_uuid_to_str(new_contract.schema_id),
        created_at=new_contract.created_at.isoformat() if new_contract.created_at else None,
        updated_at=new_contract.updated_at.isoformat() if new_contract.updated_at else None,
    )


@router.post(
    "/contracts/create-mixed",
    response_model=ContractListItem,
    status_code=status.HTTP_201_CREATED,
    summary="Create a data contract with mixed artifacts",
    description="Create a new data contract by mixing new artifacts (provided as data) and existing artifacts (identified by title and version). Each artifact type can be either new or existing independently.",
    response_description="Created contract information",
)
async def create_contract_mixed(
    request: ContractCreateMixedRequest,
    store: MetadataStoreClient = Depends(get_metadata_store),
    db: Session = Depends(get_db_session),
) -> ContractListItem:
    """
    Create a new data contract with mixed artifacts (some new, some existing).
    
    This endpoint allows creating a contract where:
    - Schema can be new (provided as data) or existing (by title+version)
    - Coercion rules can be new or existing (optional)
    - Validation rules can be new or existing (optional)
    - Metadata can be new or existing (optional)
    
    Each artifact type is independent - you can mix and match as needed.
    
    Args:
        request: Contract creation request with mixed artifacts
        store: Metadata store dependency
        db: Database session dependency
        
    Returns:
        Created contract information
        
    Raises:
        HTTPException: If contract creation fails or artifacts not found
    """
    from pycharter.db.models import (
        CoercionRuleModel,
        MetadataRecordModel,
        SchemaModel,
        ValidationRuleModel,
    )
    
    # Handle schema: create new or find existing
    # Note: store.store_schema() may create a data contract, so we check after schema creation
    schema_id = None
    existing_contract_from_store = None
    
    if request.schema is not None:
        # Create new schema artifact
        # Note: store.store_schema() creates both a data contract and schema via raw SQL
        try:
            schema_id_str = store.store_schema(
                schema_name=request.name,
                schema=request.schema,
                version=request.version,
            )
            schema_id = ensure_uuid(schema_id_str)
        except ValueError as e:
            error_msg = str(e)
            # Enhance error message for schema conflicts
            if "already exists" in error_msg.lower():
                schema_title = request.schema.get("title") or request.name
                schema_version = request.schema.get("version") or request.version
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Schema artifact '{schema_title}' v'{schema_version}' already exists. "
                           f"To use this existing schema, select 'Use Existing' mode and pick it by title and version. "
                           f"To create a new schema artifact, use a different version number in your schema JSON.",
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Schema creation failed: {error_msg}",
            )
    elif request.schema_title and request.schema_version:
        # Find existing schema
        # Check if contract with same name and version already exists (only if using existing schema)
        existing = db.query(DataContractModel).filter(
            DataContractModel.name == request.name,
            DataContractModel.version == request.version,
        ).first()
        
        if existing:
            # Log diagnostic information
            total_contracts = db.query(DataContractModel).count()
            logger.warning(
                f"Contract '{request.name}' v'{request.version}' already exists. "
                f"Total contracts in DB: {total_contracts}. "
                f"Existing contract ID: {safe_uuid_to_str(existing.id)}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Contract '{request.name}' with version '{request.version}' already exists (ID: {safe_uuid_to_str(existing.id)})",
            )
        
        schema = db.query(SchemaModel).filter(
            SchemaModel.title == request.schema_title,
            SchemaModel.version == request.schema_version,
        ).first()
        
        if not schema:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schema not found: title='{request.schema_title}', version='{request.schema_version}'",
            )
        schema_id = ensure_uuid(schema.id)
    
    # Handle coercion rules: create new or find existing
    coercion_rules_id = None
    if request.coercion_rules is not None and len(request.coercion_rules) > 0:
        # Create new coercion rules artifact
        try:
            coercion_rules_id_str = store.store_coercion_rules(
                schema_id=str(schema_id) if schema_id else None,
                coercion_rules=request.coercion_rules,
                version=request.version,
            )
            coercion_rules_id = ensure_uuid(coercion_rules_id_str) if coercion_rules_id_str else None
        except ValueError as e:
            error_msg = str(e)
            if "already exists" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Coercion rules artifact already exists with this version. "
                           f"To use existing coercion rules, select 'Use Existing' mode. "
                           f"To create new coercion rules, the artifact version must be unique.",
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Coercion rules creation failed: {error_msg}",
            )
    elif request.coercion_rules_title and request.coercion_rules_version:
        # Find existing coercion rules
        coercion_rules = db.query(CoercionRuleModel).filter(
            CoercionRuleModel.title == request.coercion_rules_title,
            CoercionRuleModel.version == request.coercion_rules_version,
        ).first()
        
        if not coercion_rules:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Coercion rules not found: title='{request.coercion_rules_title}', version='{request.coercion_rules_version}'",
            )
        coercion_rules_id = ensure_uuid(coercion_rules.id)
    
    # Handle validation rules: create new or find existing
    validation_rules_id = None
    if request.validation_rules is not None and len(request.validation_rules) > 0:
        # Create new validation rules artifact
        try:
            validation_rules_id_str = store.store_validation_rules(
                schema_id=str(schema_id) if schema_id else None,
                validation_rules=request.validation_rules,
                version=request.version,
            )
            validation_rules_id = ensure_uuid(validation_rules_id_str) if validation_rules_id_str else None
        except ValueError as e:
            error_msg = str(e)
            if "already exists" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Validation rules artifact already exists with this version. "
                           f"To use existing validation rules, select 'Use Existing' mode. "
                           f"To create new validation rules, the artifact version must be unique.",
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation rules creation failed: {error_msg}",
            )
    elif request.validation_rules_title and request.validation_rules_version:
        # Find existing validation rules
        validation_rules = db.query(ValidationRuleModel).filter(
            ValidationRuleModel.title == request.validation_rules_title,
            ValidationRuleModel.version == request.validation_rules_version,
        ).first()
        
        if not validation_rules:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Validation rules not found: title='{request.validation_rules_title}', version='{request.validation_rules_version}'",
            )
        validation_rules_id = ensure_uuid(validation_rules.id)
    
    # Handle metadata: create new or find existing
    metadata_record_id = None
    if request.metadata is not None and len(request.metadata) > 0:
        # Create new metadata artifact
        try:
            metadata_record_id_str = store.store_metadata(
                schema_id=str(schema_id) if schema_id else None,
                metadata=request.metadata,
                version=request.version,
            )
            metadata_record_id = ensure_uuid(metadata_record_id_str) if metadata_record_id_str else None
        except ValueError as e:
            error_msg = str(e)
            if "already exists" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Metadata artifact already exists with this version. "
                           f"To use existing metadata, select 'Use Existing' mode. "
                           f"To create new metadata, the artifact version must be unique.",
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Metadata creation failed: {error_msg}",
            )
    elif request.metadata_title and request.metadata_version:
        # Find existing metadata
        metadata_record = db.query(MetadataRecordModel).filter(
            MetadataRecordModel.title == request.metadata_title,
            MetadataRecordModel.version == request.metadata_version,
        ).first()
        
        if not metadata_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Metadata not found: title='{request.metadata_title}', version='{request.metadata_version}'",
            )
        metadata_record_id = ensure_uuid(metadata_record.id)
    
    # The store methods (store_schema, store_coercion_rules, store_validation_rules, store_metadata)
    # already create and link artifacts to the data contract via raw SQL.
    # We need to fetch the final contract state from the database.
    
    # Expire all cached objects to ensure we get fresh data from the database
    db.expire_all()
    
    # Query for the contract that was created/updated by the store methods
    new_contract = db.query(DataContractModel).filter(
        DataContractModel.name == request.name,
        DataContractModel.version == request.version,
    ).first()
    
    if new_contract:
        # Contract was created by store methods - just update status/description if needed
        needs_update = False
        if request.status and new_contract.status != request.status:
            new_contract.status = request.status
            needs_update = True
        if request.description is not None and new_contract.description != request.description:
            new_contract.description = request.description
            needs_update = True
        
        if needs_update:
            try:
                db.commit()
                db.refresh(new_contract)
            except Exception as e:
                db.rollback()
                logger.error(f"Error updating contract status/description: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to update contract: {str(e)}",
                )
    else:
        # Fallback: create new data contract if store methods didn't create one
        # This happens when using existing artifacts (not creating new ones via store methods)
        logger.info(f"Contract not found after store operations, creating new one: {request.name} v{request.version}")
        
        # CRITICAL: Ensure all IDs are proper UUID objects RIGHT BEFORE creating the model
        # This must happen here, not earlier, to avoid any string conversion issues
        # Double-check and convert each ID to ensure they're UUID objects, not strings
        final_schema_id = ensure_uuid(schema_id) if schema_id else None
        final_coercion_rules_id = ensure_uuid(coercion_rules_id) if coercion_rules_id else None
        final_validation_rules_id = ensure_uuid(validation_rules_id) if validation_rules_id else None
        final_metadata_record_id = ensure_uuid(metadata_record_id) if metadata_record_id else None
        
        # Final validation: ensure all non-None IDs are actually UUID objects
        # This catches any edge cases where conversion might have failed
        for id_name, id_value in [
            ("schema_id", final_schema_id),
            ("coercion_rules_id", final_coercion_rules_id),
            ("validation_rules_id", final_validation_rules_id),
            ("metadata_record_id", final_metadata_record_id),
        ]:
            if id_value is not None and not isinstance(id_value, uuid.UUID):
                raise ValueError(
                    f"Invalid {id_name} type: {type(id_value)} (value: {id_value}). "
                    f"Expected uuid.UUID or None. This indicates a bug in UUID conversion."
                )
        
        # CRITICAL: Verify that all referenced artifacts actually exist in the database
        # This prevents foreign key constraint errors
        if final_schema_id:
            schema_exists = db.query(SchemaModel).filter(SchemaModel.id == final_schema_id).first()
            if not schema_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Schema with ID '{final_schema_id}' not found in database. "
                           f"This may indicate the artifact was created in a different database or was deleted.",
                )
        
        if final_coercion_rules_id:
            coercion_rules_exists = db.query(CoercionRuleModel).filter(
                CoercionRuleModel.id == final_coercion_rules_id
            ).first()
            if not coercion_rules_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Coercion rules with ID '{final_coercion_rules_id}' not found in database. "
                           f"This may indicate the artifact was created in a different database or was deleted.",
                )
        
        if final_validation_rules_id:
            validation_rules_exists = db.query(ValidationRuleModel).filter(
                ValidationRuleModel.id == final_validation_rules_id
            ).first()
            if not validation_rules_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Validation rules with ID '{final_validation_rules_id}' not found in database. "
                           f"This may indicate the artifact was created in a different database or was deleted.",
                )
        
        if final_metadata_record_id:
            metadata_exists = db.query(MetadataRecordModel).filter(
                MetadataRecordModel.id == final_metadata_record_id
            ).first()
            if not metadata_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Metadata record with ID '{final_metadata_record_id}' not found in database. "
                           f"This may indicate the artifact was created in a different database or was deleted.",
                )
        
        # Log types for debugging
        logger.debug(f"Creating contract with IDs - schema_id type: {type(final_schema_id)}, "
                    f"coercion_rules_id type: {type(final_coercion_rules_id)}, "
                    f"validation_rules_id type: {type(final_validation_rules_id)}, "
                    f"metadata_record_id type: {type(final_metadata_record_id)}")
        
        new_contract = DataContractModel(
            name=request.name,
            version=request.version,
            status=request.status or "active",
            description=request.description,
            schema_id=final_schema_id,
            coercion_rules_id=final_coercion_rules_id,
            validation_rules_id=final_validation_rules_id,
            metadata_record_id=final_metadata_record_id,
        )
        
        try:
            db.add(new_contract)
            db.commit()
            db.refresh(new_contract)
        except Exception as e:
            db.rollback()
            error_msg = str(e)
            logger.error(f"Error creating contract with mixed artifacts: {e}", exc_info=True)
            
            # Provide more helpful error messages for foreign key constraint failures
            if "FOREIGN KEY constraint failed" in error_msg or "foreign key constraint" in error_msg.lower():
                # Log which IDs we're trying to use for debugging
                logger.error(
                    f"Foreign key constraint failed. IDs being used:\n"
                    f"  schema_id: {final_schema_id}\n"
                    f"  coercion_rules_id: {final_coercion_rules_id}\n"
                    f"  validation_rules_id: {final_validation_rules_id}\n"
                    f"  metadata_record_id: {final_metadata_record_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to create contract: One or more referenced artifacts do not exist in the database. "
                           f"This usually means the artifacts were created in a different database or were deleted. "
                           f"Please verify that all artifacts (schema, coercion rules, validation rules, metadata) exist "
                           f"in the current database before creating the contract. Error: {error_msg}",
                )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create contract: {error_msg}",
            )
    
    return ContractListItem(
        id=safe_uuid_to_str(new_contract.id),
        name=new_contract.name,
        version=new_contract.version,
        status=new_contract.status,
        description=new_contract.description,
        schema_id=safe_uuid_to_str(new_contract.schema_id),
        created_at=new_contract.created_at.isoformat() if new_contract.created_at else None,
        updated_at=new_contract.updated_at.isoformat() if new_contract.updated_at else None,
    )


@router.get(
    "/contracts",
    response_model=ContractListResponse,
    status_code=status.HTTP_200_OK,
    summary="List data contracts",
    description="Get a list of all data contracts stored in the database",
    response_description="List of contracts",
)
async def list_contracts(
    db: Session = Depends(get_db_session),
) -> ContractListResponse:
    """
    List all data contracts from the database.
    
    Args:
        db: Database session dependency
        
    Returns:
        List of contracts with metadata
        
    Raises:
        HTTPException: If database query fails
    """
    try:
        # Query all contracts
        contracts = db.query(DataContractModel).order_by(
            DataContractModel.created_at.desc()
        ).all()
        
        # Log for debugging
        logger.debug(f"Found {len(contracts)} contracts in database")
        
        contract_items = [
            ContractListItem(
                id=safe_uuid_to_str(contract.id),
                name=contract.name,
                version=contract.version,
                status=contract.status,
                description=contract.description,
                schema_id=safe_uuid_to_str(contract.schema_id),
                created_at=contract.created_at.isoformat() if contract.created_at else None,
                updated_at=contract.updated_at.isoformat() if contract.updated_at else None,
            )
            for contract in contracts
        ]
        
        return ContractListResponse(
            contracts=contract_items,
            total=len(contract_items),
        )
    except Exception as e:
        logger.error(f"Error listing contracts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list contracts: {str(e)}",
        )


@router.get(
    "/contracts/{contract_id}",
    response_model=ContractListItem,
    status_code=status.HTTP_200_OK,
    summary="Get data contract by ID",
    description="Retrieve a specific data contract from the database by its ID",
    response_description="Contract details",
)
async def get_contract(
    contract_id: str,
    db: Session = Depends(get_db_session),
) -> ContractListItem:
    """
    Get a specific data contract from the database by ID.
    
    Args:
        contract_id: Contract ID (UUID)
        db: Database session dependency
        
    Returns:
        Contract details
        
    Raises:
        HTTPException: If contract not found or database query fails
    """
    # Validate contract ID format
    try:
        ensure_uuid(contract_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid contract ID format: {contract_id}",
        )
    
    # Get contract from database
    contract = get_by_id_or_404(
        db, DataContractModel, contract_id,
        error_message=f"Contract not found: {contract_id}",
        model_name="Contract"
    )
    
    return ContractListItem(
        id=safe_uuid_to_str(contract.id),
        name=contract.name,
        version=contract.version,
        status=contract.status,
        description=contract.description,
        schema_id=safe_uuid_to_str(contract.schema_id),
        created_at=contract.created_at.isoformat() if contract.created_at else None,
        updated_at=contract.updated_at.isoformat() if contract.updated_at else None,
    )


@router.put(
    "/contracts/{contract_id}",
    response_model=ContractListItem,
    status_code=status.HTTP_200_OK,
    summary="Update data contract",
    description="Update contract metadata (name, version, status, description)",
    response_description="Updated contract details",
)
async def update_contract(
    contract_id: str,
    request: ContractUpdateRequest,
    db: Session = Depends(get_db_session),
) -> ContractListItem:
    """
    Update a data contract's metadata.
    
    This endpoint allows updating the contract's name, version, status, and description.
    Note: To update the schema, coercion rules, or validation rules, you need to
    upload a new version of the contract.
    
    Args:
        contract_id: Contract ID (UUID)
        request: Contract update request with fields to update
        db: Database session dependency
        
    Returns:
        Updated contract details
        
    Raises:
        HTTPException: If contract not found, invalid update, or database query fails
    """
    # Validate contract ID format
    try:
        ensure_uuid(contract_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid contract ID format: {contract_id}",
        )
    
    # Get contract from database
    contract = get_by_id_or_404(
        db, DataContractModel, contract_id,
        error_message=f"Contract not found: {contract_id}",
        model_name="Contract"
    )
    
    # Check if any fields are being updated
    if not any([request.name, request.version, request.status is not None, request.description is not None]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided for update",
        )
    
    # Check for unique constraint violation (name + version)
    if request.name or request.version:
        new_name = request.name if request.name else contract.name
        new_version = request.version if request.version else contract.version
        
        # Check if another contract with same name+version exists
        existing = db.query(DataContractModel).filter(
            DataContractModel.name == new_name,
            DataContractModel.version == new_version,
            DataContractModel.id != contract.id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contract with name '{new_name}' and version '{new_version}' already exists",
            )
    
    # Check if any fields are being updated
    if not any([request.name, request.version, request.status is not None, request.description is not None]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided for update",
        )
    
    try:
        # Use direct SQL UPDATE to avoid session/detachment issues with SQLite
        from sqlalchemy import text
        
        # Build UPDATE statement with only the fields that are being updated
        set_clauses = []
        params = {}
        
        if request.name is not None:
            set_clauses.append('name = :name')
            params['name'] = request.name
        if request.version is not None:
            set_clauses.append('version = :version')
            params['version'] = request.version
        if request.status is not None:
            set_clauses.append('status = :status')
            params['status'] = request.status
        if request.description is not None:
            set_clauses.append('description = :description')
            params['description'] = request.description
        
        # Always update updated_at timestamp
        set_clauses.append('updated_at = CURRENT_TIMESTAMP')
        
        set_clause = ', '.join(set_clauses)
        
        # Use contract_id string for WHERE clause (works with both PostgreSQL and SQLite)
        contract_id_str = safe_uuid_to_str(contract.id) or contract_id
        
        # Determine table name and SQL syntax based on database type
        from sqlalchemy import inspect
        engine = db.bind if hasattr(db, 'bind') else None
        is_sqlite = engine and 'sqlite' in str(engine.url)
        
        # Get contract ID as string for WHERE clause
        contract_id_str = safe_uuid_to_str(contract.id) or contract_id
        
        if is_sqlite:
            # SQLite doesn't support schemas, and stores UUIDs as TEXT
            table_name = "data_contracts"
            # For SQLite, compare as strings
            sql = f"""
                UPDATE {table_name}
                SET {set_clause}
                WHERE id = :contract_id
            """
            params['contract_id'] = contract_id_str
        else:
            # PostgreSQL and other databases
            table_name = "pycharter.data_contracts"
            # Try with UUID first
            sql = f"""
                UPDATE {table_name}
                SET {set_clause}
                WHERE id = :contract_id::uuid
            """
            params['contract_id'] = contract_id_str
        
        # Execute the update
        result = db.execute(text(sql), params)
        
        if result.rowcount == 0:
            # If no rows updated, try alternative approaches
            if is_sqlite:
                # SQLite: try with explicit string comparison
                sql_fallback = f"""
                    UPDATE {table_name}
                    SET {set_clause}
                    WHERE CAST(id AS TEXT) = :contract_id
                """
            else:
                # PostgreSQL: try with text comparison
                sql_fallback = f"""
                    UPDATE {table_name}
                    SET {set_clause}
                    WHERE id::text = :contract_id
                """
            
            params['contract_id'] = contract_id_str
            result = db.execute(text(sql_fallback), params)
            
            if result.rowcount == 0:
                # Last resort: try with the UUID object
                if not is_sqlite:
                    sql_uuid = f"""
                        UPDATE {table_name}
                        SET {set_clause}
                        WHERE id = :contract_id
                    """
                    params['contract_id'] = contract_uuid
                    result = db.execute(text(sql_uuid), params)
                
                if result.rowcount == 0:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Contract not found or could not be updated: {contract_id}",
                    )
        
        # Commit the changes
        db.commit()
        
        # Re-query the contract to get updated values (don't use refresh since we used raw SQL)
        # Expire the old object from the session first
        db.expire(contract)
        
        # Re-query the contract to get updated values
        contract = get_by_id_or_404(
            db, DataContractModel, contract_id,
            error_message=f"Contract not found after update: {contract_id}",
            model_name="Contract"
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating contract: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update contract: {str(e)}",
        )
    
    return ContractListItem(
        id=safe_uuid_to_str(contract.id),
        name=contract.name,
        version=contract.version,
        status=contract.status,
        description=contract.description,
        schema_id=safe_uuid_to_str(contract.schema_id),
        created_at=contract.created_at.isoformat() if contract.created_at else None,
        updated_at=contract.updated_at.isoformat() if contract.updated_at else None,
    )

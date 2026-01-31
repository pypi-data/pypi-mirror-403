"""
Route handlers for metadata store operations.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from pycharter.api.dependencies.database import get_db_session
from pycharter.api.dependencies.store import get_metadata_store
from pycharter.api.utils import ensure_uuid, get_by_id_or_404, model_to_dict, safe_uuid_to_str
from pycharter.api.models.metadata import (
    CoercionRulesStoreRequest,
    MetadataGetRequest,
    MetadataGetResponse,
    MetadataStoreRequest,
    MetadataStoreResponse,
    RulesGetResponse,
    RulesStoreResponse,
    SchemaGetRequest,
    SchemaGetResponse,
    SchemaListItem,
    SchemaListResponse,
    SchemaStoreRequest,
    SchemaStoreResponse,
    ValidationRulesStoreRequest,
)
from pycharter.api.models.metadata_entities import (
    DomainCreateRequest,
    DomainUpdateRequest,
    EnvironmentCreateRequest,
    EnvironmentUpdateRequest,
    OwnerCreateRequest,
    OwnerUpdateRequest,
    StorageLocationCreateRequest,
    StorageLocationUpdateRequest,
    SystemCreateRequest,
    SystemUpdateRequest,
    TagCreateRequest,
    TagUpdateRequest,
)
from pycharter.db.models import (
    DataContractModel,
    DomainModel,
    EnvironmentModel,
    OwnerModel,
    StorageLocationModel,
    SystemModel,
    TagModel,
)
from pycharter.metadata_store import MetadataStoreClient
from pycharter.utils.version import compare_versions, get_latest_version

router = APIRouter()


@router.post(
    "/metadata/schemas",
    response_model=SchemaStoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store a schema",
    description="Store a JSON Schema definition in the metadata store. Validates version numbers and prevents duplicate contracts.",
    response_description="Stored schema information",
)
async def store_schema(
    request: SchemaStoreRequest,
    store: MetadataStoreClient = Depends(get_metadata_store),
    db: Session = Depends(get_db_session),
) -> SchemaStoreResponse:
    """
    Store a schema in the metadata store.
    
    This endpoint stores a JSON Schema definition with a given name and version
    in the metadata store. The schema can later be retrieved by its ID and version.
    
    **Version Validation:**
    - Prevents duplicate contracts (same name + version)
    - Ensures new versions are higher than existing versions
    - Prevents overwriting existing contracts
    
    Args:
        request: Schema store request containing schema name, schema definition, and version
        store: Metadata store dependency
        db: Database session for contract validation
        
    Returns:
        Stored schema information including schema_id
        
    Raises:
        HTTPException: If schema storage fails, duplicate contract exists, or version is invalid
    """
    # Check for existing contracts with the same name
    existing_contracts = db.query(DataContractModel).filter(
        DataContractModel.name == request.schema_name
    ).all()
    
    if existing_contracts:
        # Check if exact duplicate (same name + version)
        for contract in existing_contracts:
            if contract.version == request.version:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Contract '{request.schema_name}' with version '{request.version}' already exists. "
                        f"Cannot create duplicate contracts. Use a different version number."
                    ),
                )
        
        # Get all existing versions for this contract name
        existing_versions = [c.version for c in existing_contracts]
        latest_version = get_latest_version(existing_versions)
        
        if latest_version:
            # Validate that new version is higher than the latest existing version
            version_comparison = compare_versions(request.version, latest_version)
            if version_comparison <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Version '{request.version}' must be higher than the latest existing version "
                        f"'{latest_version}' for contract '{request.schema_name}'. "
                        f"Existing versions: {', '.join(existing_versions)}"
                    ),
                )
    
    # Store the schema (this will create the data contract if it doesn't exist)
    try:
        schema_id = store.store_schema(
            schema_name=request.schema_name,
            schema=request.schema,
            version=request.version,
        )
    except ValueError as e:
        # Re-raise ValueError as HTTPException
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    return SchemaStoreResponse(
        schema_id=schema_id,
        schema_name=request.schema_name,
        version=request.version,
    )


@router.get(
    "/metadata/schemas/{schema_id}",
    response_model=SchemaGetResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a schema",
    description="Retrieve a schema from the metadata store by ID and optional version",
    response_description="Schema definition",
)
async def get_schema(
    schema_id: str,
    version: str | None = Query(None, description="Schema version (default: latest)"),
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> SchemaGetResponse:
    """
    Get a schema from the metadata store.
    
    This endpoint retrieves a schema definition by its ID. If a version is specified,
    that specific version is returned; otherwise, the latest version is returned.
    
    Args:
        schema_id: Schema identifier
        version: Optional schema version (default: latest)
        store: Metadata store dependency
        
    Returns:
        Schema definition
        
    Raises:
        HTTPException: If schema retrieval fails or schema not found
    """
    schema = store.get_schema(schema_id, version=version)
    
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema not found: {schema_id}",
        )
    
    return SchemaGetResponse(
        schema=schema,
        version=schema.get("version") if isinstance(schema, dict) else None,
    )


@router.post(
    "/metadata/metadata",
    response_model=MetadataStoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store metadata",
    description="Store metadata for a resource in the metadata store",
    response_description="Stored metadata information",
)
async def store_metadata(
    request: MetadataStoreRequest,
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> MetadataStoreResponse:
    """
    Store metadata for a schema in the metadata store.
    
    This endpoint stores metadata associated with a schema.
    The metadata can include ownership information, governance rules, and other metadata.
    
    Args:
        request: Metadata store request containing schema_id, metadata, and optional version
        store: Metadata store dependency
        
    Returns:
        Stored metadata information including metadata_id
        
    Raises:
        HTTPException: If metadata storage fails
    """
    metadata_id = store.store_metadata(
        schema_id=request.schema_id,
        metadata=request.metadata,
        version=request.version,
    )
    
    return MetadataStoreResponse(
        metadata_id=metadata_id,
        schema_id=request.schema_id,
    )


@router.get(
    "/metadata/metadata/{schema_id}",
    response_model=MetadataGetResponse,
    status_code=status.HTTP_200_OK,
    summary="Get metadata",
    description="Retrieve metadata for a schema from the metadata store",
    response_description="Metadata dictionary",
)
async def get_metadata(
    schema_id: str,
    version: str | None = Query(None, description="Metadata version (default: latest)"),
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> MetadataGetResponse:
    """
    Get metadata for a schema from the metadata store.
    
    This endpoint retrieves metadata associated with a schema by its ID and optional version.
    
    Args:
        schema_id: Schema identifier
        version: Optional metadata version (default: latest)
        store: Metadata store dependency
        
    Returns:
        Metadata dictionary
        
    Raises:
        HTTPException: If metadata retrieval fails or metadata not found
    """
    metadata = store.get_metadata(
        schema_id=schema_id,
        version=version,
    )
    
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Metadata not found for schema: {schema_id}",
        )
    
    return MetadataGetResponse(metadata=metadata)


@router.post(
    "/metadata/coercion-rules",
    response_model=RulesStoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store coercion rules",
    description="Store coercion rules for a schema in the metadata store",
    response_description="Stored rules information",
)
async def store_coercion_rules(
    request: CoercionRulesStoreRequest,
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> RulesStoreResponse:
    """
    Store coercion rules for a schema in the metadata store.
    
    This endpoint stores coercion rules that define how data should be transformed
    before validation. Coercion rules are versioned and associated with a schema.
    
    Args:
        request: Coercion rules store request containing schema_id, coercion_rules, and version
        store: Metadata store dependency
        
    Returns:
        Stored rules information including rule_id
        
    Raises:
        HTTPException: If coercion rules storage fails
    """
    rule_id = store.store_coercion_rules(
        schema_id=request.schema_id,
        coercion_rules=request.coercion_rules,
        version=request.version or "1.0.0",
    )
    
    return RulesStoreResponse(
        rule_id=rule_id,
        schema_id=request.schema_id,
        version=request.version or "1.0.0",
    )


@router.post(
    "/metadata/validation-rules",
    response_model=RulesStoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store validation rules",
    description="Store validation rules for a schema in the metadata store",
    response_description="Stored rules information",
)
async def store_validation_rules(
    request: ValidationRulesStoreRequest,
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> RulesStoreResponse:
    """
    Store validation rules for a schema in the metadata store.
    
    This endpoint stores validation rules that define custom validation logic
    beyond the JSON Schema validation. Validation rules are versioned and associated with a schema.
    
    Args:
        request: Validation rules store request containing schema_id, validation_rules, and version
        store: Metadata store dependency
        
    Returns:
        Stored rules information including rule_id
        
    Raises:
        HTTPException: If validation rules storage fails
    """
    rule_id = store.store_validation_rules(
        schema_id=request.schema_id,
        validation_rules=request.validation_rules,
        version=request.version or "1.0.0",
    )
    
    return RulesStoreResponse(
        rule_id=rule_id,
        schema_id=request.schema_id,
        version=request.version or "1.0.0",
    )


@router.get(
    "/metadata/schemas",
    response_model=SchemaListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all schemas",
    description="Retrieve a list of all schemas stored in the metadata store",
    response_description="List of schemas",
)
async def list_schemas(
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> SchemaListResponse:
    """
    List all schemas in the metadata store.
    
    This endpoint retrieves a list of all schemas with their basic information
    (id, name, title, version).
    
    Args:
        store: Metadata store dependency
        
    Returns:
        List of schemas with metadata
        
    Raises:
        HTTPException: If schema listing fails
    """
    schemas = store.list_schemas()
    
    schema_items = [
        SchemaListItem(
            id=schema.get("id", ""),
            name=schema.get("name"),
            title=schema.get("title"),
            version=schema.get("version"),
        )
        for schema in schemas
    ]
    
    return SchemaListResponse(
        schemas=schema_items,
        count=len(schema_items),
    )


@router.get(
    "/metadata/artifacts",
    status_code=status.HTTP_200_OK,
    summary="List all artifacts",
    description="Retrieve lists of all artifacts (schemas, coercion rules, validation rules, metadata) with their titles and versions",
    response_description="Lists of artifacts",
)
async def list_artifacts(
    db: Session = Depends(get_db_session),
) -> Dict[str, List[Dict[str, Any]]]:
    """
    List all artifacts grouped by type.
    
    Returns lists of schemas, coercion rules, validation rules, and metadata records
    with their titles and versions, allowing users to select existing artifacts when
    creating new contracts.
    
    Args:
        db: Database session dependency
        
    Returns:
        Dictionary with lists of artifacts by type
    """
    from pycharter.db.models import (
        CoercionRuleModel,
        MetadataRecordModel,
        SchemaModel,
        ValidationRuleModel,
    )
    
    # Get all schemas
    schemas = db.query(SchemaModel).order_by(SchemaModel.title, SchemaModel.version).all()
    schema_list = [
        {"title": s.title, "version": s.version, "id": str(s.id)}
        for s in schemas
    ]
    
    # Get all coercion rules
    coercion_rules = db.query(CoercionRuleModel).order_by(CoercionRuleModel.title, CoercionRuleModel.version).all()
    coercion_list = [
        {"title": cr.title, "version": cr.version, "id": str(cr.id)}
        for cr in coercion_rules
    ]
    
    # Get all validation rules
    validation_rules = db.query(ValidationRuleModel).order_by(ValidationRuleModel.title, ValidationRuleModel.version).all()
    validation_list = [
        {"title": vr.title, "version": vr.version, "id": str(vr.id)}
        for vr in validation_rules
    ]
    
    # Get all metadata records
    metadata_records = db.query(MetadataRecordModel).order_by(MetadataRecordModel.title, MetadataRecordModel.version).all()
    metadata_list = [
        {"title": mr.title, "version": mr.version, "id": str(mr.id)}
        for mr in metadata_records
    ]
    
    return {
        "schemas": schema_list,
        "coercion_rules": coercion_list,
        "validation_rules": validation_list,
        "metadata": metadata_list,
    }


@router.get(
    "/metadata/coercion-rules/{schema_id}",
    response_model=RulesGetResponse,
    status_code=status.HTTP_200_OK,
    summary="Get coercion rules",
    description="Retrieve coercion rules for a schema from the metadata store",
    response_description="Coercion rules dictionary",
)
async def get_coercion_rules(
    schema_id: str,
    version: str | None = Query(None, description="Rules version (default: latest)"),
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> RulesGetResponse:
    """
    Get coercion rules for a schema from the metadata store.
    
    This endpoint retrieves coercion rules associated with a schema. If a version
    is specified, that specific version is returned; otherwise, the latest version
    is returned.
    
    Args:
        schema_id: Schema identifier
        version: Optional rules version (default: latest)
        store: Metadata store dependency
        
    Returns:
        Coercion rules dictionary
        
    Raises:
        HTTPException: If coercion rules retrieval fails or rules not found
    """
    rules = store.get_coercion_rules(schema_id, version=version)
    
    if not rules:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coercion rules not found for schema: {schema_id}",
        )
    
    return RulesGetResponse(
        rules=rules,
        schema_id=schema_id,
        version=version,
    )


@router.get(
    "/metadata/validation-rules/{schema_id}",
    response_model=RulesGetResponse,
    status_code=status.HTTP_200_OK,
    summary="Get validation rules",
    description="Retrieve validation rules for a schema from the metadata store",
    response_description="Validation rules dictionary",
)
async def get_validation_rules(
    schema_id: str,
    version: str | None = Query(None, description="Rules version (default: latest)"),
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> RulesGetResponse:
    """
    Get validation rules for a schema from the metadata store.
    
    This endpoint retrieves validation rules associated with a schema. If a version
    is specified, that specific version is returned; otherwise, the latest version
    is returned.
    
    Args:
        schema_id: Schema identifier
        version: Optional rules version (default: latest)
        store: Metadata store dependency
        
    Returns:
        Validation rules dictionary
        
    Raises:
        HTTPException: If validation rules retrieval fails or rules not found
    """
    rules = store.get_validation_rules(schema_id, version=version)
    
    if not rules:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation rules not found for schema: {schema_id}",
        )
    
    return RulesGetResponse(
        rules=rules,
        schema_id=schema_id,
        version=version,
    )


@router.get(
    "/metadata/schemas/{schema_id}/complete",
    response_model=SchemaGetResponse,
    status_code=status.HTTP_200_OK,
    summary="Get complete schema with rules",
    description="Retrieve a complete schema with coercion and validation rules merged from the metadata store",
    response_description="Complete schema with rules merged",
)
async def get_complete_schema(
    schema_id: str,
    version: str | None = Query(None, description="Schema version (default: latest)"),
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> SchemaGetResponse:
    """
    Get complete schema with coercion and validation rules merged.
    
    This endpoint retrieves a schema and automatically merges coercion and validation
    rules into it, returning a complete schema ready for validation.
    
    Args:
        schema_id: Schema identifier
        version: Optional schema version (default: latest)
        store: Metadata store dependency
        
    Returns:
        Complete schema dictionary with rules merged
        
    Raises:
        HTTPException: If schema retrieval fails or schema not found
    """
    complete_schema = store.get_complete_schema(schema_id, version=version)
    
    if not complete_schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema not found: {schema_id}",
        )
    
    return SchemaGetResponse(
        schema=complete_schema,
        version=complete_schema.get("version") if isinstance(complete_schema, dict) else None,
    )


@router.get(
    "/metadata/{entity_type}",
    status_code=status.HTTP_200_OK,
    summary="List metadata entities by type",
    description="Retrieve a list of metadata entities by type (owners, domains, systems, environments, storage_locations, tags)",
    response_description="List of entity dictionaries",
)
async def list_metadata_entities(
    entity_type: str,
    db: Session = Depends(get_db_session),
) -> List[Dict[str, Any]]:
    """
    List metadata entities by type.
    
    Supported entity types:
    - owners
    - domains
    - systems
    - environments
    - storage_locations
    - tags
    
    Args:
        entity_type: Type of metadata entity to list
        db: Database session dependency
        
    Returns:
        List of entity dictionaries
        
    Raises:
        HTTPException: If entity type is not supported
    """
    entity_map = {
        'owners': OwnerModel,
        'domains': DomainModel,
        'systems': SystemModel,
        'environments': EnvironmentModel,
        'storage_locations': StorageLocationModel,
        'tags': TagModel,
    }
    
    if entity_type not in entity_map:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown entity type: {entity_type}. Supported types: {', '.join(entity_map.keys())}",
        )
    
    model_class = entity_map[entity_type]
    entities = db.query(model_class).all()
    
    # Special handling for storage_locations to include related data
    if entity_type == 'storage_locations':
        result = []
        for entity in entities:
            data = model_to_dict(entity)
            if entity.system:
                data['system_name'] = entity.system.name
            if entity.environment:
                data['environment_name'] = entity.environment.name
            result.append(data)
        return result
    
    return [model_to_dict(entity) for entity in entities]


# Create endpoints (POST routes for creating entities)
@router.post(
    "/metadata/owners",
    status_code=status.HTTP_201_CREATED,
    summary="Create owner",
    description="Create a new owner",
    response_description="Created owner",
)
async def create_owner(
    request: OwnerCreateRequest,
    db: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Create a new owner."""
    # Check if owner already exists
    existing = db.query(OwnerModel).filter(OwnerModel.id == request.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Owner with ID '{request.id}' already exists",
        )
    
    owner = OwnerModel(
        id=request.id,
        name=request.name,
        email=request.email,
        team=request.team,
        additional_info=request.additional_info,
    )
    db.add(owner)
    db.commit()
    db.refresh(owner)
    return model_to_dict(owner)


@router.post(
    "/metadata/domains",
    status_code=status.HTTP_201_CREATED,
    summary="Create domain",
    description="Create a new domain",
    response_description="Created domain",
)
async def create_domain(
    request: DomainCreateRequest,
    db: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Create a new domain."""
    # Check if domain already exists
    existing = db.query(DomainModel).filter(DomainModel.name == request.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Domain with name '{request.name}' already exists",
        )
    
    domain = DomainModel(
        name=request.name,
        description=request.description,
    )
    db.add(domain)
    db.commit()
    db.refresh(domain)
    return model_to_dict(domain)


@router.post(
    "/metadata/systems",
    status_code=status.HTTP_201_CREATED,
    summary="Create system",
    description="Create a new system",
    response_description="Created system",
)
async def create_system(
    request: SystemCreateRequest,
    db: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Create a new system."""
    # Check if system already exists
    existing = db.query(SystemModel).filter(SystemModel.name == request.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"System with name '{request.name}' already exists",
        )
    
    system = SystemModel(
        name=request.name,
        app_id=request.app_id,
        description=request.description,
    )
    db.add(system)
    db.commit()
    db.refresh(system)
    return model_to_dict(system)


@router.post(
    "/metadata/environments",
    status_code=status.HTTP_201_CREATED,
    summary="Create environment",
    description="Create a new environment",
    response_description="Created environment",
)
async def create_environment(
    request: EnvironmentCreateRequest,
    db: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Create a new environment."""
    # Check if environment already exists
    existing = db.query(EnvironmentModel).filter(EnvironmentModel.name == request.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Environment with name '{request.name}' already exists",
        )
    
    environment = EnvironmentModel(
        name=request.name,
        description=request.description,
        environment_type=request.environment_type,
        is_production=request.is_production,
        additional_metadata=request.additional_metadata,
    )
    db.add(environment)
    db.commit()
    db.refresh(environment)
    return model_to_dict(environment)


@router.post(
    "/metadata/storage_locations",
    status_code=status.HTTP_201_CREATED,
    summary="Create storage location",
    description="Create a new storage location",
    response_description="Created storage location",
)
async def create_storage_location(
    request: StorageLocationCreateRequest,
    db: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Create a new storage location."""
    # Check if storage location already exists
    existing = db.query(StorageLocationModel).filter(StorageLocationModel.name == request.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Storage location with name '{request.name}' already exists",
        )
    
    storage_location = StorageLocationModel(
        name=request.name,
        location_type=request.location_type,
        cluster=request.cluster,
        database=request.database,
        collection=request.collection,
        schema_name=request.schema_name,
        table_name=request.table_name,
        connection_string=request.connection_string,
        system_id=request.system_id,
        environment_id=request.environment_id,
        additional_metadata=request.additional_metadata,
    )
    db.add(storage_location)
    db.commit()
    db.refresh(storage_location)
    
    # Include related data
    result = model_to_dict(storage_location)
    if storage_location.system:
        result['system_name'] = storage_location.system.name
    if storage_location.environment:
        result['environment_name'] = storage_location.environment.name
    return result


@router.post(
    "/metadata/tags",
    status_code=status.HTTP_201_CREATED,
    summary="Create tag",
    description="Create a new tag",
    response_description="Created tag",
)
async def create_tag(
    request: TagCreateRequest,
    db: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Create a new tag."""
    # Check if tag already exists
    existing = db.query(TagModel).filter(TagModel.name == request.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tag with name '{request.name}' already exists",
        )
    
    tag = TagModel(
        name=request.name,
        description=request.description,
        category=request.category,
        color=request.color,
        additional_metadata=request.additional_metadata,
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return model_to_dict(tag)


# Update endpoints
@router.put(
    "/metadata/owners/{owner_id}",
    status_code=status.HTTP_200_OK,
    summary="Update owner",
    description="Update an existing owner",
    response_description="Updated owner",
)
async def update_owner(
    owner_id: str,
    request: OwnerUpdateRequest,
    db: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Update an existing owner."""
    owner = get_by_id_or_404(
        db, OwnerModel, owner_id,
        error_message=f"Owner with ID '{owner_id}' not found",
        model_name="Owner"
    )
    
    if request.name is not None:
        owner.name = request.name
    if request.email is not None:
        owner.email = request.email
    if request.team is not None:
        owner.team = request.team
    if request.additional_info is not None:
        owner.additional_info = request.additional_info
    
    db.commit()
    db.refresh(owner)
    return model_to_dict(owner)


@router.put(
    "/metadata/domains/{domain_id}",
    status_code=status.HTTP_200_OK,
    summary="Update domain",
    description="Update an existing domain",
    response_description="Updated domain",
)
async def update_domain(
    domain_id: str,
    request: DomainUpdateRequest,
    db: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Update an existing domain."""
    try:
        ensure_uuid(domain_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid domain ID format: {domain_id}",
        )
    
    domain = get_by_id_or_404(
        db, DomainModel, domain_id,
        error_message=f"Domain with ID '{domain_id}' not found",
        model_name="Domain"
    )
    
    if request.name is not None:
        domain.name = request.name
    if request.description is not None:
        domain.description = request.description
    
    db.commit()
    db.refresh(domain)
    return model_to_dict(domain)


@router.put(
    "/metadata/systems/{system_id}",
    status_code=status.HTTP_200_OK,
    summary="Update system",
    description="Update an existing system",
    response_description="Updated system",
)
async def update_system(
    system_id: str,
    request: SystemUpdateRequest,
    db: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Update an existing system."""
    try:
        ensure_uuid(system_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid system ID format: {system_id}",
        )
    
    system = get_by_id_or_404(
        db, SystemModel, system_id,
        error_message=f"System with ID '{system_id}' not found",
        model_name="System"
    )
    
    if request.name is not None:
        system.name = request.name
    if request.app_id is not None:
        system.app_id = request.app_id
    if request.description is not None:
        system.description = request.description
    
    db.commit()
    db.refresh(system)
    return model_to_dict(system)


@router.put(
    "/metadata/environments/{environment_id}",
    status_code=status.HTTP_200_OK,
    summary="Update environment",
    description="Update an existing environment",
    response_description="Updated environment",
)
async def update_environment(
    environment_id: str,
    request: EnvironmentUpdateRequest,
    db: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Update an existing environment."""
    try:
        ensure_uuid(environment_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid environment ID format: {environment_id}",
        )
    
    environment = get_by_id_or_404(
        db, EnvironmentModel, environment_id,
        error_message=f"Environment with ID '{environment_id}' not found",
        model_name="Environment"
    )
    
    if request.name is not None:
        environment.name = request.name
    if request.description is not None:
        environment.description = request.description
    if request.environment_type is not None:
        environment.environment_type = request.environment_type
    if request.is_production is not None:
        environment.is_production = request.is_production
    if request.additional_metadata is not None:
        environment.additional_metadata = request.additional_metadata
    
    db.commit()
    db.refresh(environment)
    return model_to_dict(environment)


@router.put(
    "/metadata/storage_locations/{storage_location_id}",
    status_code=status.HTTP_200_OK,
    summary="Update storage location",
    description="Update an existing storage location",
    response_description="Updated storage location",
)
async def update_storage_location(
    storage_location_id: str,
    request: StorageLocationUpdateRequest,
    db: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Update an existing storage location."""
    try:
        ensure_uuid(storage_location_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid storage location ID format: {storage_location_id}",
        )
    
    storage_location = get_by_id_or_404(
        db, StorageLocationModel, storage_location_id,
        error_message=f"Storage location with ID '{storage_location_id}' not found",
        model_name="StorageLocation"
    )
    
    if request.name is not None:
        storage_location.name = request.name
    if request.location_type is not None:
        storage_location.location_type = request.location_type
    if request.cluster is not None:
        storage_location.cluster = request.cluster
    if request.database is not None:
        storage_location.database = request.database
    if request.collection is not None:
        storage_location.collection = request.collection
    if request.schema_name is not None:
        storage_location.schema_name = request.schema_name
    if request.table_name is not None:
        storage_location.table_name = request.table_name
    if request.connection_string is not None:
        storage_location.connection_string = request.connection_string
    if request.system_id is not None:
        storage_location.system_id = request.system_id
    if request.environment_id is not None:
        storage_location.environment_id = request.environment_id
    if request.additional_metadata is not None:
        storage_location.additional_metadata = request.additional_metadata
    
    db.commit()
    db.refresh(storage_location)
    
    # Include related data
    result = model_to_dict(storage_location)
    if storage_location.system:
        result['system_name'] = storage_location.system.name
    if storage_location.environment:
        result['environment_name'] = storage_location.environment.name
    return result


@router.put(
    "/metadata/tags/{tag_id}",
    status_code=status.HTTP_200_OK,
    summary="Update tag",
    description="Update an existing tag",
    response_description="Updated tag",
)
async def update_tag(
    tag_id: str,
    request: TagUpdateRequest,
    db: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Update an existing tag."""
    try:
        ensure_uuid(tag_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tag ID format: {tag_id}",
        )
    
    tag = get_by_id_or_404(
        db, TagModel, tag_id,
        error_message=f"Tag with ID '{tag_id}' not found",
        model_name="Tag"
    )
    
    if request.name is not None:
        tag.name = request.name
    if request.description is not None:
        tag.description = request.description
    if request.category is not None:
        tag.category = request.category
    if request.color is not None:
        tag.color = request.color
    if request.additional_metadata is not None:
        tag.additional_metadata = request.additional_metadata
    
    db.commit()
    db.refresh(tag)
    return model_to_dict(tag)

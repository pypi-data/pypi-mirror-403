"""
API routes for documentation generation.

Provides endpoints to generate human-readable documentation
from data contracts.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from pycharter.api.dependencies.store import get_metadata_store
from pycharter.api.models.docs import (
    DocsFormat,
    DocsRequest,
    DocsResponse,
    DocsSectionRequest,
    DocsSectionResponse,
)
from pycharter.contract_parser import parse_contract
from pycharter.docs_generator import DocsGenerator, generate_docs
from pycharter.docs_generator.renderers import HTMLRenderer, MarkdownRenderer
from pycharter.metadata_store import MetadataStoreClient

router = APIRouter(prefix="/docs", tags=["Documentation"])


@router.post(
    "/generate",
    response_model=DocsResponse,
    summary="Generate documentation from contract",
    description="Generate human-readable documentation from contract data",
)
async def generate_documentation(request: DocsRequest) -> DocsResponse:
    """
    Generate documentation from a contract.

    Accepts contract data and generates formatted documentation
    in the specified format (Markdown or HTML).
    """
    try:
        # Parse the contract
        contract = parse_contract(request.contract, validate=False)

        # Generate documentation
        docs = generate_docs(
            contract,
            format=request.format.value,
            include_schema=request.include_schema,
            include_coercions=request.include_coercions,
            include_validations=request.include_validations,
            include_metadata=request.include_metadata,
        )

        # Extract schema name and version
        schema_name = contract.schema.get("title") or contract.metadata.get("title")
        version = contract.versions.get("schema") or contract.schema.get("version")

        return DocsResponse(
            documentation=docs,
            format=request.format,
            schema_name=schema_name,
            version=version,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate documentation: {e}")


@router.post(
    "/section",
    response_model=DocsSectionResponse,
    summary="Generate a specific documentation section",
    description="Generate a specific section of documentation from contract data",
)
async def generate_section(request: DocsSectionRequest) -> DocsSectionResponse:
    """
    Generate a specific section of documentation.

    Sections: 'schema', 'coercions', 'validations', 'metadata'
    """
    try:
        # Parse the contract
        contract = parse_contract(request.contract, validate=False)

        # Select renderer
        if request.format == DocsFormat.HTML:
            renderer = HTMLRenderer()
        else:
            renderer = MarkdownRenderer()

        generator = DocsGenerator(renderer=renderer)

        # Generate the requested section
        section = request.section.lower()
        if section == "schema":
            content = generator.generate_schema_section(contract.schema)
        elif section in ("coercions", "coercion_rules"):
            content = generator.generate_coercion_section(contract.coercion_rules)
        elif section in ("validations", "validation_rules"):
            content = generator.generate_validation_section(contract.validation_rules)
        elif section == "metadata":
            content = generator.generate_metadata_section(contract)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown section: {section}. Valid sections: schema, coercions, validations, metadata",
            )

        return DocsSectionResponse(
            section=section,
            content=content,
            format=request.format,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate section: {e}")


@router.get(
    "/{schema_name}",
    response_model=DocsResponse,
    summary="Generate documentation for a stored schema",
    description="Generate documentation for a schema stored in the metadata store",
)
async def get_schema_docs(
    schema_name: str,
    version: Optional[str] = Query(default=None, description="Schema version (latest if not specified)"),
    format: DocsFormat = Query(default=DocsFormat.MARKDOWN, description="Output format"),
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> DocsResponse:
    """
    Generate documentation for a schema from the metadata store.

    Retrieves the schema from the store and generates documentation.
    """
    try:
        # Get the complete schema from store
        schema_data = store.get_complete_schema(schema_name, version=version)

        if not schema_data:
            raise HTTPException(
                status_code=404, detail=f"Schema not found: {schema_name}"
            )

        # Build contract data from stored components
        contract_data = {"schema": schema_data}

        # Try to get additional components
        try:
            coercion_rules = store.get_coercion_rules(schema_name, version=version)
            if coercion_rules:
                contract_data["coercion_rules"] = coercion_rules
        except Exception:
            pass

        try:
            validation_rules = store.get_validation_rules(schema_name, version=version)
            if validation_rules:
                contract_data["validation_rules"] = validation_rules
        except Exception:
            pass

        try:
            metadata = store.get_metadata(schema_name, version=version)
            if metadata:
                contract_data["metadata"] = metadata
        except Exception:
            pass

        # Parse and generate docs
        contract = parse_contract(contract_data, validate=False)
        docs = generate_docs(contract, format=format.value)

        return DocsResponse(
            documentation=docs,
            format=format,
            schema_name=schema_name,
            version=version or contract.versions.get("schema"),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate documentation: {e}")

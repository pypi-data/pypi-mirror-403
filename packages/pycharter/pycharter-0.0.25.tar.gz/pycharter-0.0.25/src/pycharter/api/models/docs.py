"""
API models for documentation generation endpoints.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DocsFormat(str, Enum):
    """Supported documentation output formats."""

    MARKDOWN = "markdown"
    HTML = "html"


class DocsRequest(BaseModel):
    """Request model for generating documentation from contract data."""

    contract: dict = Field(..., description="Contract data to generate documentation for")
    format: DocsFormat = Field(
        default=DocsFormat.MARKDOWN, description="Output format for documentation"
    )
    include_schema: bool = Field(default=True, description="Include schema fields section")
    include_coercions: bool = Field(
        default=True, description="Include coercion rules section"
    )
    include_validations: bool = Field(
        default=True, description="Include validation rules section"
    )
    include_metadata: bool = Field(
        default=True, description="Include metadata/ownership section"
    )


class DocsResponse(BaseModel):
    """Response model for generated documentation."""

    documentation: str = Field(..., description="Generated documentation content")
    format: DocsFormat = Field(..., description="Format of the generated documentation")
    schema_name: Optional[str] = Field(
        default=None, description="Name of the schema documented"
    )
    version: Optional[str] = Field(
        default=None, description="Version of the schema documented"
    )


class DocsSectionRequest(BaseModel):
    """Request model for generating a specific documentation section."""

    contract: dict = Field(..., description="Contract data to generate documentation for")
    section: str = Field(
        ...,
        description="Section to generate: 'schema', 'coercions', 'validations', 'metadata'",
    )
    format: DocsFormat = Field(
        default=DocsFormat.MARKDOWN, description="Output format for documentation"
    )


class DocsSectionResponse(BaseModel):
    """Response model for a documentation section."""

    section: str = Field(..., description="Name of the section generated")
    content: str = Field(..., description="Generated section content")
    format: DocsFormat = Field(..., description="Format of the generated content")

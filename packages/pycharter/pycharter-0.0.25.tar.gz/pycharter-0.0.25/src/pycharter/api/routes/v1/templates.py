"""
Route handlers for template file downloads.

Provides endpoints to download template files for:
- Contract artifacts (schema, metadata, coercion/validation rules, contract)
- ETL configs (extract, transform, load)
"""

import io
import logging
import zipfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse, Response

logger = logging.getLogger(__name__)
router = APIRouter()


def _find_template_dir() -> Path:
    """
    Find contract template directory in multiple locations (package, source, etc.).

    Contract templates (schema, metadata, coercion/validation rules, contract)
    live under templates/contract/.

    Priority:
    1. Installed package location (pycharter/data/templates/contract/)
    2. Source location (relative to api/routes/v1/)
    3. Legacy location (data/aviation_examples/template/)

    Returns:
        Path to contract template directory (templates/contract/)
    """
    # Try installed package location (when package is installed)
    try:
        import pycharter

        pycharter_path = Path(pycharter.__file__).parent
        package_contract = pycharter_path / "data" / "templates" / "contract"
        if (
            package_contract.exists()
            and (package_contract / "template_schema.yaml").exists()
        ):
            return package_contract
    except (ImportError, AttributeError):
        pass

    # Try source locations (development)
    possible_paths = [
        Path(__file__).parent.parent.parent.parent
        / "pycharter"
        / "data"
        / "templates"
        / "contract",
        Path(__file__).parent.parent.parent.parent
        / "data"
        / "aviation_examples"
        / "template",
        Path.cwd() / "pycharter" / "data" / "templates" / "contract",
        Path.cwd() / "data" / "aviation_examples" / "template",
    ]

    for template_path in possible_paths:
        if template_path.exists() and (template_path / "template_schema.yaml").exists():
            return template_path

    # Fallback to original location
    fallback = (
        Path(__file__).parent.parent.parent.parent
        / "data"
        / "aviation_examples"
        / "template"
    )
    return fallback


def _get_template_path(filename: str) -> Path:
    """Get the full path to a contract template file."""
    template_dir = _find_template_dir()
    template_path = template_dir / filename
    if not template_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template file not found: {filename}",
        )
    return template_path


def _find_etl_template_dir() -> Path:
    """
    Find ETL template directory (extract/transform/load configs).

    ETL templates live under pycharter/data/templates/etl/.
    Priority: installed package, then source/dev paths.
    """
    try:
        import pycharter

        pycharter_path = Path(pycharter.__file__).parent
        etl_dir = pycharter_path / "data" / "templates" / "etl"
        if etl_dir.exists() and (etl_dir / "extract_http_simple.yaml").exists():
            return etl_dir
    except (ImportError, AttributeError):
        pass

    dev_paths = [
        Path(__file__).parent.parent.parent.parent / "pycharter" / "data" / "templates" / "etl",
        Path.cwd() / "pycharter" / "data" / "templates" / "etl",
    ]
    for p in dev_paths:
        if p.exists() and (p / "extract_http_simple.yaml").exists():
            return p

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="ETL template directory not found",
    )


def _list_etl_templates() -> list[str]:
    """Return sorted list of ETL template filenames (yaml/yml and README.md)."""
    etl_dir = _find_etl_template_dir()
    allowed = []
    for f in etl_dir.iterdir():
        if not f.is_file():
            continue
        if f.suffix in (".yaml", ".yml") or f.name == "README.md":
            allowed.append(f.name)
    return sorted(allowed)


def _get_etl_template_path(filename: str) -> Path:
    """Get path to an ETL template file; filename must be in allowlist (no path traversal)."""
    safe_name = Path(filename).name
    if safe_name != filename or ".." in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename",
        )
    allowed = _list_etl_templates()
    if safe_name not in allowed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ETL template not found: {filename}. Available: {allowed[:10]}{'...' if len(allowed) > 10 else ''}",
        )
    return _find_etl_template_dir() / safe_name


@router.get(
    "/templates/schema",
    summary="Download schema template",
    description="Download a template YAML file for creating a new schema",
    response_description="YAML template file",
    tags=["Templates"],
)
async def download_schema_template() -> FileResponse:
    """
    Download the schema template file.

    Returns:
        YAML file containing a template schema structure
    """
    try:
        template_path = _get_template_path("template_schema.yaml")
        return FileResponse(
            path=str(template_path),
            media_type="application/x-yaml",
            filename="template_schema.yaml",
            headers={
                "Content-Disposition": 'attachment; filename="template_schema.yaml"',
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving schema template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to serve schema template: {str(e)}",
        )


@router.get(
    "/templates/metadata",
    summary="Download metadata template",
    description="Download a template YAML file for creating new metadata",
    response_description="YAML template file",
    tags=["Templates"],
)
async def download_metadata_template() -> FileResponse:
    """
    Download the metadata template file.

    Returns:
        YAML file containing a template metadata structure
    """
    try:
        template_path = _get_template_path("template_metadata.yaml")
        return FileResponse(
            path=str(template_path),
            media_type="application/x-yaml",
            filename="template_metadata.yaml",
            headers={
                "Content-Disposition": 'attachment; filename="template_metadata.yaml"',
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving metadata template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to serve metadata template: {str(e)}",
        )


@router.get(
    "/templates/coercion-rules",
    summary="Download coercion rules template",
    description="Download a template YAML file for creating new coercion rules",
    response_description="YAML template file",
    tags=["Templates"],
)
async def download_coercion_rules_template() -> FileResponse:
    """
    Download the coercion rules template file.

    Returns:
        YAML file containing a template coercion rules structure
    """
    try:
        template_path = _get_template_path("template_coercion_rules.yaml")
        return FileResponse(
            path=str(template_path),
            media_type="application/x-yaml",
            filename="template_coercion_rules.yaml",
            headers={
                "Content-Disposition": 'attachment; filename="template_coercion_rules.yaml"',
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving coercion rules template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to serve coercion rules template: {str(e)}",
        )


@router.get(
    "/templates/validation-rules",
    summary="Download validation rules template",
    description="Download a template YAML file for creating new validation rules",
    response_description="YAML template file",
    tags=["Templates"],
)
async def download_validation_rules_template() -> FileResponse:
    """
    Download the validation rules template file.

    Returns:
        YAML file containing a template validation rules structure
    """
    try:
        template_path = _get_template_path("template_validation_rules.yaml")
        return FileResponse(
            path=str(template_path),
            media_type="application/x-yaml",
            filename="template_validation_rules.yaml",
            headers={
                "Content-Disposition": 'attachment; filename="template_validation_rules.yaml"',
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving validation rules template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to serve validation rules template: {str(e)}",
        )


@router.get(
    "/templates/contract-artifacts",
    summary="Download contract artifact templates",
    description="Download a ZIP archive containing all contract artifact templates (schema, metadata, coercion rules, validation rules, and contract)",
    response_description="ZIP archive containing template files",
    tags=["Templates"],
)
async def download_contract_artifacts() -> Response:
    """
    Download all contract artifact templates as a ZIP archive.

    The ZIP file contains:
    - template_schema.yaml
    - template_metadata.yaml
    - template_coercion_rules.yaml
    - template_validation_rules.yaml
    - template_contract.yaml

    Returns:
        ZIP file containing all template files
    """
    try:
        # Template files to include in the ZIP
        template_files = [
            "template_schema.yaml",
            "template_metadata.yaml",
            "template_coercion_rules.yaml",
            "template_validation_rules.yaml",
            "template_contract.yaml",
        ]

        # Create ZIP archive in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for template_file in template_files:
                template_path = _get_template_path(template_file)
                # Read file content and add to ZIP
                zip_file.write(template_path, arcname=template_file)

        # Get ZIP content
        zip_buffer.seek(0)
        zip_content = zip_buffer.read()
        zip_buffer.close()

        return Response(
            content=zip_content,
            media_type="application/zip",
            headers={
                "Content-Disposition": 'attachment; filename="contract_artifact_templates.zip"',
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating contract artifacts ZIP: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create contract artifacts ZIP: {str(e)}",
        )


# -----------------------------------------------------------------------------
# ETL config templates (extract, transform, load)
# -----------------------------------------------------------------------------


@router.get(
    "/templates/etl",
    summary="List ETL template filenames",
    description="Return a list of available ETL config template filenames (extract, transform, load). Use GET /templates/etl/{filename} to download one.",
    response_description="JSON array of template filenames",
    tags=["Templates"],
)
async def list_etl_templates() -> JSONResponse:
    """
    List available ETL config template filenames.

    Returns:
        JSON array of filenames, e.g. ["extract_http_simple.yaml", "transform_simple.yaml", ...]
    """
    try:
        names = _list_etl_templates()
        return JSONResponse(content={"templates": names})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing ETL templates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list ETL templates: {str(e)}",
        )


@router.get(
    "/templates/etl/{filename:path}",
    summary="Download an ETL config template",
    description="Download a single ETL template by filename (e.g. extract_http_simple.yaml, transform_simple.yaml, load_file.yaml). Use GET /templates/etl to see available names.",
    response_description="YAML or Markdown file",
    tags=["Templates"],
)
async def download_etl_template(filename: str):
    """
    Download one ETL config template file.

    Filename must be one of the names returned by GET /templates/etl.
    """
    try:
        template_path = _get_etl_template_path(filename)
        media_type = "text/markdown" if template_path.suffix == ".md" else "application/x-yaml"
        return FileResponse(
            path=str(template_path),
            media_type=media_type,
            filename=template_path.name,
            headers={"Content-Disposition": f'attachment; filename="{template_path.name}"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving ETL template {filename}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to serve ETL template: {str(e)}",
        )


@router.get(
    "/templates/etl-artifacts",
    summary="Download all ETL config templates",
    description="Download a ZIP archive of all ETL config templates (extract, transform, load YAMLs and README).",
    response_description="ZIP archive containing ETL template files",
    tags=["Templates"],
)
async def download_etl_artifacts() -> Response:
    """
    Download all ETL config templates as a ZIP archive.

    Contains extract_*.yaml, transform_*.yaml, load_*.yaml and README.md.
    Copy files into your contract dir as extract.yaml, transform.yaml, load.yaml.
    """
    try:
        etl_dir = _find_etl_template_dir()
        names = _list_etl_templates()
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for name in names:
                zip_file.write(etl_dir / name, arcname=name)
        zip_buffer.seek(0)
        content = zip_buffer.read()
        zip_buffer.close()
        return Response(
            content=content,
            media_type="application/zip",
            headers={"Content-Disposition": 'attachment; filename="etl_config_templates.zip"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating ETL templates ZIP: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create ETL templates ZIP: {str(e)}",
        )

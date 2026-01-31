"""
Documentation Generator - Core generation logic.

Transforms ContractMetadata into human-readable documentation.
"""

import json
from typing import Any, Dict, List, Optional, Union

from pycharter.contract_parser import ContractMetadata
from pycharter.docs_generator.renderers import DocsRenderer, MarkdownRenderer


class DocsGenerator:
    """
    Generate documentation from data contracts.

    Transforms ContractMetadata objects into human-readable documentation
    in various formats (Markdown, HTML, etc.).

    Example:
        >>> from pycharter import parse_contract_file
        >>> from pycharter.docs_generator import DocsGenerator
        >>>
        >>> contract = parse_contract_file("contract.yaml")
        >>> generator = DocsGenerator()
        >>> docs = generator.generate(contract)
        >>> print(docs)
    """

    def __init__(self, renderer: Optional[DocsRenderer] = None):
        """
        Initialize the documentation generator.

        Args:
            renderer: Renderer to use for output format. Defaults to MarkdownRenderer.
        """
        self.renderer = renderer or MarkdownRenderer()

    def generate(
        self,
        contract: ContractMetadata,
        include_schema: bool = True,
        include_coercions: bool = True,
        include_validations: bool = True,
        include_metadata: bool = True,
    ) -> str:
        """
        Generate full documentation for a contract.

        Args:
            contract: ContractMetadata object to document
            include_schema: Include schema field documentation
            include_coercions: Include coercion rules documentation
            include_validations: Include validation rules documentation
            include_metadata: Include metadata/ownership documentation

        Returns:
            Generated documentation as string
        """
        parts = []

        # Get title from schema or metadata
        title = self._get_title(contract)
        version = contract.versions.get("schema") or contract.schema.get("version")

        # Header
        parts.append(self.renderer.render_header(title, version))

        # Description
        description = contract.schema.get("description") or contract.metadata.get(
            "description"
        )
        if description:
            parts.append(self.renderer.render_description(description))

        # Schema section
        if include_schema and contract.schema:
            parts.append(self.generate_schema_section(contract.schema))

        # Coercion rules section
        if include_coercions and contract.coercion_rules:
            parts.append(self.generate_coercion_section(contract.coercion_rules))

        # Validation rules section
        if include_validations and contract.validation_rules:
            parts.append(self.generate_validation_section(contract.validation_rules))

        # Metadata section
        if include_metadata and contract.metadata:
            parts.append(self.generate_metadata_section(contract))

        # Footer for HTML
        if hasattr(self.renderer, "render_footer"):
            parts.append(self.renderer.render_footer())

        return "".join(parts)

    def generate_schema_section(self, schema: Dict[str, Any]) -> str:
        """
        Generate documentation for schema fields.

        Args:
            schema: JSON Schema dictionary

        Returns:
            Formatted schema documentation
        """
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))

        if not properties:
            return ""

        # Build table rows for fields
        headers = ["Field", "Type", "Required", "Description", "Constraints"]
        rows = []

        for field_name, field_def in properties.items():
            row = self._build_field_row(field_name, field_def, field_name in required)
            rows.append(row)

        table = self.renderer.render_table(headers, rows)
        return self.renderer.render_section("Schema Fields", table)

    def generate_coercion_section(self, rules: Dict[str, Any]) -> str:
        """
        Generate documentation for coercion rules.

        Args:
            rules: Coercion rules dictionary

        Returns:
            Formatted coercion documentation
        """
        # Filter out version key
        coercion_rules = {k: v for k, v in rules.items() if k != "version"}

        if not coercion_rules:
            return ""

        headers = ["Field", "Coercion", "Description"]
        rows = []

        for field, coercion in coercion_rules.items():
            if isinstance(coercion, str):
                coercion_name = coercion
                description = self._get_coercion_description(coercion_name)
            elif isinstance(coercion, dict):
                coercion_name = coercion.get("type", str(coercion))
                description = coercion.get(
                    "description", self._get_coercion_description(coercion_name)
                )
            else:
                coercion_name = str(coercion)
                description = ""

            rows.append([f"`{field}`", f"`{coercion_name}`", description])

        content = self.renderer.render_description(
            "Coercions are applied before validation to transform incoming data."
        )
        content += self.renderer.render_table(headers, rows)
        return self.renderer.render_section("Coercion Rules", content)

    def generate_validation_section(self, rules: Dict[str, Any]) -> str:
        """
        Generate documentation for validation rules.

        Args:
            rules: Validation rules dictionary

        Returns:
            Formatted validation documentation
        """
        # Filter out version key
        validation_rules = {k: v for k, v in rules.items() if k != "version"}

        if not validation_rules:
            return ""

        headers = ["Field", "Validation", "Configuration"]
        rows = []

        for field, validations in validation_rules.items():
            if isinstance(validations, dict):
                for val_name, val_config in validations.items():
                    config_str = self._format_config(val_config)
                    rows.append([f"`{field}`", f"`{val_name}`", config_str])
            elif isinstance(validations, str):
                rows.append([f"`{field}`", f"`{validations}`", ""])
            elif isinstance(validations, list):
                for val in validations:
                    rows.append([f"`{field}`", f"`{val}`", ""])

        content = self.renderer.render_description(
            "Validations are applied after coercion to ensure data meets requirements."
        )
        content += self.renderer.render_table(headers, rows)
        return self.renderer.render_section("Validation Rules", content)

    def generate_metadata_section(self, contract: ContractMetadata) -> str:
        """
        Generate documentation for contract metadata.

        Args:
            contract: ContractMetadata object

        Returns:
            Formatted metadata documentation
        """
        parts = []

        # Ownership section
        if contract.ownership:
            ownership_content = self._format_ownership(contract.ownership)
            parts.append(
                self.renderer.render_section("Ownership", ownership_content)
            )

        # Governance rules
        if contract.governance_rules:
            governance_content = self._format_governance(contract.governance_rules)
            parts.append(
                self.renderer.render_section("Governance Rules", governance_content)
            )

        # Version information
        if contract.versions:
            version_content = self._format_versions(contract.versions)
            parts.append(
                self.renderer.render_section("Version Information", version_content)
            )

        # Other metadata
        other_metadata = {
            k: v
            for k, v in contract.metadata.items()
            if k not in ["ownership", "governance_rules", "version"]
        }
        if other_metadata:
            other_content = self._format_metadata_dict(other_metadata)
            parts.append(
                self.renderer.render_section("Additional Metadata", other_content)
            )

        return "".join(parts)

    def _get_title(self, contract: ContractMetadata) -> str:
        """Extract title from contract."""
        # Try schema title
        if "title" in contract.schema:
            return contract.schema["title"]
        # Try metadata title
        if "title" in contract.metadata:
            return contract.metadata["title"]
        # Try schema $id
        if "$id" in contract.schema:
            return contract.schema["$id"]
        return "Data Contract Documentation"

    def _build_field_row(
        self, field_name: str, field_def: Dict[str, Any], is_required: bool
    ) -> List[str]:
        """Build a table row for a schema field."""
        # Type
        field_type = self._get_field_type(field_def)

        # Required badge
        required_str = "Yes" if is_required else "No"

        # Description
        description = field_def.get("description", "")

        # Constraints
        constraints = self._get_field_constraints(field_def)

        return [f"`{field_name}`", field_type, required_str, description, constraints]

    def _get_field_type(self, field_def: Dict[str, Any]) -> str:
        """Extract field type from definition."""
        if "type" in field_def:
            base_type = field_def["type"]
            if base_type == "array" and "items" in field_def:
                items_type = self._get_field_type(field_def["items"])
                return f"array[{items_type}]"
            return base_type
        if "anyOf" in field_def:
            types = [self._get_field_type(t) for t in field_def["anyOf"]]
            return " | ".join(types)
        if "oneOf" in field_def:
            types = [self._get_field_type(t) for t in field_def["oneOf"]]
            return " | ".join(types)
        if "$ref" in field_def:
            return f"ref: {field_def['$ref']}"
        return "any"

    def _get_field_constraints(self, field_def: Dict[str, Any]) -> str:
        """Extract constraints from field definition."""
        constraints = []

        # String constraints
        if "minLength" in field_def:
            constraints.append(f"minLength: {field_def['minLength']}")
        if "maxLength" in field_def:
            constraints.append(f"maxLength: {field_def['maxLength']}")
        if "pattern" in field_def:
            constraints.append(f"pattern: `{field_def['pattern']}`")
        if "format" in field_def:
            constraints.append(f"format: {field_def['format']}")

        # Number constraints
        if "minimum" in field_def:
            constraints.append(f"min: {field_def['minimum']}")
        if "maximum" in field_def:
            constraints.append(f"max: {field_def['maximum']}")
        if "exclusiveMinimum" in field_def:
            constraints.append(f"exclusiveMin: {field_def['exclusiveMinimum']}")
        if "exclusiveMaximum" in field_def:
            constraints.append(f"exclusiveMax: {field_def['exclusiveMaximum']}")
        if "multipleOf" in field_def:
            constraints.append(f"multipleOf: {field_def['multipleOf']}")

        # Enum
        if "enum" in field_def:
            enum_vals = ", ".join(str(v) for v in field_def["enum"][:5])
            if len(field_def["enum"]) > 5:
                enum_vals += "..."
            constraints.append(f"enum: [{enum_vals}]")

        # Default
        if "default" in field_def:
            constraints.append(f"default: {field_def['default']}")

        return "; ".join(constraints) if constraints else ""

    def _get_coercion_description(self, coercion_name: str) -> str:
        """Get description for built-in coercion types."""
        descriptions = {
            "to_string": "Convert value to string",
            "to_integer": "Convert value to integer",
            "to_float": "Convert value to float",
            "to_number": "Convert value to number",
            "to_boolean": "Convert value to boolean",
            "to_datetime": "Parse value as datetime",
            "to_date": "Parse value as date",
            "trim": "Remove leading/trailing whitespace",
            "lowercase": "Convert to lowercase",
            "uppercase": "Convert to uppercase",
            "strip_html": "Remove HTML tags",
            "normalize_whitespace": "Normalize whitespace characters",
        }
        return descriptions.get(coercion_name, "")

    def _format_config(self, config: Any) -> str:
        """Format validation configuration for display."""
        if config is None:
            return ""
        if isinstance(config, bool):
            return "enabled" if config else "disabled"
        if isinstance(config, (int, float, str)):
            return str(config)
        if isinstance(config, dict):
            parts = [f"{k}={v}" for k, v in config.items()]
            return ", ".join(parts)
        if isinstance(config, list):
            return ", ".join(str(v) for v in config)
        return str(config)

    def _format_ownership(self, ownership: Dict[str, Any]) -> str:
        """Format ownership information."""
        headers = ["Role", "Contact"]
        rows = []

        role_labels = {
            "business_owners": "Business Owners",
            "bu_sme": "Business Unit SME",
            "it_application_owners": "IT Application Owners",
            "it_sme": "IT SME",
            "support_lead": "Support Lead",
            "owner": "Owner",
            "team": "Team",
        }

        for key, value in ownership.items():
            label = role_labels.get(key, key.replace("_", " ").title())
            if isinstance(value, list):
                value_str = ", ".join(str(v) for v in value)
            else:
                value_str = str(value)
            rows.append([label, value_str])

        return self.renderer.render_table(headers, rows)

    def _format_governance(self, governance: Dict[str, Any]) -> str:
        """Format governance rules."""
        headers = ["Rule", "Configuration"]
        rows = []

        for rule, config in governance.items():
            rule_label = rule.replace("_", " ").title()
            config_str = self._format_config(config)
            rows.append([rule_label, config_str])

        return self.renderer.render_table(headers, rows)

    def _format_versions(self, versions: Dict[str, str]) -> str:
        """Format version information."""
        headers = ["Component", "Version"]
        rows = [[comp.replace("_", " ").title(), ver] for comp, ver in versions.items()]
        return self.renderer.render_table(headers, rows)

    def _format_metadata_dict(self, metadata: Dict[str, Any]) -> str:
        """Format a metadata dictionary."""
        headers = ["Property", "Value"]
        rows = []
        for key, value in metadata.items():
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, indent=2)
            else:
                value_str = str(value)
            rows.append([key.replace("_", " ").title(), value_str])
        return self.renderer.render_table(headers, rows)


def generate_docs(
    contract: Union[ContractMetadata, Dict[str, Any]],
    format: str = "markdown",
    **kwargs,
) -> str:
    """
    Convenience function to generate documentation from a contract.

    Args:
        contract: ContractMetadata object or contract dictionary
        format: Output format ('markdown' or 'html')
        **kwargs: Additional options passed to DocsGenerator.generate()

    Returns:
        Generated documentation as string

    Example:
        >>> from pycharter import parse_contract_file
        >>> from pycharter.docs_generator import generate_docs
        >>>
        >>> contract = parse_contract_file("contract.yaml")
        >>> markdown = generate_docs(contract)
        >>> html = generate_docs(contract, format="html")
    """
    from pycharter.docs_generator.renderers import HTMLRenderer, MarkdownRenderer

    # Convert dict to ContractMetadata if needed
    if isinstance(contract, dict):
        from pycharter.contract_parser import parse_contract

        contract = parse_contract(contract, validate=False)

    # Select renderer
    if format.lower() == "html":
        renderer = HTMLRenderer()
    else:
        renderer = MarkdownRenderer()

    generator = DocsGenerator(renderer=renderer)
    return generator.generate(contract, **kwargs)

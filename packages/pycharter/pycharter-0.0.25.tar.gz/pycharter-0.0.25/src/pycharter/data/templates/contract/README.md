# Data Contract Templates

Templates for creating data contracts with schema, coercion rules, validation rules, and metadata.

## Quick Start

```python
from pycharter import parse_contract, validate_with_contract

# Option 1: Complete contract in one file
contract = {
    "schema": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string", "minLength": 1},
        },
        "required": ["id", "name"]
    },
    "metadata": {"version": "1.0.0"},
    "ownership": {"owner": "data-team"}
}

# Validate data
result = validate_with_contract(contract, {"id": "123", "name": "Alice"})
print(f"Valid: {result.is_valid}")
```

## Template Files

| Template | Description |
|----------|-------------|
| `template_contract.yaml` | Complete contract (schema + rules + metadata) |
| `template_schema.yaml` | JSON Schema with PyCharter extensions |
| `template_coercion_rules.yaml` | Data type transformation rules |
| `template_validation_rules.yaml` | Business validation rules |
| `template_metadata.yaml` | Ownership and governance metadata |

## Contract Structure

```yaml
# Complete contract structure
schema:               # JSON Schema with PyCharter extensions
  type: object
  properties:
    field_name:
      type: string
      coercion: coerce_to_string      # PyCharter: coercion rule
      validations:                     # PyCharter: validation rules
        max_length: {threshold: 100}

metadata:             # Version and description
  version: "1.0.0"
  description: "Contract description"

ownership:            # Ownership information
  owner: team-name
  team: department

governance_rules:     # Governance policies
  data_retention: {days: 365}
  pii_fields: {fields: [email]}
```

## Coercion Rules

Applied BEFORE Pydantic validation to transform input data:

| Rule | Description |
|------|-------------|
| `coerce_to_string` | Convert to string |
| `coerce_to_integer` | Convert to int |
| `coerce_to_float` | Convert to float |
| `coerce_to_boolean` | Convert to bool |
| `coerce_to_datetime` | Parse datetime |
| `coerce_to_date` | Parse date |
| `coerce_to_uuid` | Parse UUID |
| `coerce_to_lowercase` | Lowercase string |
| `coerce_to_uppercase` | Uppercase string |
| `coerce_to_stripped_string` | Trim whitespace |
| `coerce_to_nullable_*` | Handle null values |

## Validation Rules

Applied AFTER Pydantic validation for business rules:

| Rule | Parameters | Description |
|------|------------|-------------|
| `min_length` | `{threshold: N}` | Minimum string length |
| `max_length` | `{threshold: N}` | Maximum string length |
| `greater_than_or_equal_to` | `{threshold: N}` | Minimum value |
| `less_than_or_equal_to` | `{threshold: N}` | Maximum value |
| `only_allow` | `{allowed_values: [...]}` | Enum validation |
| `non_empty_string` | `null` | Non-empty string |
| `is_email` | `null` | Email format |
| `is_url` | `null` | URL format |
| `matches_regex` | `{pattern: "..."}` | Regex match |

## Usage Patterns

### 1. Validate with Contract

```python
from pycharter import validate_with_contract

result = validate_with_contract(
    "path/to/contract.yaml",  # or dict
    {"id": "123", "name": "Alice"}
)

if result.is_valid:
    print(f"Data: {result.data}")
else:
    print(f"Errors: {result.errors}")
```

### 2. Build Contract from Artifacts

```python
from pycharter import build_contract

contract = build_contract(
    schema=schema_dict,
    metadata=metadata_dict,
    coercion_rules=coercion_dict,
    validation_rules=validation_dict,
)
```

### 3. Quality Check

```python
from pycharter import QualityCheck

report = QualityCheck().run(
    contract=contract,
    data=records
)
print(f"Score: {report.quality_score.overall_score}/100")
```

## Examples

See `examples/02_contracts.py` and `examples/03_validation.py` for working examples.

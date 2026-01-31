# Data Contract Validation Schemas

This directory contains Pydantic models for validating data contract structure.

## Purpose

The Pydantic models in this directory ensure that all data contracts parsed by `parse_contract()` and `parse_contract_file()` strictly adhere to the database table design.

## Files

- `data_contract.py` - Main Pydantic models for data contract validation
  - `DataContractSchema` - Main model for validating complete contracts
  - `SchemaComponent` - Validates the schema component (required)
  - `MetadataComponent` - Validates metadata component (optional)
  - `OwnershipComponent` - Validates ownership component (optional)
  - `GovernanceRulesComponent` - Validates governance rules (optional)
  - `CoercionRulesComponent` - Validates coercion rules (optional)
  - `ValidationRulesComponent` - Validates validation rules (optional)
  - `VersionsComponent` - Validates version tracking (optional)

## Database Alignment

All models are designed to match the database table structure exactly:

- **Field constraints** (max_length) match database column sizes
- **Required fields** match database NOT NULL constraints
- **Optional fields** match database nullable columns
- **Enum values** match database CHECK constraints
- **Field types** match database column types

## Usage

The models are automatically used by the contract parser:

```python
from pycharter import parse_contract, parse_contract_file

# Validation is enabled by default
contract_metadata = parse_contract_file("contract.yaml")  # Validates automatically

# You can disable validation if needed (not recommended)
contract_metadata = parse_contract_file("contract.yaml", validate=False)
```

## Validation Behavior

- **Valid contracts**: Pass validation and parse successfully
- **Invalid contracts**: Raise `ValueError` with detailed Pydantic error messages
- **Missing required fields**: Validation fails with clear error messages
- **Extra fields**: Rejected (except in flexible components like metadata)

## Model Design Principles

1. **Strict Top-Level**: `DataContractSchema` uses `extra = "forbid"` to prevent unexpected fields
2. **Flexible Components**: Metadata, governance_rules allow `extra = "allow"` for flexible JSON storage
3. **Database Constraints**: All field constraints match database column definitions
4. **Type Safety**: Full Python type hints for IDE support and static analysis

## Updating Models

When the database schema changes:

1. Update the corresponding Pydantic model in `data_contract.py`
2. Update field constraints to match new database columns
3. Add/remove fields as needed
4. Test with existing contracts to ensure backward compatibility
5. Update this README if model structure changes significantly

## Testing

To test the validation models:

```python
from pycharter.db.schemas.data_contract import DataContractSchema

# Valid contract
valid_contract = {
    "schema": {"type": "object", "properties": {"name": {"type": "string"}}}
}
result = DataContractSchema.model_validate(valid_contract)  # ✓ Passes

# Invalid contract (missing required schema)
invalid_contract = {
    "metadata": {"version": "1.0.0"}
}
result = DataContractSchema.model_validate(invalid_contract)  # ✗ Raises ValidationError
```










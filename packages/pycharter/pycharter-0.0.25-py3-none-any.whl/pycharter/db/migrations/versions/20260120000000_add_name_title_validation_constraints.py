"""Add name and title validation constraints

Revision ID: name_title_validation
Revises: 7f8a9b2c3d4e
Create Date: 2026-01-20 00:00:00.000000

Adds CHECK constraints to enforce naming convention:
- Only lowercase alphanumerics and underscores allowed
- Applies to: data_contracts.name, schemas.title, metadata_records.title,
  coercion_rules.title, validation_rules.title, data_feeds.name
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'name_title_validation'
down_revision: Union[str, None] = '7f8a9b2c3d4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Detect database type for schema handling
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'
    schema_name = None if is_sqlite else 'pycharter'
    
    if is_sqlite:
        # SQLite doesn't support adding CHECK constraints to existing tables
        # We skip database-level constraints for SQLite since validation is
        # already enforced at the API and frontend layers
        # This is acceptable because:
        # 1. API validation prevents invalid data from being stored
        # 2. Frontend validation provides immediate user feedback
        # 3. SQLite is typically used for development/testing
        # 4. Production should use PostgreSQL which supports CHECK constraints
        pass
    else:
        # PostgreSQL supports regex in CHECK constraints
        name_pattern_check = "name ~ '^[a-z0-9_]+$'"
        title_pattern_check = "title ~ '^[a-z0-9_]+$'"
        
        # Add CHECK constraints to data_contracts.name
        op.create_check_constraint(
            'ck_data_contracts_name_format',
            'data_contracts',
            name_pattern_check,
            schema=schema_name
        )
        
        # Add CHECK constraints to schemas.title
        op.create_check_constraint(
            'ck_schemas_title_format',
            'schemas',
            title_pattern_check,
            schema=schema_name
        )
        
        # Add CHECK constraints to metadata_records.title
        op.create_check_constraint(
            'ck_metadata_records_title_format',
            'metadata_records',
            title_pattern_check,
            schema=schema_name
        )
        
        # Add CHECK constraints to coercion_rules.title
        op.create_check_constraint(
            'ck_coercion_rules_title_format',
            'coercion_rules',
            title_pattern_check,
            schema=schema_name
        )
        
        # Add CHECK constraints to validation_rules.title
        op.create_check_constraint(
            'ck_validation_rules_title_format',
            'validation_rules',
            title_pattern_check,
            schema=schema_name
        )
        
        # Add CHECK constraints to data_feeds.name
        op.create_check_constraint(
            'ck_data_feeds_name_format',
            'data_feeds',
            name_pattern_check,
            schema=schema_name
        )


def downgrade() -> None:
    # Detect database type for schema handling
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'
    schema_name = None if is_sqlite else 'pycharter'
    
    if not is_sqlite:
        # Drop CHECK constraints (only for PostgreSQL)
        op.drop_constraint('ck_data_feeds_name_format', 'data_feeds', schema=schema_name, type_='check')
        op.drop_constraint('ck_validation_rules_title_format', 'validation_rules', schema=schema_name, type_='check')
        op.drop_constraint('ck_coercion_rules_title_format', 'coercion_rules', schema=schema_name, type_='check')
        op.drop_constraint('ck_metadata_records_title_format', 'metadata_records', schema=schema_name, type_='check')
        op.drop_constraint('ck_schemas_title_format', 'schemas', schema=schema_name, type_='check')
        op.drop_constraint('ck_data_contracts_name_format', 'data_contracts', schema=schema_name, type_='check')

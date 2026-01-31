"""Change artifact unique constraints from (data_contract_id, version) to (title, version)

Revision ID: change_artifact_unique_constraints
Revises: remove_artifact_versions
Create Date: 2026-01-22 00:00:00.000000

Changes unique constraints on artifact tables:
- schemas: from (data_contract_id, version) to (title, version)
- coercion_rules: from (data_contract_id, version) to (title, version)
- validation_rules: from (data_contract_id, version) to (title, version)
- metadata_records: from (data_contract_id, version) to (title, version)

This ensures that artifacts are uniquely identified by their title and version
globally, not per data contract. This allows artifacts to be shared across
different data contracts while maintaining uniqueness.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'change_artifact_unique_constraints'
down_revision: Union[str, None] = 'remove_artifact_versions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Detect database type for schema handling
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'
    schema_name = None if is_sqlite else 'pycharter'
    
    # For SQLite, we need to handle potential duplicate (title, version) pairs
    # by keeping only one record per (title, version) combination
    if is_sqlite:
        # Handle duplicates in schemas - keep the one with the latest created_at
        op.execute(sa.text("""
            DELETE FROM schemas
            WHERE id NOT IN (
                SELECT id FROM (
                    SELECT id, ROW_NUMBER() OVER (PARTITION BY title, version ORDER BY created_at DESC) as rn
                    FROM schemas
                ) WHERE rn = 1
            )
        """))
        
        # Handle duplicates in coercion_rules - keep the one with the latest created_at
        op.execute(sa.text("""
            DELETE FROM coercion_rules
            WHERE id NOT IN (
                SELECT id FROM (
                    SELECT id, ROW_NUMBER() OVER (PARTITION BY title, version ORDER BY created_at DESC) as rn
                    FROM coercion_rules
                ) WHERE rn = 1
            )
        """))
        
        # Handle duplicates in validation_rules - keep the one with the latest created_at
        op.execute(sa.text("""
            DELETE FROM validation_rules
            WHERE id NOT IN (
                SELECT id FROM (
                    SELECT id, ROW_NUMBER() OVER (PARTITION BY title, version ORDER BY created_at DESC) as rn
                    FROM validation_rules
                ) WHERE rn = 1
            )
        """))
        
        # Handle duplicates in metadata_records - keep the one with the latest created_at
        op.execute(sa.text("""
            DELETE FROM metadata_records
            WHERE id NOT IN (
                SELECT id FROM (
                    SELECT id, ROW_NUMBER() OVER (PARTITION BY title, version ORDER BY created_at DESC) as rn
                    FROM metadata_records
                ) WHERE rn = 1
            )
        """))
        
        # Now apply the constraint changes using batch mode
        with op.batch_alter_table('schemas', schema=None) as batch_op:
            batch_op.drop_constraint('uq_schemas_contract_version', type_='unique')
            batch_op.create_unique_constraint('uq_schemas_title_version', ['title', 'version'])
        
        with op.batch_alter_table('coercion_rules', schema=None) as batch_op:
            batch_op.drop_constraint('uq_coercion_rules_contract_version', type_='unique')
            batch_op.create_unique_constraint('uq_coercion_rules_title_version', ['title', 'version'])
        
        with op.batch_alter_table('validation_rules', schema=None) as batch_op:
            batch_op.drop_constraint('uq_validation_rules_contract_version', type_='unique')
            batch_op.create_unique_constraint('uq_validation_rules_title_version', ['title', 'version'])
        
        with op.batch_alter_table('metadata_records', schema=None) as batch_op:
            batch_op.drop_constraint('uq_metadata_records_contract_version', type_='unique')
            batch_op.create_unique_constraint('uq_metadata_records_title_version', ['title', 'version'])
    else:
        # PostgreSQL and other databases support ALTER TABLE directly
        # Drop old unique constraints and add new ones
        # schemas table
        op.drop_constraint('uq_schemas_contract_version', 'schemas', schema=schema_name, type_='unique')
        op.create_unique_constraint('uq_schemas_title_version', 'schemas', ['title', 'version'], schema=schema_name)
        
        # coercion_rules table
        op.drop_constraint('uq_coercion_rules_contract_version', 'coercion_rules', schema=schema_name, type_='unique')
        op.create_unique_constraint('uq_coercion_rules_title_version', 'coercion_rules', ['title', 'version'], schema=schema_name)
        
        # validation_rules table
        op.drop_constraint('uq_validation_rules_contract_version', 'validation_rules', schema=schema_name, type_='unique')
        op.create_unique_constraint('uq_validation_rules_title_version', 'validation_rules', ['title', 'version'], schema=schema_name)
        
        # metadata_records table
        op.drop_constraint('uq_metadata_records_contract_version', 'metadata_records', schema=schema_name, type_='unique')
        op.create_unique_constraint('uq_metadata_records_title_version', 'metadata_records', ['title', 'version'], schema=schema_name)


def downgrade() -> None:
    # Detect database type for schema handling
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'
    schema_name = None if is_sqlite else 'pycharter'
    
    if is_sqlite:
        # SQLite doesn't support ALTER TABLE for constraints, use batch mode
        with op.batch_alter_table('schemas', schema=None) as batch_op:
            batch_op.drop_constraint('uq_schemas_title_version', type_='unique')
            batch_op.create_unique_constraint('uq_schemas_contract_version', ['data_contract_id', 'version'])
        
        with op.batch_alter_table('coercion_rules', schema=None) as batch_op:
            batch_op.drop_constraint('uq_coercion_rules_title_version', type_='unique')
            batch_op.create_unique_constraint('uq_coercion_rules_contract_version', ['data_contract_id', 'version'])
        
        with op.batch_alter_table('validation_rules', schema=None) as batch_op:
            batch_op.drop_constraint('uq_validation_rules_title_version', type_='unique')
            batch_op.create_unique_constraint('uq_validation_rules_contract_version', ['data_contract_id', 'version'])
        
        with op.batch_alter_table('metadata_records', schema=None) as batch_op:
            batch_op.drop_constraint('uq_metadata_records_title_version', type_='unique')
            batch_op.create_unique_constraint('uq_metadata_records_contract_version', ['data_contract_id', 'version'])
    else:
        # PostgreSQL and other databases support ALTER TABLE directly
        # Revert to old unique constraints
        # schemas table
        op.drop_constraint('uq_schemas_title_version', 'schemas', schema=schema_name, type_='unique')
        op.create_unique_constraint('uq_schemas_contract_version', 'schemas', ['data_contract_id', 'version'], schema=schema_name)
        
        # coercion_rules table
        op.drop_constraint('uq_coercion_rules_title_version', 'coercion_rules', schema=schema_name, type_='unique')
        op.create_unique_constraint('uq_coercion_rules_contract_version', 'coercion_rules', ['data_contract_id', 'version'], schema=schema_name)
        
        # validation_rules table
        op.drop_constraint('uq_validation_rules_title_version', 'validation_rules', schema=schema_name, type_='unique')
        op.create_unique_constraint('uq_validation_rules_contract_version', 'validation_rules', ['data_contract_id', 'version'], schema=schema_name)
        
        # metadata_records table
        op.drop_constraint('uq_metadata_records_title_version', 'metadata_records', schema=schema_name, type_='unique')
        op.create_unique_constraint('uq_metadata_records_contract_version', 'metadata_records', ['data_contract_id', 'version'], schema=schema_name)

"""Remove artifact version columns from data_contracts table

Revision ID: remove_artifact_versions
Revises: name_title_validation
Create Date: 2026-01-21 00:00:00.000000

Removes version tracking columns from data_contracts table:
- schema_version
- coercion_rules_version
- validation_rules_version
- metadata_version

These columns are redundant since artifacts are referenced by UUID,
and each artifact (schemas, coercion_rules, validation_rules, metadata_records)
already has its own version field. The data_contract.version field
represents the contract version, which is independent of artifact versions.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'remove_artifact_versions'
down_revision: Union[str, None] = 'name_title_validation'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Detect database type for schema handling
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'
    schema_name = None if is_sqlite else 'pycharter'
    
    # Drop version columns from data_contracts table
    op.drop_column('data_contracts', 'schema_version', schema=schema_name)
    op.drop_column('data_contracts', 'coercion_rules_version', schema=schema_name)
    op.drop_column('data_contracts', 'validation_rules_version', schema=schema_name)
    op.drop_column('data_contracts', 'metadata_version', schema=schema_name)


def downgrade() -> None:
    # Detect database type for schema handling
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'
    schema_name = None if is_sqlite else 'pycharter'
    
    # Re-add version columns (nullable since we can't restore the original values)
    op.add_column('data_contracts', 
        sa.Column('schema_version', sa.String(length=50), nullable=True),
        schema=schema_name
    )
    op.add_column('data_contracts',
        sa.Column('coercion_rules_version', sa.String(length=50), nullable=True),
        schema=schema_name
    )
    op.add_column('data_contracts',
        sa.Column('validation_rules_version', sa.String(length=50), nullable=True),
        schema=schema_name
    )
    op.add_column('data_contracts',
        sa.Column('metadata_version', sa.String(length=50), nullable=True),
        schema=schema_name
    )

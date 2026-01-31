"""Add Tier 2 and Tier 3 metadata entities

Revision ID: 7f8a9b2c3d4e
Revises: a1b2c3d4e5f6
Create Date: 2025-01-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# For SQLite compatibility, use sa.UUID() instead of postgresql.UUID()
# SQLite will store UUIDs as strings

# revision identifiers, used by Alembic.
revision: str = '7f8a9b2c3d4e'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Detect database type for schema handling
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'
    schema_name = None if is_sqlite else 'pycharter'
    
    # Use UUID type (SQLite will store as text, but we use UUID type for consistency)
    uuid_type = sa.UUID()
    
    # Use appropriate datetime default for SQLite vs PostgreSQL
    if is_sqlite:
        datetime_default = None  # SQLite doesn't support now() function
    else:
        datetime_default = sa.text('now()')
    
    # Create data_dependencies table
    op.create_table(
        'data_dependencies',
        sa.Column('id', uuid_type, nullable=False),
        sa.Column('source_contract_id', uuid_type, nullable=False),
        sa.Column('target_contract_id', uuid_type, nullable=False),
        sa.Column('dependency_type', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_critical', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['source_contract_id'], [f'{schema_name + "." if schema_name else ""}data_contracts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_contract_id'], [f'{schema_name + "." if schema_name else ""}data_contracts.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('source_contract_id', 'target_contract_id', name='uq_data_dependencies_source_target'),
        schema=schema_name
    )

    # Create environments table
    op.create_table(
        'environments',
        sa.Column('id', uuid_type, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('environment_type', sa.String(length=50), nullable=True),
        sa.Column('is_production', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('additional_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_environments_name'),
        schema=schema_name
    )

    # Create data_feeds table
    op.create_table(
        'data_feeds',
        sa.Column('id', uuid_type, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('feed_type', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('additional_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_data_feeds_name'),
        schema=schema_name
    )

    # Create storage_locations table
    op.create_table(
        'storage_locations',
        sa.Column('id', uuid_type, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('location_type', sa.String(length=50), nullable=True),
        sa.Column('cluster', sa.String(length=255), nullable=True),
        sa.Column('database', sa.String(length=255), nullable=True),
        sa.Column('collection', sa.String(length=255), nullable=True),
        sa.Column('schema_name', sa.String(length=255), nullable=True),
        sa.Column('table_name', sa.String(length=255), nullable=True),
        sa.Column('connection_string', sa.Text(), nullable=True),
        sa.Column('system_id', uuid_type, nullable=True),
        sa.Column('environment_id', uuid_type, nullable=True),
        sa.Column('additional_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['system_id'], [f'{schema_name + "." if schema_name else ""}systems.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['environment_id'], [f'{schema_name + "." if schema_name else ""}environments.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('name', name='uq_storage_locations_name'),
        schema=schema_name
    )

    # Create compliance_frameworks table
    op.create_table(
        'compliance_frameworks',
        sa.Column('id', uuid_type, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('framework_type', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('additional_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_compliance_frameworks_name'),
        sa.UniqueConstraint('code', name='uq_compliance_frameworks_code'),
        schema=schema_name
    )

    # Create tags table
    op.create_table(
        'tags',
        sa.Column('id', uuid_type, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('additional_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_tags_name'),
        schema=schema_name
    )

    # Create api_endpoints table
    op.create_table(
        'api_endpoints',
        sa.Column('id', uuid_type, nullable=False),
        sa.Column('path', sa.String(length=500), nullable=False),
        sa.Column('method', sa.String(length=10), nullable=False),
        sa.Column('metadata_record_id', uuid_type, nullable=False),
        sa.Column('rate_limit', sa.String(length=50), nullable=True),
        sa.Column('cache_ttl', sa.Integer(), nullable=True),
        sa.Column('documentation_url', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('additional_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['metadata_record_id'], [f'{schema_name + "." if schema_name else ""}metadata_records.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('path', 'method', 'metadata_record_id', name='uq_api_endpoints'),
        schema=schema_name
    )

    # Create join tables
    op.create_table(
        'metadata_record_environments',
        sa.Column('id', uuid_type, nullable=False),
        sa.Column('metadata_record_id', uuid_type, nullable=False),
        sa.Column('environment_id', uuid_type, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['environment_id'], [f'{schema_name + "." if schema_name else ""}environments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['metadata_record_id'], [f'{schema_name + "." if schema_name else ""}metadata_records.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('metadata_record_id', 'environment_id', name='uq_mr_environment'),
        schema=schema_name
    )

    op.create_table(
        'metadata_record_data_feeds',
        sa.Column('id', uuid_type, nullable=False),
        sa.Column('metadata_record_id', uuid_type, nullable=False),
        sa.Column('data_feed_id', uuid_type, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['data_feed_id'], [f'{schema_name + "." if schema_name else ""}data_feeds.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['metadata_record_id'], [f'{schema_name + "." if schema_name else ""}metadata_records.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('metadata_record_id', 'data_feed_id', name='uq_mr_data_feed'),
        schema=schema_name
    )

    op.create_table(
        'metadata_record_storage_locations',
        sa.Column('id', uuid_type, nullable=False),
        sa.Column('metadata_record_id', uuid_type, nullable=False),
        sa.Column('storage_location_id', uuid_type, nullable=False),
        sa.Column('usage_type', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['metadata_record_id'], [f'{schema_name + "." if schema_name else ""}metadata_records.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['storage_location_id'], [f'{schema_name + "." if schema_name else ""}storage_locations.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('metadata_record_id', 'storage_location_id', name='uq_mr_storage_location'),
        schema=schema_name
    )

    op.create_table(
        'metadata_record_compliance_frameworks',
        sa.Column('id', uuid_type, nullable=False),
        sa.Column('metadata_record_id', uuid_type, nullable=False),
        sa.Column('compliance_framework_id', uuid_type, nullable=False),
        sa.Column('compliance_status', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['compliance_framework_id'], [f'{schema_name + "." if schema_name else ""}compliance_frameworks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['metadata_record_id'], [f'{schema_name + "." if schema_name else ""}metadata_records.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('metadata_record_id', 'compliance_framework_id', name='uq_mr_compliance'),
        schema=schema_name
    )

    op.create_table(
        'data_contract_tags',
        sa.Column('id', uuid_type, nullable=False),
        sa.Column('data_contract_id', uuid_type, nullable=False),
        sa.Column('tag_id', uuid_type, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=datetime_default, nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['data_contract_id'], [f'{schema_name + "." if schema_name else ""}data_contracts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], [f'{schema_name + "." if schema_name else ""}tags.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('data_contract_id', 'tag_id', name='uq_dc_tag'),
        schema=schema_name
    )


def downgrade() -> None:
    # Detect database type for schema handling
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'
    schema_name = None if is_sqlite else 'pycharter'
    
    # Drop join tables first
    op.drop_table('data_contract_tags', schema=schema_name)
    op.drop_table('metadata_record_compliance_frameworks', schema=schema_name)
    op.drop_table('metadata_record_storage_locations', schema=schema_name)
    op.drop_table('metadata_record_data_feeds', schema=schema_name)
    op.drop_table('metadata_record_environments', schema=schema_name)
    
    # Drop main tables
    op.drop_table('api_endpoints', schema=schema_name)
    op.drop_table('tags', schema=schema_name)
    op.drop_table('compliance_frameworks', schema=schema_name)
    op.drop_table('storage_locations', schema=schema_name)
    op.drop_table('data_feeds', schema=schema_name)
    op.drop_table('environments', schema=schema_name)
    op.drop_table('data_dependencies', schema=schema_name)

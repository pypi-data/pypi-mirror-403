"""Add dead_letter_queue table

Revision ID: a1b2c3d4e5f6
Revises: 8b08d78068e3
Create Date: 2026-01-10 08:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '8b08d78068e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create dead_letter_queue table in pycharter schema
    op.create_table(
        'dead_letter_queue',
        sa.Column('id', sa.String(length=16), nullable=False),
        sa.Column('pipeline_name', sa.String(length=255), nullable=False),
        sa.Column('record_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('reason', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('error_type', sa.String(length=100), nullable=False),
        sa.Column('stage', sa.String(length=20), nullable=False),
        sa.Column('additional_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='pycharter'
    )
    
    # Create indexes
    op.create_index(
        'ix_pycharter_dead_letter_queue_pipeline_name',
        'dead_letter_queue',
        ['pipeline_name'],
        schema='pycharter'
    )
    op.create_index(
        'ix_pycharter_dead_letter_queue_reason',
        'dead_letter_queue',
        ['reason'],
        schema='pycharter'
    )
    op.create_index(
        'ix_pycharter_dead_letter_queue_error_type',
        'dead_letter_queue',
        ['error_type'],
        schema='pycharter'
    )
    op.create_index(
        'ix_pycharter_dead_letter_queue_stage',
        'dead_letter_queue',
        ['stage'],
        schema='pycharter'
    )
    op.create_index(
        'ix_pycharter_dead_letter_queue_status',
        'dead_letter_queue',
        ['status'],
        schema='pycharter'
    )
    op.create_index(
        'ix_pycharter_dead_letter_queue_timestamp',
        'dead_letter_queue',
        ['timestamp'],
        schema='pycharter'
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_pycharter_dead_letter_queue_timestamp', table_name='dead_letter_queue', schema='pycharter')
    op.drop_index('ix_pycharter_dead_letter_queue_status', table_name='dead_letter_queue', schema='pycharter')
    op.drop_index('ix_pycharter_dead_letter_queue_stage', table_name='dead_letter_queue', schema='pycharter')
    op.drop_index('ix_pycharter_dead_letter_queue_error_type', table_name='dead_letter_queue', schema='pycharter')
    op.drop_index('ix_pycharter_dead_letter_queue_reason', table_name='dead_letter_queue', schema='pycharter')
    op.drop_index('ix_pycharter_dead_letter_queue_pipeline_name', table_name='dead_letter_queue', schema='pycharter')
    
    # Drop table
    op.drop_table('dead_letter_queue', schema='pycharter')


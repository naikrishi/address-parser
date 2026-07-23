"""add enrichment and geocode results

Revision ID: 5d6a6d3f9c12
Revises: d23a9abb64c2
Create Date: 2026-07-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d6a6d3f9c12'
down_revision: Union[str, Sequence[str], None] = 'd23a9abb64c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'enrichment_result',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('parse_result_id', sa.UUID(), nullable=False),
        sa.Column('provider_name', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('enriched_components', sa.JSON(), nullable=False),
        sa.Column('is_complete', sa.Boolean(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['parse_result_id'], ['parse_result.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_enrichment_result_created_at'), 'enrichment_result', ['created_at'], unique=False)
    op.create_index(op.f('ix_enrichment_result_parse_result_id'), 'enrichment_result', ['parse_result_id'], unique=False)
    op.create_index(op.f('ix_enrichment_result_status'), 'enrichment_result', ['status'], unique=False)

    op.create_table(
        'geocode_result',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('parse_result_id', sa.UUID(), nullable=False),
        sa.Column('enrichment_result_id', sa.UUID(), nullable=True),
        sa.Column('provider_name', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('result_payload', sa.JSON(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['enrichment_result_id'], ['enrichment_result.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parse_result_id'], ['parse_result.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_geocode_result_created_at'), 'geocode_result', ['created_at'], unique=False)
    op.create_index(op.f('ix_geocode_result_enrichment_result_id'), 'geocode_result', ['enrichment_result_id'], unique=False)
    op.create_index(op.f('ix_geocode_result_parse_result_id'), 'geocode_result', ['parse_result_id'], unique=False)
    op.create_index(op.f('ix_geocode_result_status'), 'geocode_result', ['status'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_geocode_result_status'), table_name='geocode_result')
    op.drop_index(op.f('ix_geocode_result_parse_result_id'), table_name='geocode_result')
    op.drop_index(op.f('ix_geocode_result_enrichment_result_id'), table_name='geocode_result')
    op.drop_index(op.f('ix_geocode_result_created_at'), table_name='geocode_result')
    op.drop_table('geocode_result')

    op.drop_index(op.f('ix_enrichment_result_status'), table_name='enrichment_result')
    op.drop_index(op.f('ix_enrichment_result_parse_result_id'), table_name='enrichment_result')
    op.drop_index(op.f('ix_enrichment_result_created_at'), table_name='enrichment_result')
    op.drop_table('enrichment_result')
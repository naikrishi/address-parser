"""Day 9+10: pgvector extension, embedding column, enrichment/geocode telemetry fields

Revision ID: a1b2c3d4e5f6
Revises: 5d6a6d3f9c12
Create Date: 2026-08-03

"""
from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "5d6a6d3f9c12"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # pgvector extension must exist before the vector column can be added
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Day 9: embedding column on parse_result (nullable for safe backfill)
    op.add_column(
        "parse_result",
        sa.Column("embedding", sa.Text(), nullable=True),  # stored as text; pgvector handles cast
    )
    # Replace with native vector type via raw SQL so we don't need the pgvector SA type at migration time
    op.execute("ALTER TABLE parse_result ALTER COLUMN embedding TYPE vector(384) USING NULL")

    # Day 10: enrichment_result telemetry columns
    op.add_column("enrichment_result", sa.Column("confidence_label", sa.String(10), nullable=True))
    op.add_column("enrichment_result", sa.Column("prompt_tokens", sa.Integer(), nullable=True))
    op.add_column("enrichment_result", sa.Column("completion_tokens", sa.Integer(), nullable=True))
    op.add_column("enrichment_result", sa.Column("estimated_cost", sa.Float(), nullable=True))
    op.add_column("enrichment_result", sa.Column("llm_summary", sa.Text(), nullable=True))

    # Day 10: geocode_result telemetry columns
    op.add_column("geocode_result", sa.Column("prompt_tokens", sa.Integer(), nullable=True))
    op.add_column("geocode_result", sa.Column("completion_tokens", sa.Integer(), nullable=True))
    op.add_column("geocode_result", sa.Column("estimated_cost", sa.Float(), nullable=True))

    # Indexes for common telemetry filters
    op.create_index("ix_enrichment_result_confidence_label", "enrichment_result", ["confidence_label"])
    op.create_index("ix_enrichment_result_estimated_cost", "enrichment_result", ["estimated_cost"])
    op.create_index("ix_geocode_result_estimated_cost", "geocode_result", ["estimated_cost"])


def downgrade() -> None:
    op.drop_index("ix_geocode_result_estimated_cost", table_name="geocode_result")
    op.drop_index("ix_enrichment_result_estimated_cost", table_name="enrichment_result")
    op.drop_index("ix_enrichment_result_confidence_label", table_name="enrichment_result")

    op.drop_column("geocode_result", "estimated_cost")
    op.drop_column("geocode_result", "completion_tokens")
    op.drop_column("geocode_result", "prompt_tokens")

    op.drop_column("enrichment_result", "llm_summary")
    op.drop_column("enrichment_result", "estimated_cost")
    op.drop_column("enrichment_result", "completion_tokens")
    op.drop_column("enrichment_result", "prompt_tokens")
    op.drop_column("enrichment_result", "confidence_label")

    op.drop_column("parse_result", "embedding")

"""add user account table

Revision ID: f1e2d3c4b5a6
Revises: a1b2c3d4e5f6
Create Date: 2026-08-05 17:35:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "f1e2d3c4b5a6"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


user_role = postgresql.ENUM("ops", "admin", name="user_role", create_type=False)


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE user_role AS ENUM ('ops', 'admin');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END
        $$;
        """
    )

    op.create_table(
        "user_account",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False, server_default="ops"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_account_email"), "user_account", ["email"], unique=True)
    op.create_index(op.f("ix_user_account_username"), "user_account", ["username"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_account_username"), table_name="user_account")
    op.drop_index(op.f("ix_user_account_email"), table_name="user_account")
    op.drop_table("user_account")
    user_role.drop(op.get_bind(), checkfirst=True)

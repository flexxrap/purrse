"""create_categories

Revision ID: 6a21e573
Revises: 6a21e196
Create Date: 2026-06-04
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "6a21e573"
down_revision = "6a21e196"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("color", sa.String(7), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("char_length(name) <= 64", name="categories_name_length"),
        sa.CheckConstraint(
            "color ~ '^#[0-9A-Fa-f]{6}$'", name="categories_color_format"
        ),
        sa.CheckConstraint(
            "type IN ('income', 'expense')", name="categories_type_values"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_categories_user_id", "categories", ["user_id"])


def downgrade() -> None:
    op.drop_index("idx_categories_user_id", table_name="categories")
    op.drop_table("categories")

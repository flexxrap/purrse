"""create_goals

Revision ID: 6a21eb2c
Revises: 6a21e7b5
Create Date: 2026-06-05
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "6a21eb2c"
down_revision = "6a21e7b5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "goals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("target_cents", sa.Integer(), nullable=False),
        sa.Column("current_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("char_length(name) <= 128", name="goals_name_length"),
        sa.CheckConstraint("target_cents > 0", name="goals_target_positive"),
        sa.CheckConstraint("current_cents >= 0", name="goals_current_non_negative"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_goals_user_id", "goals", ["user_id"])


def downgrade() -> None:
    op.drop_index("idx_goals_user_id", table_name="goals")
    op.drop_table("goals")

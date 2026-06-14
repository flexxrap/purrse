"""create_budgets

Revision ID: 7b30f002
Revises: 7b30f001
Create Date: 2026-06-11

D-04: budget limits per category per month.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "7b30f002"
down_revision = "7b30f001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "budgets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("month", sa.String(7), nullable=False),
        sa.Column("limit_cents", sa.Integer, nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("limit_cents > 0", name="budgets_limit_positive"),
        sa.CheckConstraint("month ~ '^[0-9]{4}-[0-9]{2}$'", name="budgets_month_format"),
        sa.UniqueConstraint("user_id", "category_id", "month", name="uq_budgets_user_category_month"),
    )
    op.create_index("idx_budgets_user_month", "budgets", ["user_id", "month"])


def downgrade() -> None:
    op.drop_index("idx_budgets_user_month")
    op.drop_table("budgets")

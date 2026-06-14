"""create_recurring_transactions

Revision ID: 7b30f005
Revises: 7b30f004
Create Date: 2026-06-12

T-10: recurring transactions (weekly/monthly/yearly).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "7b30f005"
down_revision = "7b30f004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recurring_transactions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("amount_cents", sa.Integer, nullable=False),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("frequency", sa.String(10), nullable=False),
        sa.Column("next_date", sa.Date, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("amount_cents > 0", name="recurring_amount_positive"),
        sa.CheckConstraint("frequency IN ('weekly', 'monthly', 'yearly')", name="recurring_frequency_valid"),
    )
    op.create_index("idx_recurring_user_id", "recurring_transactions", ["user_id"])
    op.create_index("idx_recurring_next_date", "recurring_transactions", ["next_date"], postgresql_where=sa.text("is_active = true"))


def downgrade() -> None:
    op.drop_index("idx_recurring_next_date")
    op.drop_index("idx_recurring_user_id")
    op.drop_table("recurring_transactions")

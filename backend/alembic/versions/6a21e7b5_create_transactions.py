"""create_transactions

Revision ID: 6a21e7b5
Revises: 6a21e573
Create Date: 2026-06-05
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "6a21e7b5"
down_revision = "6a21e573"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("tx_date", sa.Date(), nullable=False),
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
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint("amount_cents > 0", name="transactions_amount_positive"),
        sa.CheckConstraint("char_length(note) <= 500", name="transactions_note_length"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_transactions_user_id", "transactions", ["user_id"])
    op.create_index(
        "idx_transactions_tx_date", "transactions", ["tx_date"],
        postgresql_ops={"tx_date": "DESC"},
    )
    op.create_index(
        "idx_transactions_user_date",
        "transactions",
        ["user_id", "tx_date"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("idx_transactions_user_date", table_name="transactions")
    op.drop_index("idx_transactions_tx_date", table_name="transactions")
    op.drop_index("idx_transactions_user_id", table_name="transactions")
    op.drop_table("transactions")

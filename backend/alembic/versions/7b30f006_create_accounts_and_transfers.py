"""create_accounts_and_transfers

Revision ID: 7b30f006
Revises: 7b30f005
Create Date: 2026-06-14

T-11: multiple accounts/wallets per user, transfers between accounts.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "7b30f006"
down_revision = "7b30f005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("type", sa.Text, nullable=False),
        sa.Column("initial_balance_cents", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_archived", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("char_length(name) <= 64", name="accounts_name_length"),
        sa.CheckConstraint("type IN ('cash', 'card', 'savings', 'other')", name="accounts_type_values"),
    )
    op.create_index("idx_accounts_user_id", "accounts", ["user_id"])

    op.create_table(
        "transfers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_account_id", UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("to_account_id", UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("amount_cents", sa.Integer, nullable=False),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("tx_date", sa.Date, nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("amount_cents > 0", name="transfers_amount_positive"),
        sa.CheckConstraint("char_length(note) <= 500", name="transfers_note_length"),
        sa.CheckConstraint("from_account_id != to_account_id", name="transfers_different_accounts"),
    )
    op.create_index("idx_transfers_user_id", "transfers", ["user_id"])
    op.create_index("idx_transfers_from_account", "transfers", ["from_account_id"])
    op.create_index("idx_transfers_to_account", "transfers", ["to_account_id"])

    # --- account_id on transactions & recurring_transactions ---
    op.add_column("transactions", sa.Column("account_id", UUID(as_uuid=True), nullable=True))
    op.add_column("recurring_transactions", sa.Column("account_id", UUID(as_uuid=True), nullable=True))

    # One default "Main" cash account per existing user, then backfill account_id
    op.execute(
        """
        INSERT INTO accounts (id, user_id, name, type, initial_balance_cents, is_archived, created_at, updated_at)
        SELECT gen_random_uuid(), id, 'Main', 'cash', 0, false, now(), now()
        FROM users
        """
    )
    op.execute(
        """
        UPDATE transactions t
        SET account_id = a.id
        FROM accounts a
        WHERE a.user_id = t.user_id AND t.account_id IS NULL
        """
    )
    op.execute(
        """
        UPDATE recurring_transactions r
        SET account_id = a.id
        FROM accounts a
        WHERE a.user_id = r.user_id AND r.account_id IS NULL
        """
    )

    op.alter_column("transactions", "account_id", nullable=False)
    op.alter_column("recurring_transactions", "account_id", nullable=False)

    op.create_foreign_key(
        "fk_transactions_account_id", "transactions", "accounts", ["account_id"], ["id"], ondelete="RESTRICT"
    )
    op.create_foreign_key(
        "fk_recurring_account_id", "recurring_transactions", "accounts", ["account_id"], ["id"], ondelete="RESTRICT"
    )
    op.create_index("idx_transactions_account_id", "transactions", ["account_id"])
    op.create_index("idx_recurring_account_id", "recurring_transactions", ["account_id"])


def downgrade() -> None:
    op.drop_index("idx_recurring_account_id", table_name="recurring_transactions")
    op.drop_index("idx_transactions_account_id", table_name="transactions")
    op.drop_constraint("fk_recurring_account_id", "recurring_transactions", type_="foreignkey")
    op.drop_constraint("fk_transactions_account_id", "transactions", type_="foreignkey")
    op.drop_column("recurring_transactions", "account_id")
    op.drop_column("transactions", "account_id")

    op.drop_index("idx_transfers_to_account", table_name="transfers")
    op.drop_index("idx_transfers_from_account", table_name="transfers")
    op.drop_index("idx_transfers_user_id", table_name="transfers")
    op.drop_table("transfers")

    op.drop_index("idx_accounts_user_id", table_name="accounts")
    op.drop_table("accounts")

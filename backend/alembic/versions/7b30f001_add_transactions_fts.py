"""add_transactions_fts

Revision ID: 7b30f001
Revises: 6a21eb2c
Create Date: 2026-06-10

Adds note_tsv generated tsvector column and GIN index for T-07 full-text search.
"""

from alembic import op

revision = "7b30f001"
down_revision = "6a21eb2c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE transactions
        ADD COLUMN note_tsv TSVECTOR
        GENERATED ALWAYS AS (to_tsvector('simple', coalesce(note, ''))) STORED
    """)
    op.execute("""
        CREATE INDEX idx_transactions_note_fts
        ON transactions USING GIN(note_tsv)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_transactions_note_fts")
    op.execute("ALTER TABLE transactions DROP COLUMN IF EXISTS note_tsv")

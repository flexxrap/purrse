"""fix refresh_token expires_at to TIMESTAMPTZ

Revision ID: 7b30f004
Revises: 7b30f003
Create Date: 2026-06-11

TIMESTAMP WITHOUT TIME ZONE caused DataError when inserting timezone-aware
datetimes from Python (datetime.now(timezone.utc)). Changing to TIMESTAMPTZ
so PostgreSQL stores and returns UTC-aware values correctly.
"""

from alembic import op
import sqlalchemy as sa

revision = "7b30f004"
down_revision = "7b30f003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "refresh_tokens",
        "expires_at",
        type_=sa.DateTime(timezone=True),
        postgresql_using="expires_at AT TIME ZONE 'UTC'",
    )


def downgrade() -> None:
    op.alter_column(
        "refresh_tokens",
        "expires_at",
        type_=sa.DateTime(timezone=False),
        postgresql_using="expires_at AT TIME ZONE 'UTC'",
    )

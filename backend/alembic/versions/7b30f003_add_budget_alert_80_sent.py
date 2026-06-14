"""add_budget_alert_80_sent

Revision ID: 7b30f003
Revises: 7b30f002
Create Date: 2026-06-11

D-06: flag to prevent duplicate 80% budget alerts.
"""

import sqlalchemy as sa
from alembic import op

revision = "7b30f003"
down_revision = "7b30f002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "budgets",
        sa.Column(
            "alert_80_sent",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("budgets", "alert_80_sent")

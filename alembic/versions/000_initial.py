"""initial schema — users + events

Revision ID: 000_initial
Revises:
Create Date: 2026-01-01 00:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "000_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("username", sa.String(32), nullable=False),
        sa.Column("password_hash", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_id", "users", ["id"], unique=False)

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("level", sa.String(20), nullable=False, server_default="info"),
        sa.Column(
            "severity", sa.String(20), nullable=False, server_default="info"
        ),
        sa.Column("message", sa.String(500), nullable=False),
        sa.Column("remediation_hint", sa.String(1000), nullable=True),
        sa.Column("runbook_id", sa.String(100), nullable=True),
        sa.Column("metric_cpu", sa.Float(), nullable=True),
        sa.Column("metric_mem", sa.Float(), nullable=True),
        sa.Column("metric_rps", sa.Float(), nullable=True),
    )
    op.create_index("ix_events_id", "events", ["id"], unique=False)
    op.create_index("ix_events_ts", "events", ["ts"], unique=False)
    op.create_index("ix_events_severity", "events", ["severity"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_events_severity", table_name="events")
    op.drop_index("ix_events_ts", table_name="events")
    op.drop_index("ix_events_id", table_name="events")
    op.drop_table("events")

    op.drop_index("ix_users_id", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
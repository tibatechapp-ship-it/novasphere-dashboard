"""add audit_log table

Revision ID: 001_audit_log
Revises: 000_initial
Create Date: 2026-01-01 00:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_audit_log"
down_revision: Union[str, None] = "000_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user", sa.String(32), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("target", sa.String(200), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
    )
    op.create_index("ix_audit_log_id", "audit_log", ["id"])
    op.create_index("ix_audit_log_ts", "audit_log", ["ts"])
    op.create_index("ix_audit_log_user", "audit_log", ["user"])
    op.create_index("ix_audit_log_action", "audit_log", ["action"])


def downgrade() -> None:
    op.drop_index("ix_audit_log_action", table_name="audit_log")
    op.drop_index("ix_audit_log_user", table_name="audit_log")
    op.drop_index("ix_audit_log_ts", table_name="audit_log")
    op.drop_index("ix_audit_log_id", table_name="audit_log")
    op.drop_table("audit_log")
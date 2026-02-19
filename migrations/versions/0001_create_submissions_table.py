"""Create submissions table baseline.

Revision ID: 0001
Revises:
Create Date: 2026-02-19 09:07:00.000000

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "submissions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("month", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("test_coverage", sa.JSON(), nullable=True),
        sa.Column("overall_test_cases", sa.Integer(), nullable=True),
        sa.Column("supported_releases_count", sa.Integer(), nullable=True),
        sa.Column("raw_conversation", sa.String(), nullable=True),
        sa.CheckConstraint(
            "overall_test_cases IS NULL OR overall_test_cases >= 0",
            name="ck_submissions_overall_test_cases_non_negative",
        ),
        sa.CheckConstraint(
            "supported_releases_count IS NULL OR supported_releases_count >= 0",
            name="ck_submissions_supported_releases_non_negative",
        ),
        sa.CheckConstraint(
            "length(month) = 7 AND substr(month, 5, 1) = '-' "
            "AND CAST(substr(month, 1, 4) AS INTEGER) BETWEEN 2000 AND 2100 "
            "AND CAST(substr(month, 6, 2) AS INTEGER) BETWEEN 1 AND 12",
            name="ck_submissions_month_iso",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "month", name="uq_project_month"),
    )
    op.create_index("ix_submissions_project_id", "submissions", ["project_id"], unique=False)
    op.create_index("ix_submissions_month", "submissions", ["month"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_submissions_month", table_name="submissions")
    op.drop_index("ix_submissions_project_id", table_name="submissions")
    op.drop_table("submissions")

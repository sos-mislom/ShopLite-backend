"""add store visits

Revision ID: a785af671557
Revises: 238481681222
Create Date: 2026-01-02 21:13:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a785af671557"
down_revision: Union[str, None] = "238481681222"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "store_visits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("path", sa.Text(), nullable=True),
        sa.Column("referrer", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_store_visits_store_id_created_at", "store_visits", ["store_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_store_visits_store_id_created_at", table_name="store_visits")
    op.drop_table("store_visits")


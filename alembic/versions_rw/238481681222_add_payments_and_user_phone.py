"""add payments and user phone

Revision ID: 238481681222
Revises: 26651686583e
Create Date: 2026-01-02 21:09:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "238481681222"
down_revision: Union[str, None] = "26651686583e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone", sa.String(length=50), nullable=True))

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_payment_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default=sa.text("'RUB'"), nullable=False),
        sa.Column("confirmation_url", sa.Text(), nullable=True),
        sa.Column("raw_response", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider_payment_id"),
    )


def downgrade() -> None:
    op.drop_table("payments")
    op.drop_column("users", "phone")

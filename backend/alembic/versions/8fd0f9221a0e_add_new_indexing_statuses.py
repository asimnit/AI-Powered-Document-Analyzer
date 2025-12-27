"""add_new_indexing_statuses

Revision ID: 8fd0f9221a0e
Revises: d5faaa3cf5ac
Create Date: 2025-12-27 10:41:09.174786

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8fd0f9221a0e'
down_revision: Union[str, Sequence[str], None] = 'd5faaa3cf5ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add new indexing status values."""
    # Add new enum values to the processingstatus enum (matching existing UPPERCASE convention)
    op.execute("ALTER TYPE processingstatus ADD VALUE IF NOT EXISTS 'INDEXING'")
    op.execute("ALTER TYPE processingstatus ADD VALUE IF NOT EXISTS 'INDEXED'")
    op.execute("ALTER TYPE processingstatus ADD VALUE IF NOT EXISTS 'PARTIALLY_INDEXED'")
    op.execute("ALTER TYPE processingstatus ADD VALUE IF NOT EXISTS 'INDEXING_FAILED'")


def downgrade() -> None:
    """Downgrade schema - Note: PostgreSQL doesn't support removing enum values."""
    # PostgreSQL doesn't allow removing enum values once added
    # The old values will remain but won't be used
    pass

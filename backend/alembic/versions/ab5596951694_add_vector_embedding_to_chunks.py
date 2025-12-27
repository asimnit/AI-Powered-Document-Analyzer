"""add_vector_embedding_to_chunks

Revision ID: ab5596951694
Revises: 06ab023bcfeb
Create Date: 2025-12-25 20:45:38.353733

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab5596951694'
down_revision: Union[str, Sequence[str], None] = '06ab023bcfeb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

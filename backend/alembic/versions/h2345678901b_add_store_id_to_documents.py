"""add_store_id_to_documents

Revision ID: h2345678901b
Revises: g1234567890a
Create Date: 2025-12-28 10:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'h2345678901b'
down_revision: Union[str, Sequence[str], None] = 'g1234567890a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add store_id column to documents table."""
    # Add store_id as nullable first
    op.add_column('documents', sa.Column('store_id', sa.Integer(), nullable=True))
    
    # Create foreign key constraint
    op.create_foreign_key(
        'fk_documents_store_id',
        'documents',
        'document_stores',
        ['store_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # Create index for better query performance
    op.create_index(op.f('ix_documents_store_id'), 'documents', ['store_id'], unique=False)


def downgrade() -> None:
    """Remove store_id column from documents table."""
    op.drop_index(op.f('ix_documents_store_id'), table_name='documents')
    op.drop_constraint('fk_documents_store_id', 'documents', type_='foreignkey')
    op.drop_column('documents', 'store_id')

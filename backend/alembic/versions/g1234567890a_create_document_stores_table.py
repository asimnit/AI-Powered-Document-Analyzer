"""create_document_stores_table

Revision ID: g1234567890a
Revises: 8fd0f9221a0e
Create Date: 2025-12-28 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g1234567890a'
down_revision: Union[str, Sequence[str], None] = '8fd0f9221a0e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create document_stores table."""
    op.create_table('document_stores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_document_stores_user_id'), 'document_stores', ['user_id'], unique=False)
    op.create_index(op.f('ix_document_stores_is_deleted'), 'document_stores', ['is_deleted'], unique=False)
    
    # Create unique constraint for store name per user (excluding deleted stores)
    # Note: PostgreSQL partial unique constraint
    op.execute("""
        CREATE UNIQUE INDEX unique_store_name_per_user 
        ON document_stores(user_id, name) 
        WHERE is_deleted = false
    """)


def downgrade() -> None:
    """Drop document_stores table."""
    op.drop_index('unique_store_name_per_user', table_name='document_stores')
    op.drop_index(op.f('ix_document_stores_is_deleted'), table_name='document_stores')
    op.drop_index(op.f('ix_document_stores_user_id'), table_name='document_stores')
    op.drop_table('document_stores')

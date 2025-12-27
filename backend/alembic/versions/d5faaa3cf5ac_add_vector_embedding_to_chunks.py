"""add_vector_embedding_to_chunks

Revision ID: d5faaa3cf5ac
Revises: ab5596951694
Create Date: 2025-12-25 20:46:32.681827

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = 'd5faaa3cf5ac'
down_revision: Union[str, Sequence[str], None] = 'ab5596951694'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add pgvector extension and embedding column."""
    # Create pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Add embedding column to document_chunks
    op.add_column(
        'document_chunks',
        sa.Column('embedding', Vector(1536), nullable=True)
    )
    
    # Add indexed_at column to track when embeddings were generated
    op.add_column(
        'document_chunks',
        sa.Column('indexed_at', sa.DateTime(), nullable=True)
    )
    
    # Create index for vector similarity search using cosine distance
    op.execute(
        'CREATE INDEX idx_document_chunks_embedding ON document_chunks '
        'USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)'
    )


def downgrade() -> None:
    """Downgrade schema: Remove vector column and extension."""
    # Drop index
    op.execute('DROP INDEX IF EXISTS idx_document_chunks_embedding')
    
    # Drop columns
    op.drop_column('document_chunks', 'indexed_at')
    op.drop_column('document_chunks', 'embedding')
    
    # Note: We don't drop the vector extension as other tables might use it

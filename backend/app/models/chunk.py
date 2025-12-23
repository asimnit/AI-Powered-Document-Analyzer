"""
Document Chunk Model

Represents text chunks extracted from documents for efficient processing and retrieval.
Documents are split into smaller chunks for:
- Better context management for AI models
- More precise information retrieval
- Efficient vector embedding storage
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class DocumentChunk(Base):
    """
    Document Chunk database model
    
    Stores text chunks extracted from documents:
    - Each chunk contains ~1000-2000 characters of text
    - Maintains order via chunk_index
    - Tracks page numbers for source reference
    - Stores metadata for filtering and search
    """
    __tablename__ = "document_chunks"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key - Parent document
    document_id = Column(
        Integer, 
        ForeignKey("documents.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    
    # Chunk Information
    chunk_index = Column(Integer, nullable=False)              # Order within document (0, 1, 2, ...)
    content = Column(Text, nullable=False)                     # Actual text content
    char_count = Column(Integer, nullable=False)               # Number of characters
    word_count = Column(Integer, nullable=False)               # Number of words
    
    # Source Reference
    page_numbers = Column(JSON, nullable=True)                 # List of page numbers this chunk spans [1, 2]
    
    # Metadata (use chunk_metadata to avoid SQLAlchemy's reserved 'metadata' name)
    chunk_metadata = Column(JSON, nullable=True)               # Additional chunk metadata (language, etc.)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"
    
    @property
    def preview(self) -> str:
        """Return first 100 characters as preview"""
        return self.content[:100] + "..." if len(self.content) > 100 else self.content

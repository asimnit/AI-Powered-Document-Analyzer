"""
Document Model

Represents uploaded documents in the database.
Each document belongs to a user and tracks file information,
processing status, and metadata.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class ProcessingStatus(str, enum.Enum):
    """
    Document processing status enum
    
    Tracks the lifecycle of a document from upload to processing completion
    """
    UPLOADED = "UPLOADED"           # Just uploaded, awaiting processing
    PROCESSING = "PROCESSING"       # Currently being analyzed by AI
    COMPLETED = "COMPLETED"         # Processing complete, ready to query
    FAILED = "FAILED"              # Processing failed, check error message
    DELETED = "DELETED"            # Soft delete - marked for deletion
    INDEXING = "INDEXING"          # Generating embeddings for search
    INDEXED = "INDEXED"            # Embeddings generated successfully
    PARTIALLY_INDEXED = "PARTIALLY_INDEXED"  # Some embeddings failed
    INDEXING_FAILED = "INDEXING_FAILED"      # Embedding generation failed


class Document(Base):
    """
    Document database model
    
    Stores information about uploaded documents including:
    - File metadata (name, type, size, path)
    - Processing status and results
    - Relationship to user who uploaded it
    """
    __tablename__ = "documents"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key - Owner of this document
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Foreign Key - Store this document belongs to
    store_id = Column(Integer, ForeignKey("document_stores.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # File Information
    filename = Column(String(255), nullable=False)              # Original filename (e.g., "report.pdf")
    file_path = Column(String(500), nullable=False, unique=True) # S3 key or storage path
    file_type = Column(String(50), nullable=False)              # MIME type or extension (e.g., "pdf", "docx")
    file_size = Column(Integer, nullable=False)                 # Size in bytes
    
    # Timestamps
    upload_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Processing Status
    status = Column(
        Enum(ProcessingStatus), 
        default=ProcessingStatus.UPLOADED, 
        nullable=False,
        index=True  # Index for filtering by status
    )
    
    # Processing Results (populated after AI analysis)
    extracted_text = Column(Text, nullable=True)                # Full text extracted from document
    summary = Column(Text, nullable=True)                       # AI-generated summary
    page_count = Column(Integer, nullable=True)                 # Number of pages (if applicable)
    word_count = Column(Integer, nullable=True)                 # Total word count
    language = Column(String(10), nullable=True)                # Detected language code (e.g., "en", "es")
    
    # Error Handling
    error_message = Column(Text, nullable=True)                 # Error details if processing failed
    
    # Soft Delete
    is_deleted = Column(Boolean, default=False, nullable=False) # For soft deletion
    deleted_at = Column(DateTime, nullable=True)                # When it was deleted
    
    # Relationships
    user = relationship("User", back_populates="documents")
    store = relationship("DocumentStore", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    # Future: queries = relationship("Query", back_populates="document")  # Q&A history
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', user_id={self.user_id}, status='{self.status}')>"
    
    @property
    def file_size_mb(self) -> float:
        """Return file size in megabytes"""
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def is_processing_complete(self) -> bool:
        """Check if document processing is complete"""
        return self.status == ProcessingStatus.COMPLETED
    
    @property
    def is_ready_for_query(self) -> bool:
        """Check if document is ready to be queried"""
        return (
            self.status == ProcessingStatus.COMPLETED 
            and not self.is_deleted 
            and self.extracted_text is not None
        )

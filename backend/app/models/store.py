"""
Document Store Model

Represents a collection/folder of documents in the database.
Each store belongs to a user and contains multiple documents.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class DocumentStore(Base):
    """
    Document Store database model
    
    Stores allow users to organize documents into collections.
    Each store has a unique name per user and can contain multiple documents.
    """
    __tablename__ = "document_stores"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key - Owner of this store
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Store Information
    name = Column(String(255), nullable=False)           # Store name (must be unique per user)
    description = Column(Text, nullable=True)             # Optional description
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Soft Delete
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="document_stores")
    documents = relationship("Document", back_populates="store", cascade="all, delete-orphan")
    conversations = relationship("Conversation", secondary="conversation_stores", back_populates="stores")
    
    def __repr__(self):
        return f"<DocumentStore(id={self.id}, name='{self.name}', user_id={self.user_id})>"
    
    @property
    def document_count(self) -> int:
        """Return count of documents in this store"""
        return len([doc for doc in self.documents if not doc.is_deleted])

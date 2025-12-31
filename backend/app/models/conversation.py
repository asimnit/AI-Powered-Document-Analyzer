"""
Conversation Model

Represents a chat conversation where users can ask questions about their documents.
Conversations can have multiple document stores attached (many-to-many relationship).
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


# Junction table for many-to-many relationship between conversations and stores
conversation_stores = Table(
    'conversation_stores',
    Base.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('conversation_id', Integer, ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
    Column('store_id', Integer, ForeignKey('document_stores.id', ondelete='CASCADE'), nullable=False),
    Column('attached_at', DateTime, default=datetime.utcnow, nullable=False)
)


class Conversation(Base):
    """
    Conversation database model
    
    Represents a chat conversation with:
    - User ownership
    - Multiple document stores attached (via junction table)
    - Message history
    - Auto-generated or custom title
    """
    __tablename__ = "conversations"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key - Owner of this conversation
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Conversation Information
    title = Column(String(500), nullable=True)  # Auto-generated from first question or custom
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    stores = relationship("DocumentStore", secondary=conversation_stores, back_populates="conversations")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, title='{self.title}', user_id={self.user_id})>"
    
    @property
    def message_count(self) -> int:
        """Get the number of messages in this conversation"""
        return len(self.messages)
    
    @property
    def store_count(self) -> int:
        """Get the number of attached stores"""
        return len(self.stores)
    
    @property
    def last_message_at(self) -> datetime:
        """Get the timestamp of the last message"""
        if self.messages:
            return self.messages[-1].created_at
        return self.created_at

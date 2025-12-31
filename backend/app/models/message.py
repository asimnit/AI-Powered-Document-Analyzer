"""
Message Model

Represents individual messages in a chat conversation.
Messages can be from the user or the AI assistant, with sources tracked for assistant responses.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Message(Base):
    """
    Message database model
    
    Stores individual chat messages with:
    - Role (user or assistant)
    - Message content
    - Source citations (for assistant messages)
    - Token usage tracking
    """
    __tablename__ = "messages"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key - Conversation this message belongs to
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Message Information
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)      # The actual message text
    
    # Source Attribution (for assistant messages)
    # JSON structure: [{"store_id": 1, "store_name": "Research", "document_id": 5, 
    #                   "document_name": "paper.pdf", "chunk_id": 10, "chunk_text": "...", 
    #                   "page_number": 3, "similarity_score": 0.85}]
    sources = Column(JSON, nullable=True)
    
    # Token Usage (for cost tracking)
    token_count = Column(Integer, nullable=True)  # Number of tokens in this message
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, role='{self.role}', conversation_id={self.conversation_id})>"
    
    @property
    def is_user_message(self) -> bool:
        """Check if this message is from the user"""
        return self.role == "user"
    
    @property
    def is_assistant_message(self) -> bool:
        """Check if this message is from the assistant"""
        return self.role == "assistant"
    
    @property
    def has_sources(self) -> bool:
        """Check if this message has source citations"""
        return self.sources is not None and len(self.sources) > 0
    
    @property
    def source_count(self) -> int:
        """Get the number of sources cited"""
        return len(self.sources) if self.sources else 0

"""
Chat Schemas

Request and response models for chat/conversation functionality
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ==================== Source Citation ====================

class SourceCitation(BaseModel):
    """Source citation for assistant responses"""
    
    store_id: int = Field(..., description="Store ID")
    store_name: str = Field(..., description="Store name")
    document_id: int = Field(..., description="Document ID")
    document_name: str = Field(..., description="Document filename")
    chunk_id: int = Field(..., description="Chunk ID")
    chunk_text: str = Field(..., description="Chunk text excerpt (truncated)")
    page_number: Optional[int] = Field(None, description="Page number (if available)")
    similarity_score: float = Field(..., description="Similarity score (0-1)")
    
    class Config:
        from_attributes = True


# ==================== Message ====================

class MessageResponse(BaseModel):
    """Response model for a single message"""
    
    id: int = Field(..., description="Message ID")
    conversation_id: int = Field(..., description="Conversation ID")
    role: str = Field(..., description="Message role (user or assistant)")
    content: str = Field(..., description="Message content")
    sources: Optional[List[SourceCitation]] = Field(None, description="Source citations (for assistant messages)")
    token_count: Optional[int] = Field(None, description="Token count (for cost tracking)")
    created_at: datetime = Field(..., description="Message timestamp")
    
    class Config:
        from_attributes = True


# ==================== Conversation ====================

class ConversationResponse(BaseModel):
    """Response model for conversation metadata"""
    
    id: int = Field(..., description="Conversation ID")
    user_id: int = Field(..., description="User ID")
    title: Optional[str] = Field(None, description="Conversation title")
    store_count: int = Field(..., description="Number of attached stores")
    message_count: int = Field(..., description="Number of messages")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


class AttachedStoreInfo(BaseModel):
    """Info about a store attached to a conversation"""
    
    store_id: int = Field(..., description="Store ID")
    store_name: str = Field(..., description="Store name")
    attached_at: datetime = Field(..., description="When store was attached")
    
    class Config:
        from_attributes = True


class ConversationDetail(BaseModel):
    """Detailed conversation with messages and attached stores"""
    
    id: int = Field(..., description="Conversation ID")
    user_id: int = Field(..., description="User ID")
    title: Optional[str] = Field(None, description="Conversation title")
    attached_stores: List[AttachedStoreInfo] = Field(..., description="Attached stores")
    messages: List[MessageResponse] = Field(..., description="Conversation messages")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


# ==================== Requests ====================

class CreateConversationRequest(BaseModel):
    """Request to create a new conversation"""
    
    title: Optional[str] = Field(None, max_length=500, description="Conversation title (optional)")
    store_ids: Optional[List[int]] = Field(None, description="Initial stores to attach (optional)")


class UpdateConversationRequest(BaseModel):
    """Request to update conversation title"""
    
    title: str = Field(..., min_length=1, max_length=500, description="New conversation title")


class AttachStoresRequest(BaseModel):
    """Request to attach stores to a conversation"""
    
    store_ids: List[int] = Field(..., min_items=1, max_items=5, description="Store IDs to attach (1-5)")


class AskQuestionRequest(BaseModel):
    """Request to ask a question in a conversation"""
    
    query: str = Field(..., min_length=1, max_length=2000, description="User question")


# ==================== Responses ====================

class AskQuestionResponse(BaseModel):
    """Response after asking a question"""
    
    user_message: MessageResponse = Field(..., description="User's question message")
    assistant_message: MessageResponse = Field(..., description="Assistant's answer message")
    
    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """Response with list of conversations"""
    
    conversations: List[ConversationResponse] = Field(..., description="List of conversations")
    total: int = Field(..., description="Total number of conversations")
    
    class Config:
        from_attributes = True


class AttachStoresResponse(BaseModel):
    """Response after attaching stores"""
    
    conversation_id: int = Field(..., description="Conversation ID")
    attached_stores: List[AttachedStoreInfo] = Field(..., description="Currently attached stores")
    total_stores: int = Field(..., description="Total number of attached stores")
    
    class Config:
        from_attributes = True


class DetachStoreResponse(BaseModel):
    """Response after detaching a store"""
    
    conversation_id: int = Field(..., description="Conversation ID")
    detached_store_id: int = Field(..., description="Detached store ID")
    remaining_stores: int = Field(..., description="Number of remaining stores")
    
    class Config:
        from_attributes = True

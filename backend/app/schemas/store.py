"""
Document Store Schemas

Pydantic models for document store API request/response validation
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Dict


# Request Schemas

class StoreCreate(BaseModel):
    """Request schema for creating a new store"""
    name: str = Field(..., min_length=1, max_length=255, description="Store name (required)")
    description: Optional[str] = Field(None, description="Store description (optional)")


class StoreUpdate(BaseModel):
    """Request schema for updating a store"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Store name")
    description: Optional[str] = Field(None, description="Store description")


# Response Schemas

class StoreResponse(BaseModel):
    """Basic store information"""
    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    document_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class StoreStatusBreakdown(BaseModel):
    """Document status breakdown within a store"""
    uploaded: int = 0
    processing: int = 0
    completed: int = 0
    indexing: int = 0
    indexed: int = 0
    partially_indexed: int = 0
    indexing_failed: int = 0
    failed: int = 0


class StoreDetail(BaseModel):
    """Detailed store information with statistics"""
    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    document_count: int = 0
    status_breakdown: StoreStatusBreakdown
    total_size: int = 0  # Total size in bytes
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class StoreListResponse(BaseModel):
    """Paginated list of stores"""
    stores: list[StoreResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class StoreDeleteResponse(BaseModel):
    """Response after deleting a store"""
    message: str
    deleted_documents_count: int


class ProcessAllResponse(BaseModel):
    """Response after processing all documents in a store"""
    message: str
    task_ids: list[str]
    documents_queued: int


class RetryAllFailedResponse(BaseModel):
    """Response after retrying all failed documents in a store"""
    message: str
    task_ids: list[str]
    documents_queued: int


class RetryAllIndexingResponse(BaseModel):
    """Response after retrying indexing for all completed documents in a store"""
    message: str
    task_ids: list[str]
    documents_queued: int


class MoveDocumentRequest(BaseModel):
    """Request schema for moving a document to another store"""
    store_id: int = Field(..., description="Target store ID")

"""
Document Schemas

Pydantic models for document API request/response validation
"""

from pydantic import BaseModel, Field, ConfigDict, field_serializer
from datetime import datetime
from typing import Optional

from app.models.document import ProcessingStatus


# Request Schemas

class DocumentUploadResponse(BaseModel):
    """Response after successful document upload"""
    id: int
    filename: str
    file_type: str
    file_size: int
    status: ProcessingStatus
    upload_date: datetime
    message: str = "Document uploaded successfully"
    
    @field_serializer('status')
    def serialize_status(self, status: ProcessingStatus) -> str:
        """Convert status enum to lowercase for frontend consistency"""
        return status.value.lower()
    
    model_config = ConfigDict(from_attributes=True)


# Response Schemas

class DocumentResponse(BaseModel):
    """Complete document information"""
    id: int
    user_id: int
    filename: str
    file_path: str
    file_type: str
    file_size: int
    upload_date: datetime
    last_modified: datetime
    status: ProcessingStatus
    error_message: Optional[str] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    
    # Computed properties
    file_size_mb: float
    is_ready_for_query: bool
    
    @field_serializer('status')
    def serialize_status(self, status: ProcessingStatus) -> str:
        """Convert status enum to lowercase for frontend consistency"""
        return status.value.lower()
    
    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    """Paginated list of documents"""
    documents: list[DocumentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DocumentSummary(BaseModel):
    """Brief document information for list views"""
    id: int
    filename: str
    file_type: str
    file_size_mb: float
    upload_date: datetime
    status: ProcessingStatus
    error_message: Optional[str] = None
    is_ready_for_query: bool
    store_name: Optional[str] = None
    
    @field_serializer('status')
    def serialize_status(self, status: ProcessingStatus) -> str:
        """Convert status enum to lowercase for frontend consistency"""
        return status.value.lower()
    
    model_config = ConfigDict(from_attributes=True)


class DocumentListSummary(BaseModel):
    """Paginated list of document summaries"""
    documents: list[DocumentSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class DocumentDeleteResponse(BaseModel):
    """Response after document deletion"""
    message: str
    document_id: int
    filename: str


class DocumentStats(BaseModel):
    """User's document statistics"""
    total_documents: int
    total_size_mb: float
    by_status: dict[str, int]
    by_type: dict[str, int]

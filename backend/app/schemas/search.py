"""
Search Schemas

Request and response models for semantic search functionality
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class SearchRequest(BaseModel):
    """Request model for semantic search"""
    
    query: str = Field(..., min_length=1, max_length=500, description="Search query text")
    top_k: Optional[int] = Field(5, ge=1, le=20, description="Number of results to return")


class SearchResultItem(BaseModel):
    """Single search result item"""
    
    chunk_id: int = Field(..., description="Chunk ID")
    chunk_content: str = Field(..., description="Chunk text content")
    chunk_index: int = Field(..., description="Chunk index within document")
    document_id: int = Field(..., description="Document ID")
    document_filename: str = Field(..., description="Document filename")
    similarity_score: float = Field(..., description="Similarity score (0-1, higher is better)")
    page_numbers: List[int] = Field(default_factory=list, description="Page numbers where chunk appears")
    
    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    """Response model for search results"""
    
    query: str = Field(..., description="Original search query")
    results: List[SearchResultItem] = Field(..., description="Search results ordered by relevance")
    total_results: int = Field(..., description="Number of results returned")
    store_id: int = Field(..., description="Store ID searched")
    
    class Config:
        from_attributes = True

"""
Semantic Search Service

Performs vector similarity search using pgvector to find relevant document chunks
within a specific store based on a query.
"""

import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.services.embeddings import EmbeddingService
from app.core.config import settings

logger = logging.getLogger(__name__)


class SearchResult:
    """Single search result with chunk and document info"""
    
    def __init__(
        self,
        chunk_id: int,
        chunk_content: str,
        chunk_index: int,
        document_id: int,
        document_filename: str,
        similarity_score: float,
        page_numbers: Optional[List[int]] = None
    ):
        self.chunk_id = chunk_id
        self.chunk_content = chunk_content
        self.chunk_index = chunk_index
        self.document_id = document_id
        self.document_filename = document_filename
        self.similarity_score = similarity_score
        self.page_numbers = page_numbers or []


class SearchService:
    """
    Semantic search service using vector similarity
    
    Searches document chunks within a specific store using
    cosine similarity on embeddings.
    """
    
    def __init__(self):
        """Initialize search service with embedding service"""
        self.embedding_service = EmbeddingService()
        logger.info("✅ Search service initialized")
    
    async def search_in_store(
        self,
        db: Session,
        store_id: int,
        user_id: int,
        query: str,
        top_k: Optional[int] = None
    ) -> List[SearchResult]:
        """
        Perform semantic search within a specific store
        
        Args:
            db: Database session
            store_id: Store ID to search within
            user_id: User ID (for access control)
            query: Search query text
            top_k: Number of results to return (default from config)
            
        Returns:
            List of SearchResult objects ordered by similarity
        """
        if not top_k:
            top_k = settings.RAG_TOP_K
        
        logger.info(f"🔍 Semantic search in store {store_id}: '{query}' (top_k={top_k})")
        
        try:
            # Generate embedding for query
            query_embedding = await self.embedding_service.generate_embedding(query)
            logger.info(f"Generated query embedding: {len(query_embedding)} dimensions")
            
            # Perform vector similarity search using pgvector
            # <=> is the cosine distance operator in pgvector
            results = db.query(
                DocumentChunk.id,
                DocumentChunk.content,
                DocumentChunk.chunk_index,
                DocumentChunk.page_numbers,
                Document.id.label('document_id'),
                Document.filename,
                DocumentChunk.embedding.cosine_distance(query_embedding).label('distance')
            ).join(
                Document, DocumentChunk.document_id == Document.id
            ).filter(
                and_(
                    Document.store_id == store_id,
                    Document.user_id == user_id,
                    Document.is_deleted == False,
                    DocumentChunk.embedding.isnot(None)  # Only search indexed chunks
                )
            ).order_by(
                DocumentChunk.embedding.cosine_distance(query_embedding)
            ).limit(top_k).all()
            
            # Convert to SearchResult objects
            search_results = []
            for row in results:
                # Convert cosine distance to similarity score (1 - distance)
                similarity_score = 1.0 - row.distance
                
                search_result = SearchResult(
                    chunk_id=row.id,
                    chunk_content=row.content,
                    chunk_index=row.chunk_index,
                    document_id=row.document_id,
                    document_filename=row.filename,
                    similarity_score=round(similarity_score, 4),
                    page_numbers=row.page_numbers
                )
                search_results.append(search_result)
            
            logger.info(f"✅ Found {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            raise Exception(f"Search failed: {str(e)}")

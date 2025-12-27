"""
Embedding Service

High-level service for generating and managing embeddings
using the configured LLM provider.
"""

import logging
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app.services.llm.factory import get_llm_provider
from app.models.chunk import DocumentChunk
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Embedding service for generating and storing vector embeddings
    
    Uses the configured LLM provider (Azure OpenAI by default)
    to generate embeddings for document chunks.
    """
    
    def __init__(self):
        """Initialize embedding service with LLM provider"""
        self.llm_provider = get_llm_provider()
        logger.info("✅ Embedding service initialized")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        return await self.llm_provider.get_embedding(text)
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        # Process in batches to avoid API limits
        batch_size = settings.EMBEDDING_BATCH_SIZE
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1} ({len(batch)} texts)")
            embeddings = await self.llm_provider.get_embeddings_batch(batch)
            all_embeddings.extend(embeddings)
        
        return all_embeddings
    
    async def embed_chunk(self, chunk: DocumentChunk, db: Session) -> bool:
        """
        Generate and store embedding for a single chunk
        
        Args:
            chunk: DocumentChunk to embed
            db: Database session
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Generating embedding for chunk {chunk.id}")
            
            # Generate embedding
            embedding = await self.generate_embedding(chunk.content)
            
            # Store in database
            chunk.embedding = embedding
            chunk.indexed_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"✅ Chunk {chunk.id} embedded successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to embed chunk {chunk.id}: {e}")
            db.rollback()
            return False
    
    async def embed_chunks_batch(self, chunks: List[DocumentChunk], db: Session) -> tuple[int, str | None]:
        """
        Generate and store embeddings for multiple chunks in batch
        
        Args:
            chunks: List of DocumentChunks to embed
            db: Database session
            
        Returns:
            Tuple of (success_count, error_message)
            - success_count: Number of successfully embedded chunks
            - error_message: Error message if failure occurred, None otherwise
        """
        try:
            logger.info(f"📦 Generating embeddings for {len(chunks)} chunks")
            
            # Extract text content
            texts = [chunk.content for chunk in chunks]
            
            # Generate embeddings in batch
            embeddings = await self.generate_embeddings_batch(texts)
            
            # Store embeddings
            success_count = 0
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
                chunk.indexed_at = datetime.utcnow()
                success_count += 1
            
            db.commit()
            logger.info(f"✅ Successfully embedded {success_count}/{len(chunks)} chunks")
            return success_count, None
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Failed to embed chunks batch: {error_msg}")
            db.rollback()
            return 0, error_msg
    
    async def reindex_document_chunks(self, document_id: int, db: Session) -> int:
        """
        Regenerate embeddings for all chunks of a document
        
        Args:
            document_id: Document ID
            db: Database session
            
        Returns:
            Number of successfully re-indexed chunks
        """
        try:
            logger.info(f"🔄 Re-indexing chunks for document {document_id}")
            
            # Get all chunks for document
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).all()
            
            if not chunks:
                logger.warning(f"No chunks found for document {document_id}")
                return 0
            
            # Generate embeddings
            success_count = await self.embed_chunks_batch(chunks, db)
            
            logger.info(f"✅ Re-indexed {success_count}/{len(chunks)} chunks for document {document_id}")
            return success_count
            
        except Exception as e:
            logger.error(f"❌ Failed to re-index document {document_id}: {e}")
            return 0


# Global embedding service instance
embedding_service = EmbeddingService()

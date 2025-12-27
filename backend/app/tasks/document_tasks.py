"""
Document Processing Tasks

Celery tasks for asynchronous document processing:
- Parse documents to extract text
- Chunk text for efficient storage
- Generate embeddings for chunks
- Update document status via WebSocket
"""

import logging
import os
import tempfile
import asyncio
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.models import Document, DocumentChunk, ProcessingStatus
from app.services.parsers import ParserFactory
from app.services.chunking import TextChunker
from app.services.embeddings import embedding_service
from app.api.endpoints.websocket import broadcast_document_update_sync

# S3 Client (if S3 is enabled)
import boto3
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize services
parser_factory = ParserFactory()
text_chunker = TextChunker()


def get_s3_client():
    """Get configured S3 client"""
    return boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION
    )


@celery_app.task(bind=True, name="app.tasks.process_document")
def process_document_task(self, document_id: int):
    """
    Process a document: parse, chunk, and store
    
    Args:
        document_id: ID of document to process
    """
    db = SessionLocal()
    
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found")
            return {"status": "error", "message": "Document not found"}
        
        # Update status to processing
        document.status = ProcessingStatus.PROCESSING
        db.commit()
        
        # Broadcast status update via WebSocket
        broadcast_document_update_sync(
            user_id=document.user_id,
            document_id=document_id,
            status="processing",
            message="Processing document..."
        )
        
        logger.info(f"Processing document {document_id}: {document.filename}")
        
        # Download file from S3 if enabled
        if settings.S3_UPLOAD_ENABLED:
            temp_file = download_from_s3(document.file_path)
            file_path = temp_file
        else:
            file_path = document.file_path
        
        # Parse document
        parser_result = parser_factory.parse(file_path)
        
        if not parser_result.success:
            # Parsing failed
            document.status = ProcessingStatus.FAILED
            document.error_message = parser_result.error
            db.commit()
            
            # Broadcast failure via WebSocket
            broadcast_document_update_sync(
                user_id=document.user_id,
                document_id=document_id,
                status="failed",
                message=parser_result.error
            )
            
            # Clean up temp file
            if settings.S3_UPLOAD_ENABLED and os.path.exists(file_path):
                os.unlink(file_path)
            
            return {"status": "error", "message": parser_result.error}
        
        # Store extracted text
        document.extracted_text = parser_result.text
        document.page_count = parser_result.page_count
        document.word_count = parser_result.word_count
        
        # Detect language
        language = text_chunker.detect_language(parser_result.text)
        document.language = language
        
        # Create text chunks
        chunks = text_chunker.chunk_text(parser_result.text)
        
        # Store chunks in database
        for chunk in chunks:
            db_chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=chunk.index,
                content=chunk.content,
                char_count=chunk.char_count,
                word_count=chunk.word_count,
                page_numbers=chunk.page_numbers,
                chunk_metadata={"language": language}
            )
            db.add(db_chunk)
        
        # Update document status to completed
        document.status = ProcessingStatus.COMPLETED
        db.commit()
        
        # Broadcast success via WebSocket
        broadcast_document_update_sync(
            user_id=document.user_id,
            document_id=document_id,
            status="completed",
            message=f"Successfully processed {len(chunks)} chunks",
            data={
                "chunks": len(chunks),
                "word_count": document.word_count,
                "language": language
            }
        )
        
        # Clean up temp file
        if settings.S3_UPLOAD_ENABLED and os.path.exists(file_path):
            os.unlink(file_path)
        
        logger.info(f"Successfully processed document {document_id}: {len(chunks)} chunks created")
        
        # Trigger embedding generation task
        logger.info(f"🔷 Triggering embedding generation for document {document_id}")
        generate_embeddings_task.delay(document_id)
        
        return {
            "status": "success",
            "document_id": document_id,
            "chunks": len(chunks),
            "word_count": document.word_count,
            "language": language
        }
        
    except Exception as e:
        # Handle any unexpected errors
        logger.error(f"Error processing document {document_id}: {str(e)}")
        
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = ProcessingStatus.FAILED
                document.error_message = str(e)
                db.commit()
                
                # Broadcast error via WebSocket
                broadcast_document_update_sync(
                    user_id=document.user_id,
                    document_id=document_id,
                    status="failed",
                    message=str(e)
                )
        except:
            pass
        
        return {"status": "error", "message": str(e)}
        
    finally:
        db.close()


def download_from_s3(s3_key: str) -> str:
    """
    Download file from S3 to temp directory
    
    Args:
        s3_key: S3 object key
        
    Returns:
        Path to downloaded temp file
    """
    s3_client = get_s3_client()
    
    # Create temp file
    suffix = os.path.splitext(s3_key)[1]
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_path = temp_file.name
    temp_file.close()
    
    # Download from S3
    logger.info(f"Downloading {s3_key} from S3")
    s3_client.download_file(
        settings.S3_BUCKET_NAME,
        s3_key,
        temp_path
    )
    
    return temp_path


@celery_app.task(bind=True, name="app.tasks.generate_embeddings")
def generate_embeddings_task(self, document_id: int):
    """
    Generate embeddings for all chunks of a document
    
    Args:
        document_id: ID of document to generate embeddings for
    """
    db = SessionLocal()
    
    try:
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found")
            return {"status": "error", "message": "Document not found"}
        
        # Get all chunks for this document
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).all()
        
        if not chunks:
            logger.warning(f"No chunks found for document {document_id}")
            return {"status": "success", "message": "No chunks to embed", "chunks": 0}
        
        logger.info(f"🔷 Generating embeddings for document {document_id}: {len(chunks)} chunks")
        
        # Update document status to indexing
        db.expire(document)
        document.status = ProcessingStatus.INDEXING
        db.commit()
        db.refresh(document)
        logger.info(f"Document {document_id} status updated to INDEXING in DB")
        
        # Broadcast status update
        broadcast_document_update_sync(
            user_id=document.user_id,
            document_id=document_id,
            status="indexing",
            message=f"Generating embeddings for {len(chunks)} chunks..."
        )
        
        # Generate embeddings using async service
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success_count, embedding_error = loop.run_until_complete(
                embedding_service.embed_chunks_batch(chunks, db)
            )
        finally:
            loop.close()
        
        if success_count == len(chunks):
            # All embeddings succeeded
            logger.info(f"✅ Successfully generated embeddings for document {document_id}")
            
            # Update document status to indexed
            db.expire(document)
            document.status = ProcessingStatus.INDEXED
            document.error_message = None
            db.commit()
            db.refresh(document)
            logger.info(f"Document {document_id} updated in DB - Status: {document.status}")
            
            # Broadcast success
            broadcast_document_update_sync(
                user_id=document.user_id,
                document_id=document_id,
                status="indexed",
                message=f"Successfully indexed {success_count} chunks"
            )
            
            return {
                "status": "success",
                "document_id": document_id,
                "chunks_indexed": success_count
            }
        elif success_count == 0:
            # Complete failure - no embeddings succeeded
            logger.error(f"❌ Failed to generate any embeddings for document {document_id}")
            
            error_msg = f"Embedding generation failed: {embedding_error or 'Unknown error'}"
            
            # Update document with complete failure status
            db.expire(document)
            document.status = ProcessingStatus.INDEXING_FAILED
            document.error_message = error_msg
            db.commit()
            db.refresh(document)
            
            logger.info(f"Document {document_id} updated in DB - Status: {document.status}, Error: {document.error_message}")
            
            # Broadcast failure
            broadcast_document_update_sync(
                user_id=document.user_id,
                document_id=document_id,
                status="indexing_failed",
                message=error_msg
            )
            
            return {
                "status": "failed",
                "document_id": document_id,
                "chunks_indexed": 0,
                "total_chunks": len(chunks),
                "error": error_msg
            }
        else:
            # Partial success - some embeddings succeeded
            logger.warning(f"⚠️ Partially indexed document {document_id}: {success_count}/{len(chunks)} chunks")
            
            error_msg = f"Partially indexed: {success_count}/{len(chunks)} chunks succeeded. Some embeddings failed to generate."
            
            # Update document with partial success status
            db.expire(document)
            document.status = ProcessingStatus.PARTIALLY_INDEXED
            document.error_message = error_msg
            db.commit()
            db.refresh(document)
            
            logger.info(f"Document {document_id} updated in DB - Status: {document.status}, Error: {document.error_message}")
            
            # Broadcast partial success
            broadcast_document_update_sync(
                user_id=document.user_id,
                document_id=document_id,
                status="partially_indexed",
                message=error_msg
            )
            
            return {
                "status": "partial",
                "document_id": document_id,
                "chunks_indexed": success_count,
                "total_chunks": len(chunks)
            }
    
    except Exception as e:
        logger.error(f"❌ Error generating embeddings for document {document_id}: {str(e)}")
        
        try:
            # Re-fetch document to ensure we have latest state
            db.rollback()  # Rollback any pending changes
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                error_msg = f"Embedding generation failed: {str(e)}"
                document.status = ProcessingStatus.INDEXING_FAILED
                document.error_message = error_msg
                db.commit()
                db.refresh(document)
                logger.info(f"Document {document_id} updated in DB - Status: {document.status}, Error: {document.error_message}")
                
                broadcast_document_update_sync(
                    user_id=document.user_id,
                    document_id=document_id,
                    status="indexing_failed",
                    message=error_msg
                )
        except Exception as inner_e:
            logger.error(f"Failed to update document status: {str(inner_e)}")
        
        return {"status": "error", "message": str(e)}
    
    finally:
        db.close()

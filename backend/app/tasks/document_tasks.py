"""
Document Processing Tasks

Celery tasks for asynchronous document processing:
- Parse documents to extract text
- Chunk text for efficient storage
- Update document status via WebSocket
"""

import logging
import os
import tempfile
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.models import Document, DocumentChunk, ProcessingStatus
from app.services.parsers import ParserFactory
from app.services.chunking import TextChunker
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

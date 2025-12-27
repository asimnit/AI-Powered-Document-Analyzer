"""
Document Endpoints

API routes for document management:
- Upload documents
- List user's documents
- Get document details
- Delete documents
- Get document statistics
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import io
import mimetypes

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.logging_config import get_logger
from app.models.user import User
from app.models.document import Document, ProcessingStatus
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentResponse,
    DocumentListResponse,
    DocumentSummary,
    DocumentListSummary,
    DocumentDeleteResponse,
    DocumentStats
)
from app.services.storage import storage_service
from app.core.config import settings

router = APIRouter()
logger = get_logger(__name__)

# File type validation
ALLOWED_MIME_TYPES = {
    'application/pdf': '.pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
    'text/plain': '.txt',
    'image/png': '.png',
    'image/jpeg': '.jpg',
    'image/jpg': '.jpg'
}


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload a new document
    
    - **file**: Document file (PDF, DOCX, XLSX, TXT, PNG, JPG)
    - **Max size**: Configured in settings (default 10MB)
    - Returns document information with upload status
    """
    logger.info(f"📤 Upload request from user {current_user.username} (id={current_user.id}): {file.filename}")
    
    # Validate file presence
    if not file or not file.filename:
        logger.warning("❌ Upload failed: No file provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    # Validate file type
    content_type = file.content_type
    if content_type not in ALLOWED_MIME_TYPES:
        logger.warning(f"❌ Upload failed: Invalid file type {content_type}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Supported: {', '.join(ALLOWED_MIME_TYPES.values())}"
        )
    
    # Read file content
    try:
        content = await file.read()
        file_size = len(content)
        
        # Validate file size
        if file_size > settings.MAX_FILE_SIZE:
            logger.warning(f"❌ Upload failed: File too large ({file_size} bytes)")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
        
        if file_size == 0:
            logger.warning("❌ Upload failed: Empty file")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        logger.info(f"📊 File size: {file_size / 1024:.2f} KB")
        
        # Upload to storage (S3 or local)
        file_obj = io.BytesIO(content)
        file_path = await storage_service.upload_file(
            file=file_obj,
            filename=file.filename,
            user_id=current_user.id,
            content_type=content_type
        )
        
        # Get file extension
        file_extension = ALLOWED_MIME_TYPES.get(content_type, '.bin')
        
        # Create document record in database
        db_document = Document(
            user_id=current_user.id,
            filename=file.filename,
            file_path=file_path,
            file_type=file_extension.lstrip('.'),
            file_size=file_size,
            status=ProcessingStatus.UPLOADED
        )
        
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        logger.info(f"✅ Document uploaded successfully: id={db_document.id}, path={file_path}")
        
        return DocumentUploadResponse(
            id=db_document.id,
            filename=db_document.filename,
            file_type=db_document.file_type,
            file_size=db_document.file_size,
            status=db_document.status,
            upload_date=db_document.upload_date
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Upload failed: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.get("/", response_model=DocumentListSummary)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List user's documents with pagination
    
    - **page**: Page number (starts at 1)
    - **page_size**: Items per page (max 100)
    - **status_filter**: Filter by processing status (optional)
    - Returns paginated list of documents
    """
    logger.info(f"📋 List documents request from user {current_user.username} (page={page}, size={page_size})")
    
    try:
        # Base query - user's documents only
        query = db.query(Document).filter(Document.user_id == current_user.id)
        
        # Apply status filter if provided (convert lowercase to uppercase for enum match)
        if status_filter:
            status_enum = ProcessingStatus[status_filter.upper()] if status_filter.upper() in ProcessingStatus.__members__ else None
            if status_enum:
                query = query.filter(Document.status == status_enum)
        
        # Get total count
        total = query.count()
        
        # Calculate pagination
        total_pages = (total + page_size - 1) // page_size
        offset = (page - 1) * page_size
        
        # Get documents for current page
        documents = query.order_by(Document.upload_date.desc()).offset(offset).limit(page_size).all()
        
        # Convert to summary format
        document_summaries = [
            DocumentSummary(
                id=doc.id,
                filename=doc.filename,
                file_type=doc.file_type,
                file_size_mb=doc.file_size_mb,
                upload_date=doc.upload_date,
                status=doc.status,
                error_message=doc.error_message,
                is_ready_for_query=doc.is_ready_for_query
            )
            for doc in documents
        ]
        
        logger.info(f"✅ Retrieved {len(documents)} documents (total: {total})")
        
        return DocumentListSummary(
            documents=document_summaries,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to list documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed information about a specific document
    
    - **document_id**: Document ID
    - Returns complete document information
    - Only the owner can access their documents
    """
    logger.info(f"📄 Get document {document_id} request from user {current_user.username}")
    
    try:
        # Get document
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        ).first()
        
        if not document:
            logger.warning(f"❌ Document {document_id} not found or unauthorized")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        logger.info(f"✅ Document {document_id} retrieved: {document.filename}")
        
        return DocumentResponse(
            id=document.id,
            user_id=document.user_id,
            filename=document.filename,
            file_path=document.file_path,
            file_type=document.file_type,
            file_size=document.file_size,
            upload_date=document.upload_date,
            last_modified=document.last_modified,
            status=document.status,
            error_message=document.error_message,
            page_count=document.page_count,
            word_count=document.word_count,
            file_size_mb=document.file_size_mb,
            is_ready_for_query=document.is_ready_for_query
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}"
        )


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a document
    
    - **document_id**: Document ID
    - Deletes file from storage and database record
    - Only the owner can delete their documents
    """
    logger.info(f"🗑️  Delete document {document_id} request from user {current_user.username}")
    
    try:
        # Get document
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        ).first()
        
        if not document:
            logger.warning(f"❌ Document {document_id} not found or unauthorized")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        filename = document.filename
        file_path = document.file_path
        
        # Delete from storage
        try:
            await storage_service.delete_file(file_path)
            logger.info(f"✅ Deleted file from storage: {file_path}")
        except Exception as e:
            logger.warning(f"⚠️  Failed to delete file from storage: {e}")
            # Continue with database deletion even if storage deletion fails
        
        # Delete from database
        db.delete(document)
        db.commit()
        
        logger.info(f"✅ Document {document_id} deleted successfully: {filename}")
        
        return DocumentDeleteResponse(
            message="Document deleted successfully",
            document_id=document_id,
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete document: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/stats/overview", response_model=DocumentStats)
async def get_document_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user's document statistics
    
    - Returns total documents, total size, breakdown by status and type
    """
    logger.info(f"📊 Stats request from user {current_user.username}")
    
    try:
        # Get all user's documents
        documents = db.query(Document).filter(Document.user_id == current_user.id).all()
        
        total_documents = len(documents)
        total_size = sum(doc.file_size for doc in documents)
        total_size_mb = total_size / (1024 * 1024)
        
        # Group by status
        by_status = {}
        for doc in documents:
            status_key = doc.status.value
            by_status[status_key] = by_status.get(status_key, 0) + 1
        
        # Group by type
        by_type = {}
        for doc in documents:
            by_type[doc.file_type] = by_type.get(doc.file_type, 0) + 1
        
        logger.info(f"✅ Stats retrieved: {total_documents} documents, {total_size_mb:.2f} MB")
        
        return DocumentStats(
            total_documents=total_documents,
            total_size_mb=round(total_size_mb, 2),
            by_status=by_status,
            by_type=by_type
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )


@router.get("/download/{document_id}")
async def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Download a document file
    
    - **document_id**: Document ID
    - Returns file content as download
    - Only the owner can download their documents
    """
    logger.info(f"📥 Download document {document_id} request from user {current_user.username}")
    
    try:
        # Get document
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        ).first()
        
        if not document:
            logger.warning(f"❌ Document {document_id} not found or unauthorized")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Download from storage
        file_content = await storage_service.download_file(document.file_path)
        
        # Determine content type
        content_type = mimetypes.guess_type(document.filename)[0] or 'application/octet-stream'
        
        logger.info(f"✅ Document {document_id} downloaded: {document.filename}")
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={document.filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to download document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download document: {str(e)}"
        )


@router.post("/{document_id}/process", status_code=status.HTTP_202_ACCEPTED)
async def process_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Trigger document processing
    
    Queues the document for background processing:
    - Text extraction
    - Language detection
    - Text chunking
    - Storage in database
    
    Returns immediately with task ID for tracking.
    """
    try:
        # Get document
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.id,
            Document.is_deleted == False
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check if already processing or completed
        if document.status == ProcessingStatus.PROCESSING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document is already being processed"
            )
        
        if document.status == ProcessingStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document has already been processed"
            )
        
        # Queue the task
        from app.tasks.document_tasks import process_document_task
        task = process_document_task.delay(document_id)
        
        logger.info(f"✅ Queued processing for document {document_id}, task_id: {task.id}")
        
        return {
            "message": "Document processing started",
            "document_id": document_id,
            "task_id": task.id,
            "status": "queued"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to queue document processing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start processing: {str(e)}"
        )


@router.post("/{document_id}/retry-indexing", status_code=status.HTTP_202_ACCEPTED)
async def retry_document_indexing(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retry embedding generation for a document
    
    Used when indexing fails or partially completes.
    Queues the document for embedding generation:
    - Regenerates embeddings for all chunks
    - Updates document status
    
    Returns immediately with task ID for tracking.
    """
    try:
        # Get document
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.id,
            Document.is_deleted == False
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check if document has chunks (text processing must be complete)
        if document.status not in [ProcessingStatus.COMPLETED, ProcessingStatus.INDEXING_FAILED, ProcessingStatus.PARTIALLY_INDEXED, ProcessingStatus.INDEXED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document must be processed before indexing can be retried"
            )
        
        # Check if already indexing
        if document.status == ProcessingStatus.INDEXING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document is already being indexed"
            )
        
        # Queue the embedding generation task
        from app.tasks.document_tasks import generate_embeddings_task
        task = generate_embeddings_task.delay(document_id)
        
        logger.info(f"✅ Queued indexing retry for document {document_id}, task_id: {task.id}")
        
        return {
            "message": "Document indexing started",
            "document_id": document_id,
            "task_id": task.id,
            "status": "queued"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to queue document indexing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start indexing: {str(e)}"
        )

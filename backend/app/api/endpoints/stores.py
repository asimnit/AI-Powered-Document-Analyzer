"""
Document Store Endpoints

API routes for document store management:
- List all stores for user
- Create new store
- Get store details with statistics
- Update store information
- Delete store and all documents
- Get documents in a store
- Process all documents in a store
- Retry all failed documents in a store
- Retry indexing for all completed documents in a store
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.logging_config import get_logger
from app.models.user import User
from app.models.document import Document, ProcessingStatus
from app.schemas.store import (
    StoreCreate,
    StoreUpdate,
    StoreResponse,
    StoreDetail,
    StoreListResponse,
    StoreDeleteResponse,
    ProcessAllResponse,
    RetryAllFailedResponse,
    RetryAllIndexingResponse,
    MoveDocumentRequest
)
from app.schemas.document import DocumentListSummary, DocumentSummary
from app.schemas.search import SearchRequest, SearchResponse, SearchResultItem
from app.services.store_service import store_service
from app.services.search_service import SearchService

router = APIRouter()
logger = get_logger(__name__)


@router.get("/", response_model=StoreListResponse)
async def list_stores(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all stores for current user
    
    Returns paginated list of stores with document counts
    """
    logger.info(f"📋 List stores request from user {current_user.username} (page={page}, size={page_size})")
    
    try:
        # Get all stores for user
        stores = store_service.get_user_stores(db, current_user.id)
        
        # Calculate pagination
        total = len(stores)
        total_pages = (total + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size
        
        # Get stores for current page
        paginated_stores = stores[start:end]
        
        # Convert to response format
        store_responses = []
        for store in paginated_stores:
            # Count documents in store (excluding soft-deleted)
            doc_count = db.query(Document).filter(
                Document.store_id == store.id,
                Document.is_deleted == False
            ).count()
            
            store_responses.append(StoreResponse(
                id=store.id,
                user_id=store.user_id,
                name=store.name,
                description=store.description,
                document_count=doc_count,
                created_at=store.created_at,
                updated_at=store.updated_at
            ))
        
        logger.info(f"✅ Returned {len(store_responses)} stores for user {current_user.username}")
        
        return StoreListResponse(
            stores=store_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to list stores: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list stores: {str(e)}"
        )


@router.post("/", response_model=StoreResponse, status_code=status.HTTP_201_CREATED)
async def create_store(
    store_data: StoreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new document store
    
    - **name**: Store name (required, must be unique per user)
    - **description**: Store description (optional)
    """
    logger.info(f"📁 Create store request from user {current_user.username}: name='{store_data.name}'")
    
    try:
        # Check if store name already exists for this user
        if store_service.check_store_name_exists(db, current_user.id, store_data.name):
            logger.warning(f"❌ Store name already exists: '{store_data.name}'")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A store with name '{store_data.name}' already exists"
            )
        
        # Create store
        store = store_service.create_store(
            db,
            user_id=current_user.id,
            name=store_data.name,
            description=store_data.description
        )
        
        return StoreResponse(
            id=store.id,
            user_id=store.user_id,
            name=store.name,
            description=store.description,
            document_count=0,
            created_at=store.created_at,
            updated_at=store.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create store: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create store: {str(e)}"
        )


@router.get("/{store_id}", response_model=StoreDetail)
async def get_store(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get store details with document statistics
    
    Returns store information including:
    - Status breakdown (count by processing status)
    - Total storage size
    - Document count
    """
    logger.info(f"📊 Get store details: store_id={store_id}, user={current_user.username}")
    
    try:
        # Get store
        store = store_service.get_store_by_id(db, store_id, current_user.id)
        
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found"
            )
        
        # Get status breakdown
        status_breakdown = store_service.get_store_status_breakdown(db, store_id)
        
        # Get total size
        total_size = store_service.get_store_total_size(db, store_id)
        
        # Count documents
        doc_count = db.query(Document).filter(
            Document.store_id == store_id,
            Document.is_deleted == False
        ).count()
        
        return StoreDetail(
            id=store.id,
            user_id=store.user_id,
            name=store.name,
            description=store.description,
            document_count=doc_count,
            status_breakdown=status_breakdown,
            total_size=total_size,
            created_at=store.created_at,
            updated_at=store.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get store details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get store details: {str(e)}"
        )


@router.put("/{store_id}", response_model=StoreResponse)
async def update_store(
    store_id: int,
    store_data: StoreUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update store name or description
    
    - **name**: New store name (optional)
    - **description**: New description (optional)
    """
    logger.info(f"✏️ Update store: store_id={store_id}, user={current_user.username}")
    
    try:
        # Check if new name conflicts with existing store
        if store_data.name and store_service.check_store_name_exists(
            db, current_user.id, store_data.name, exclude_store_id=store_id
        ):
            logger.warning(f"❌ Store name already exists: '{store_data.name}'")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A store with name '{store_data.name}' already exists"
            )
        
        # Update store
        store = store_service.update_store(
            db,
            store_id=store_id,
            user_id=current_user.id,
            name=store_data.name,
            description=store_data.description
        )
        
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found"
            )
        
        # Count documents
        doc_count = db.query(Document).filter(
            Document.store_id == store_id,
            Document.is_deleted == False
        ).count()
        
        return StoreResponse(
            id=store.id,
            user_id=store.user_id,
            name=store.name,
            description=store.description,
            document_count=doc_count,
            created_at=store.created_at,
            updated_at=store.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update store: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update store: {str(e)}"
        )


@router.delete("/{store_id}", response_model=StoreDeleteResponse)
async def delete_store(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete store and ALL documents permanently
    
    ⚠️ Warning: This action cannot be undone
    All documents in this store will be permanently deleted
    """
    logger.info(f"🗑️ Delete store: store_id={store_id}, user={current_user.username}")
    
    try:
        # Delete store
        success, deleted_count = await store_service.delete_store(db, store_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found"
            )
        
        return StoreDeleteResponse(
            message=f"Store deleted successfully",
            deleted_documents_count=deleted_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete store: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete store: {str(e)}"
        )


@router.get("/{store_id}/documents", response_model=DocumentListSummary)
async def get_store_documents(
    store_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by filename"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all documents in a store
    
    - **page**: Page number (starts at 1)
    - **page_size**: Items per page (max 100)
    - **status_filter**: Filter by processing status (optional)
    - **search**: Search by filename (optional)
    """
    logger.info(f"📄 Get store documents: store_id={store_id}, user={current_user.username}")
    
    try:
        # Verify store belongs to user
        store = store_service.get_store_by_id(db, store_id, current_user.id)
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found"
            )
        
        # Base query
        query = db.query(Document).filter(
            Document.store_id == store_id,
            Document.is_deleted == False
        )
        
        # Apply status filter
        if status_filter:
            status_enum = ProcessingStatus[status_filter.upper()] if status_filter.upper() in ProcessingStatus.__members__ else None
            if status_enum:
                query = query.filter(Document.status == status_enum)
        
        # Apply search filter
        if search:
            query = query.filter(Document.filename.ilike(f"%{search}%"))
        
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
                is_ready_for_query=doc.status == ProcessingStatus.INDEXED
            )
            for doc in documents
        ]
        
        return DocumentListSummary(
            documents=document_summaries,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get store documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get store documents: {str(e)}"
        )


@router.post("/{store_id}/process-all", response_model=ProcessAllResponse)
async def process_all_documents(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Process all UPLOADED documents in store
    
    Queues full processing tasks (parse, chunk, embed) for all documents with UPLOADED status
    """
    logger.info(f"⚙️ Process all documents: store_id={store_id}, user={current_user.username}")
    
    try:
        # Verify store belongs to user
        store = store_service.get_store_by_id(db, store_id, current_user.id)
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found"
            )
        
        # Get all UPLOADED documents in store
        documents = db.query(Document).filter(
            Document.store_id == store_id,
            Document.status == ProcessingStatus.UPLOADED,
            Document.is_deleted == False
        ).all()
        
        if not documents:
            return ProcessAllResponse(
                message="No documents with UPLOADED status found",
                task_ids=[],
                documents_queued=0
            )
        
        # Queue processing tasks (full processing: parse -> chunk -> embed)
        from app.tasks.document_tasks import process_document_task
        
        task_ids = []
        for doc in documents:
            task = process_document_task.delay(doc.id)
            task_ids.append(task.id)
        
        logger.info(f"✅ Queued {len(task_ids)} documents for processing")
        
        return ProcessAllResponse(
            message=f"Queued {len(documents)} documents for processing",
            task_ids=task_ids,
            documents_queued=len(documents)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to process all documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process all documents: {str(e)}"
        )


@router.post("/{store_id}/retry-all-failed", response_model=RetryAllFailedResponse)
async def retry_all_failed_documents(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retry all FAILED documents
    
    Queues retry tasks for all failed documents (processing failures only)
    """
    logger.info(f"🔄 Retry all failed: store_id={store_id}, user={current_user.username}")
    
    try:
        # Verify store belongs to user
        store = store_service.get_store_by_id(db, store_id, current_user.id)
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found"
            )
        
        # Get all failed documents in store
        documents = db.query(Document).filter(
            Document.store_id == store_id,
            Document.status == ProcessingStatus.FAILED,
            Document.is_deleted == False
        ).all()
        
        if not documents:
            return RetryAllFailedResponse(
                message="No failed documents found",
                task_ids=[],
                documents_queued=0
            )
        
        # Queue retry tasks
        from app.tasks.document_tasks import process_document_task
        
        task_ids = []
        for doc in documents:
            task = process_document_task.delay(doc.id)
            task_ids.append(task.id)
        
        logger.info(f"✅ Queued {len(task_ids)} failed documents for retry")
        
        return RetryAllFailedResponse(
            message=f"Queued {len(documents)} failed documents for retry",
            task_ids=task_ids,
            documents_queued=len(documents)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to retry all failed documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry all failed documents: {str(e)}"
        )


@router.post("/{store_id}/retry-all-indexing", response_model=RetryAllIndexingResponse)
async def retry_all_completed_indexing(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retry indexing for all INDEXING_FAILED and PARTIALLY_INDEXED documents
    
    Queues indexing tasks for documents that failed during embedding generation
    """
    logger.info(f"🔄 Retry all indexing: store_id={store_id}, user={current_user.username}")
    
    try:
        # Verify store belongs to user
        store = store_service.get_store_by_id(db, store_id, current_user.id)
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found"
            )
        
        # Get all indexing failed documents in store
        documents = db.query(Document).filter(
            Document.store_id == store_id,
            Document.status.in_([
                ProcessingStatus.INDEXING_FAILED,
                ProcessingStatus.PARTIALLY_INDEXED
            ]),
            Document.is_deleted == False
        ).all()
        
        if not documents:
            return RetryAllIndexingResponse(
                message="No indexing failed documents found",
                task_ids=[],
                documents_queued=0
            )
        
        # Queue indexing tasks
        from app.tasks.document_tasks import generate_embeddings_task
        
        task_ids = []
        for doc in documents:
            task = generate_embeddings_task.delay(doc.id)
            task_ids.append(task.id)
        
        logger.info(f"✅ Queued {len(task_ids)} indexing failed documents for retry")
        
        return RetryAllIndexingResponse(
            message=f"Queued {len(documents)} indexing failed documents for retry",
            task_ids=task_ids,
            documents_queued=len(documents)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to retry all indexing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry all indexing: {str(e)}"
        )


@router.post("/{store_id}/search", response_model=SearchResponse)
async def search_in_store(
    store_id: int,
    request: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Semantic search within a specific store
    
    Performs vector similarity search on document chunks within the specified store.
    Returns the most relevant chunks based on the query.
    
    Args:
        store_id: Store ID to search within
        request: Search request with query and top_k
        
    Returns:
        SearchResponse with relevant chunks
    """
    logger.info(f"🔍 Search in store {store_id}: '{request.query}' (top_k={request.top_k})")
    
    try:
        # Verify store exists and user has access
        store = store_service.get_store_by_id(db, store_id, current_user.id)
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found"
            )
        
        # Perform semantic search
        search_service = SearchService()
        results = await search_service.search_in_store(
            db=db,
            store_id=store_id,
            user_id=current_user.id,
            query=request.query,
            top_k=request.top_k
        )
        
        # Convert to response format
        result_items = [
            SearchResultItem(
                chunk_id=r.chunk_id,
                chunk_content=r.chunk_content,
                chunk_index=r.chunk_index,
                document_id=r.document_id,
                document_filename=r.document_filename,
                similarity_score=r.similarity_score,
                page_numbers=r.page_numbers
            )
            for r in results
        ]
        
        return SearchResponse(
            query=request.query,
            results=result_items,
            total_results=len(result_items),
            store_id=store_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

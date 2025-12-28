"""
Document Store Service

Business logic for document store operations
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Tuple
from datetime import datetime

from app.models.store import DocumentStore
from app.models.document import Document, ProcessingStatus
from app.schemas.store import StoreStatusBreakdown
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class StoreService:
    """Service for managing document stores"""
    
    @staticmethod
    def get_user_stores(db: Session, user_id: int, include_deleted: bool = False) -> List[DocumentStore]:
        """
        Get all stores for a user
        
        Args:
            db: Database session
            user_id: User ID
            include_deleted: Whether to include soft-deleted stores
            
        Returns:
            List of DocumentStore objects
        """
        query = db.query(DocumentStore).filter(DocumentStore.user_id == user_id)
        
        if not include_deleted:
            query = query.filter(DocumentStore.is_deleted == False)
        
        return query.order_by(DocumentStore.created_at.desc()).all()
    
    @staticmethod
    def get_store_by_id(db: Session, store_id: int, user_id: int) -> Optional[DocumentStore]:
        """
        Get a store by ID, ensuring it belongs to the user
        
        Args:
            db: Database session
            store_id: Store ID
            user_id: User ID
            
        Returns:
            DocumentStore object or None
        """
        return db.query(DocumentStore).filter(
            DocumentStore.id == store_id,
            DocumentStore.user_id == user_id,
            DocumentStore.is_deleted == False
        ).first()
    
    @staticmethod
    def create_store(db: Session, user_id: int, name: str, description: Optional[str] = None) -> DocumentStore:
        """
        Create a new document store
        
        Args:
            db: Database session
            user_id: User ID
            name: Store name
            description: Store description (optional)
            
        Returns:
            Created DocumentStore object
        """
        store = DocumentStore(
            user_id=user_id,
            name=name,
            description=description
        )
        
        db.add(store)
        db.commit()
        db.refresh(store)
        
        logger.info(f"✅ Created store: id={store.id}, name='{name}', user_id={user_id}")
        return store
    
    @staticmethod
    def update_store(
        db: Session,
        store_id: int,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[DocumentStore]:
        """
        Update a store's name or description
        
        Args:
            db: Database session
            store_id: Store ID
            user_id: User ID
            name: New name (optional)
            description: New description (optional)
            
        Returns:
            Updated DocumentStore object or None
        """
        store = StoreService.get_store_by_id(db, store_id, user_id)
        
        if not store:
            return None
        
        if name is not None:
            store.name = name
        if description is not None:
            store.description = description
        
        store.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(store)
        
        logger.info(f"✅ Updated store: id={store.id}, user_id={user_id}")
        return store
    
    @staticmethod
    async def delete_store(db: Session, store_id: int, user_id: int) -> Tuple[bool, int]:
        """
        Delete a store and all its documents (hard delete)
        
        Args:
            db: Database session
            store_id: Store ID
            user_id: User ID
            
        Returns:
            Tuple of (success: bool, deleted_documents_count: int)
        """
        from app.services.storage import StorageService
        
        store = StoreService.get_store_by_id(db, store_id, user_id)
        
        if not store:
            return False, 0
        
        # Get all documents in this store
        documents = db.query(Document).filter(Document.store_id == store_id).all()
        document_count = len(documents)
        
        logger.info(f"🗑️  Deleting store {store_id}: found {document_count} documents")
        
        # Delete files from S3/local storage
        storage_service = StorageService()
        deleted_files = 0
        for doc in documents:
            try:
                logger.info(f"🗑️  Attempting to delete file: {doc.file_path}")
                await storage_service.delete_file(doc.file_path)
                deleted_files += 1
                logger.info(f"✅ Deleted file from storage: {doc.file_path}")
            except Exception as e:
                logger.error(f"❌ Failed to delete file {doc.file_path}: {e}")
        
        logger.info(f"Deleted {deleted_files}/{document_count} files from storage")
        
        # Delete store (CASCADE will delete all documents from DB)
        db.delete(store)
        db.commit()
        
        logger.info(f"✅ Deleted store: id={store_id}, documents_deleted={document_count}, user_id={user_id}")
        return True, document_count
    
    @staticmethod
    def get_store_status_breakdown(db: Session, store_id: int) -> StoreStatusBreakdown:
        """
        Get document status breakdown for a store
        
        Args:
            db: Database session
            store_id: Store ID
            
        Returns:
            StoreStatusBreakdown object
        """
        # Query document counts by status
        status_counts = db.query(
            Document.status,
            func.count(Document.id)
        ).filter(
            Document.store_id == store_id,
            Document.is_deleted == False
        ).group_by(Document.status).all()
        
        # Convert to dict
        breakdown = StoreStatusBreakdown()
        status_dict = {status.value.lower(): count for status, count in status_counts}
        
        # Map to schema fields
        breakdown.uploaded = status_dict.get('uploaded', 0)
        breakdown.processing = status_dict.get('processing', 0)
        breakdown.completed = status_dict.get('completed', 0)
        breakdown.indexing = status_dict.get('indexing', 0)
        breakdown.indexed = status_dict.get('indexed', 0)
        breakdown.partially_indexed = status_dict.get('partially_indexed', 0)
        breakdown.indexing_failed = status_dict.get('indexing_failed', 0)
        breakdown.failed = status_dict.get('failed', 0)
        
        return breakdown
    
    @staticmethod
    def get_store_total_size(db: Session, store_id: int) -> int:
        """
        Get total size of all documents in a store
        
        Args:
            db: Database session
            store_id: Store ID
            
        Returns:
            Total size in bytes
        """
        result = db.query(func.sum(Document.file_size)).filter(
            Document.store_id == store_id,
            Document.is_deleted == False
        ).scalar()
        
        return result or 0
    
    @staticmethod
    def check_store_name_exists(db: Session, user_id: int, name: str, exclude_store_id: Optional[int] = None) -> bool:
        """
        Check if a store name already exists for a user
        
        Args:
            db: Database session
            user_id: User ID
            name: Store name to check
            exclude_store_id: Store ID to exclude from check (for updates)
            
        Returns:
            True if name exists, False otherwise
        """
        query = db.query(DocumentStore).filter(
            DocumentStore.user_id == user_id,
            DocumentStore.name == name,
            DocumentStore.is_deleted == False
        )
        
        if exclude_store_id:
            query = query.filter(DocumentStore.id != exclude_store_id)
        
        return query.first() is not None
    
    @staticmethod
    def move_document(db: Session, document_id: int, target_store_id: int, user_id: int) -> bool:
        """
        Move a document to another store
        
        Args:
            db: Database session
            document_id: Document ID
            target_store_id: Target store ID
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        # Verify target store exists and belongs to user
        target_store = StoreService.get_store_by_id(db, target_store_id, user_id)
        if not target_store:
            return False
        
        # Get document and verify ownership
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == user_id
        ).first()
        
        if not document:
            return False
        
        # Move document
        document.store_id = target_store_id
        document.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"✅ Moved document: id={document_id} to store_id={target_store_id}, user_id={user_id}")
        return True


store_service = StoreService()

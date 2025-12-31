"""
Chat API Endpoints

Handles conversations, messages, store attachments, and RAG-powered Q&A.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models import User, Conversation, Message, DocumentStore, conversation_stores
from app.schemas.chat import (
    ConversationResponse,
    ConversationDetail,
    ConversationListResponse,
    CreateConversationRequest,
    UpdateConversationRequest,
    AttachStoresRequest,
    AttachStoresResponse,
    DetachStoreResponse,
    AskQuestionRequest,
    AskQuestionResponse,
    MessageResponse,
    SourceCitation,
    AttachedStoreInfo
)
from app.services.llm.factory import get_rag_service
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


# ==================== Helper Functions ====================

def _conversation_to_response(conv: Conversation) -> ConversationResponse:
    """Convert Conversation model to ConversationResponse"""
    return ConversationResponse(
        id=conv.id,
        user_id=conv.user_id,
        title=conv.title,
        store_count=conv.store_count,
        message_count=conv.message_count,
        created_at=conv.created_at,
        updated_at=conv.updated_at
    )


def _message_to_response(msg: Message) -> MessageResponse:
    """Convert Message model to MessageResponse"""
    sources = None
    if msg.sources:
        sources = [SourceCitation(**src) for src in msg.sources]
    
    return MessageResponse(
        id=msg.id,
        conversation_id=msg.conversation_id,
        role=msg.role,
        content=msg.content,
        sources=sources,
        token_count=msg.token_count,
        created_at=msg.created_at
    )


# ==================== Conversation Endpoints ====================

@router.get("/", response_model=ConversationListResponse)
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all conversations for the current user
    
    Returns list of conversations with metadata (no messages).
    Ordered by most recent first.
    """
    logger.info(f"📋 Listing conversations for user {current_user.id}")
    
    try:
        conversations = db.query(Conversation).filter(
            Conversation.user_id == current_user.id
        ).order_by(Conversation.updated_at.desc()).all()
        
        conv_responses = [_conversation_to_response(conv) for conv in conversations]
        
        logger.info(f"✅ Found {len(conv_responses)} conversations")
        return ConversationListResponse(
            conversations=conv_responses,
            total=len(conv_responses)
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to list conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list conversations: {str(e)}"
        )


@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    request: CreateConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new conversation
    
    - Title is optional (can be auto-generated later from first question)
    - Can optionally attach stores immediately (max 5)
    - Empty conversations are allowed
    """
    logger.info(f"💬 Creating conversation for user {current_user.id}")
    
    try:
        # Create conversation
        new_conv = Conversation(
            user_id=current_user.id,
            title=request.title
        )
        db.add(new_conv)
        db.flush()  # Get the ID
        
        # Attach stores if provided
        if request.store_ids:
            if len(request.store_ids) > settings.MAX_STORES_PER_CONVERSATION:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot attach more than {settings.MAX_STORES_PER_CONVERSATION} stores"
                )
            
            # Verify all stores exist and belong to user
            stores = db.query(DocumentStore).filter(
                and_(
                    DocumentStore.id.in_(request.store_ids),
                    DocumentStore.user_id == current_user.id,
                    DocumentStore.is_deleted == False
                )
            ).all()
            
            if len(stores) != len(request.store_ids):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="One or more stores not found"
                )
            
            # Attach stores
            new_conv.stores = stores
        
        db.commit()
        db.refresh(new_conv)
        
        logger.info(f"✅ Created conversation {new_conv.id} with {len(new_conv.stores)} stores")
        return _conversation_to_response(new_conv)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to create conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create conversation: {str(e)}"
        )


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get conversation details with messages and attached stores
    
    Returns full conversation history including all messages and sources.
    """
    logger.info(f"📖 Getting conversation {conversation_id}")
    
    try:
        conversation = db.query(Conversation).filter(
            and_(
                Conversation.id == conversation_id,
                Conversation.user_id == current_user.id
            )
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Get attached stores info
        attached_stores_info = []
        for store in conversation.stores:
            # Get attachment time from junction table
            attachment = db.execute(
                conversation_stores.select().where(
                    and_(
                        conversation_stores.c.conversation_id == conversation_id,
                        conversation_stores.c.store_id == store.id
                    )
                )
            ).first()
            
            attached_stores_info.append(AttachedStoreInfo(
                store_id=store.id,
                store_name=store.name,
                attached_at=attachment.attached_at if attachment else datetime.utcnow()
            ))
        
        # Convert messages
        message_responses = [_message_to_response(msg) for msg in conversation.messages]
        
        return ConversationDetail(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            attached_stores=attached_stores_info,
            messages=message_responses,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation: {str(e)}"
        )


@router.put("/{conversation_id}", response_model=ConversationResponse)
def update_conversation(
    conversation_id: int,
    request: UpdateConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update conversation title
    """
    logger.info(f"✏️ Updating conversation {conversation_id}")
    
    try:
        conversation = db.query(Conversation).filter(
            and_(
                Conversation.id == conversation_id,
                Conversation.user_id == current_user.id
            )
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        conversation.title = request.title
        conversation.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(conversation)
        
        logger.info(f"✅ Updated conversation {conversation_id} title")
        return _conversation_to_response(conversation)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to update conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update conversation: {str(e)}"
        )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a conversation and all its messages
    
    Cascade delete will remove all associated messages.
    """
    logger.info(f"🗑️ Deleting conversation {conversation_id}")
    
    try:
        conversation = db.query(Conversation).filter(
            and_(
                Conversation.id == conversation_id,
                Conversation.user_id == current_user.id
            )
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        db.delete(conversation)
        db.commit()
        
        logger.info(f"✅ Deleted conversation {conversation_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to delete conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {str(e)}"
        )


# ==================== Store Management Endpoints ====================

@router.post("/{conversation_id}/stores", response_model=AttachStoresResponse)
def attach_stores(
    conversation_id: int,
    request: AttachStoresRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Attach stores to a conversation
    
    - Maximum 5 stores total per conversation
    - Stores must belong to the user
    - Duplicate attachments are ignored
    """
    logger.info(f"📎 Attaching stores to conversation {conversation_id}")
    
    try:
        conversation = db.query(Conversation).filter(
            and_(
                Conversation.id == conversation_id,
                Conversation.user_id == current_user.id
            )
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Check total limit
        current_store_ids = {s.id for s in conversation.stores}
        new_store_ids = set(request.store_ids) - current_store_ids
        
        if len(current_store_ids) + len(new_store_ids) > settings.MAX_STORES_PER_CONVERSATION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot attach more than {settings.MAX_STORES_PER_CONVERSATION} stores total"
            )
        
        # Verify stores exist and belong to user
        new_stores = db.query(DocumentStore).filter(
            and_(
                DocumentStore.id.in_(list(new_store_ids)),
                DocumentStore.user_id == current_user.id,
                DocumentStore.is_deleted == False
            )
        ).all()
        
        if len(new_stores) != len(new_store_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more stores not found"
            )
        
        # Attach new stores
        conversation.stores.extend(new_stores)
        conversation.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(conversation)
        
        # Build response
        attached_stores_info = []
        for store in conversation.stores:
            attachment = db.execute(
                conversation_stores.select().where(
                    and_(
                        conversation_stores.c.conversation_id == conversation_id,
                        conversation_stores.c.store_id == store.id
                    )
                )
            ).first()
            
            attached_stores_info.append(AttachedStoreInfo(
                store_id=store.id,
                store_name=store.name,
                attached_at=attachment.attached_at if attachment else datetime.utcnow()
            ))
        
        logger.info(f"✅ Attached {len(new_stores)} stores to conversation {conversation_id}")
        
        return AttachStoresResponse(
            conversation_id=conversation_id,
            attached_stores=attached_stores_info,
            total_stores=len(attached_stores_info)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to attach stores: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to attach stores: {str(e)}"
        )


@router.delete("/{conversation_id}/stores/{store_id}", response_model=DetachStoreResponse)
def detach_store(
    conversation_id: int,
    store_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Detach a store from a conversation
    
    Allows removing stores that are no longer needed in the conversation.
    """
    logger.info(f"📌 Detaching store {store_id} from conversation {conversation_id}")
    
    try:
        conversation = db.query(Conversation).filter(
            and_(
                Conversation.id == conversation_id,
                Conversation.user_id == current_user.id
            )
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Find and remove store
        store_to_remove = None
        for store in conversation.stores:
            if store.id == store_id:
                store_to_remove = store
                break
        
        if not store_to_remove:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not attached to this conversation"
            )
        
        conversation.stores.remove(store_to_remove)
        conversation.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"✅ Detached store {store_id} from conversation {conversation_id}")
        
        return DetachStoreResponse(
            conversation_id=conversation_id,
            detached_store_id=store_id,
            remaining_stores=len(conversation.stores)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to detach store: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detach store: {str(e)}"
        )


# ==================== Chat Endpoint ====================

@router.post("/{conversation_id}/ask", response_model=AskQuestionResponse)
async def ask_question(
    conversation_id: int,
    request: AskQuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Ask a question in a conversation (RAG-powered Q&A)
    
    - Searches across all attached stores
    - Generates AI answer with source citations
    - Saves both user question and assistant answer
    - Auto-generates title from first question if needed
    
    Requires at least one store to be attached.
    """
    logger.info(f"💬 Question in conversation {conversation_id}: {request.query[:100]}")
    
    try:
        # Verify conversation exists and belongs to user
        conversation = db.query(Conversation).filter(
            and_(
                Conversation.id == conversation_id,
                Conversation.user_id == current_user.id
            )
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Create user message
        user_message = Message(
            conversation_id=conversation_id,
            role="user",
            content=request.query
        )
        db.add(user_message)
        db.flush()  # Get message ID
        
        # Get RAG service and generate answer
        rag_service = get_rag_service()
        
        try:
            rag_response = await rag_service.ask_question(
                question=request.query,
                conversation_id=conversation_id,
                user_id=current_user.id,
                db=db
            )
        except ValueError as e:
            # Handle no stores attached error gracefully
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        # Create assistant message
        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=rag_response["answer"],
            sources=rag_response["sources"],
            token_count=rag_response["token_count"]
        )
        db.add(assistant_message)
        
        # Auto-generate title from first question if needed
        if not conversation.title and conversation.message_count == 0:
            # Use first 60 chars of question as title
            conversation.title = request.query[:60] + ("..." if len(request.query) > 60 else "")
        
        conversation.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user_message)
        db.refresh(assistant_message)
        
        logger.info(f"✅ Generated answer with {len(rag_response['sources'])} sources")
        
        return AskQuestionResponse(
            user_message=_message_to_response(user_message),
            assistant_message=_message_to_response(assistant_message)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to process question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process question: {str(e)}"
        )

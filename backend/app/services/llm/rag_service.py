"""
RAG (Retrieval-Augmented Generation) Service

Implements the complete RAG pipeline for chat:
1. Retrieve relevant chunks from multiple stores
2. Build context from chunks
3. Generate answer using Azure OpenAI chat model
4. Return answer with source citations
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_config import get_logger
from app.services.search_service import SearchService
from app.services.llm.factory import get_llm_provider
from app.services.llm.prompts import (
    format_context_from_chunks,
    build_chat_messages,
    extract_sources_from_chunks
)
from app.models import Conversation, Message

logger = get_logger(__name__)


class RAGService:
    """
    RAG Service for multi-store document chat
    
    Handles:
    - Multi-store semantic search
    - Context aggregation and re-ranking
    - Answer generation with Azure OpenAI
    - Source attribution
    """
    
    def __init__(self):
        """Initialize RAG service with LLM provider"""
        self.search_service = SearchService()
        self.llm_provider = get_llm_provider()
        logger.info("✅ RAG Service initialized with LLM provider")
    
    async def ask_question(
        self,
        question: str,
        conversation_id: int,
        user_id: int,
        db: Session
    ) -> Dict:
        """
        Main RAG pipeline - ask a question about documents
        
        Args:
            question: User's question
            conversation_id: ID of the conversation
            user_id: ID of the user
            db: Database session
        
        Returns:
            Dictionary with:
            - answer: Generated answer text
            - sources: List of source citations
            - token_count: Tokens used in response
        
        Raises:
            ValueError: If no stores attached or other validation errors
            Exception: If OpenAI API call fails
        """
        logger.info(f"RAG query for conversation {conversation_id}: {question[:100]}")
        
        # 1. Get conversation and attached stores
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()
        
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        attached_stores = conversation.stores
        if not attached_stores:
            raise ValueError("No stores attached to this conversation. Please attach at least one store.")
        
        logger.info(f"Searching across {len(attached_stores)} stores")
        
        # 2. Search across all attached stores
        all_chunks = await self._search_across_stores(
            question=question,
            stores=attached_stores,
            user_id=user_id,
            db=db
        )
        
        if not all_chunks:
            logger.warning(f"No relevant chunks found for query: {question}")
            return {
                "answer": "I couldn't find any relevant information in your documents to answer this question. Please try rephrasing or check if you have documents uploaded that might contain this information.",
                "sources": [],
                "token_count": 0
            }
        
        # 3. Build context from chunks
        context = format_context_from_chunks(all_chunks)
        
        # 4. Get conversation history
        history = self._get_conversation_history(conversation)
        
        # 5. Build messages for chat completion
        messages = build_chat_messages(question, context, history)
        
        # 6. Generate answer using LLM provider
        try:
            logger.info(f"🤖 Calling LLM provider with {len(messages)} messages")
            logger.debug(f"Messages: {messages}")
            
            # No max_tokens - let model generate full response
            answer = await self.llm_provider.get_chat_completion(
                messages=messages
            )
            
            logger.info(f"🎯 LLM Response received: {len(answer)} chars")
            logger.info(f"📝 Answer preview: {answer[:200]}")
            
            # Estimate token count (actual count not available from LangChain)
            token_count = len(answer.split()) * 2  # Rough estimate: 1 token ≈ 0.5 words
            
            logger.info(f"✅ Generated answer (~{token_count} tokens): {answer[:100]}")
            
        except Exception as e:
            logger.error(f"❌ LLM provider error: {str(e)}")
            raise Exception(f"Failed to generate answer: {str(e)}")
        
        # 7. Extract sources for response
        sources = extract_sources_from_chunks(all_chunks)
        
        return {
            "answer": answer,
            "sources": sources,
            "token_count": token_count
        }
    
    async def _search_across_stores(
        self,
        question: str,
        stores: List,
        user_id: int,
        db: Session
    ) -> List[Dict]:
        """
        Search across multiple stores and aggregate results
        
        Args:
            question: Search query
            stores: List of DocumentStore objects
            user_id: User ID for security
            db: Database session
        
        Returns:
            List of top-k chunks across all stores, re-ranked by similarity
        """
        all_chunks = []
        
        # Search each store (top 5 per store)
        for store in stores:
            try:
                results = await self.search_service.search_in_store(
                    db=db,
                    store_id=store.id,
                    user_id=user_id,
                    query=question,
                    top_k=5  # Get top 5 from each store
                )
                
                # Convert SearchResult to dict format for prompts
                for result in results:
                    chunk_dict = {
                        'chunk_id': result.chunk_id,
                        'chunk_text': result.chunk_content,  # Fixed: use chunk_content
                        'document_id': result.document_id,
                        'document_name': result.document_filename,  # Fixed: use document_filename
                        'store_id': store.id,
                        'store_name': store.name,
                        'page_number': result.page_numbers[0] if result.page_numbers else None,  # Fixed: get first page
                        'similarity_score': result.similarity_score
                    }
                    all_chunks.append(chunk_dict)
                
                logger.info(f"Found {len(results)} chunks from store '{store.name}'")
                
            except Exception as e:
                logger.error(f"Error searching store {store.id}: {str(e)}")
                continue
        
        # Re-rank all chunks by similarity score and take top-k overall
        all_chunks.sort(key=lambda x: x['similarity_score'], reverse=True)
        top_chunks = all_chunks[:settings.RAG_CONTEXT_WINDOW]
        
        logger.info(f"Selected {len(top_chunks)} top chunks from {len(all_chunks)} total")
        return top_chunks
    
    def _get_conversation_history(self, conversation: Conversation) -> List[Dict]:
        """
        Get recent conversation history for context
        
        Args:
            conversation: Conversation object with messages relationship loaded
        
        Returns:
            List of message dictionaries
        """
        history = []
        recent_messages = conversation.messages[-settings.MAX_CONVERSATION_HISTORY:]
        
        for msg in recent_messages:
            history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return history


# Singleton instance
rag_service = RAGService()

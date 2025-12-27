"""
Azure OpenAI Provider Implementation

Implements LLM operations using Azure OpenAI Service via LangChain
"""

import logging
from typing import List, Dict, Optional

from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.services.llm.base import BaseLLMProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


class AzureOpenAIProvider(BaseLLMProvider):
    """
    Azure OpenAI provider implementation
    
    Uses LangChain's Azure OpenAI integrations for:
    - Embeddings (text-embedding-3-small)
    - Chat completions (gpt-4o-mini)
    """
    
    def __init__(self):
        """Initialize Azure OpenAI clients"""
        logger.info("🔷 Initializing Azure OpenAI provider")
        
        # Embeddings client
        self.embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_deployment=settings.AZURE_EMBEDDING_DEPLOYMENT,
        )
        
        # Chat client
        self.chat = AzureChatOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_deployment=settings.AZURE_CHAT_DEPLOYMENT,
            temperature=settings.RAG_TEMPERATURE,
            max_tokens=settings.RAG_MAX_TOKENS,
        )
        
        logger.info(f"✅ Azure OpenAI initialized: {settings.AZURE_OPENAI_ENDPOINT}")
    
    async def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for single text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (1536 dimensions for text-embedding-3-small)
        """
        try:
            logger.debug(f"Generating embedding for text ({len(text)} chars)")
            embedding = await self.embeddings.aembed_query(text)
            logger.debug(f"✅ Generated embedding: {len(embedding)} dimensions")
            return embedding
        except Exception as e:
            logger.error(f"❌ Failed to generate embedding: {e}")
            raise
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            logger.info(f"📦 Generating embeddings for {len(texts)} texts")
            embeddings = await self.embeddings.aembed_documents(texts)
            logger.info(f"✅ Generated {len(embeddings)} embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"❌ Failed to generate batch embeddings: {e}")
            raise
    
    async def get_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Get chat completion from Azure OpenAI
        
        Args:
            messages: Chat messages [{"role": "user", "content": "..."}]
            temperature: Override temperature
            max_tokens: Override max tokens
            
        Returns:
            LLM response text
        """
        try:
            logger.debug(f"Getting chat completion ({len(messages)} messages)")
            
            # Update parameters if provided
            if temperature is not None:
                self.chat.temperature = temperature
            if max_tokens is not None:
                self.chat.max_tokens = max_tokens
            
            response = await self.chat.ainvoke(messages)
            logger.debug(f"✅ Chat completion received ({len(response.content)} chars)")
            return response.content
        except Exception as e:
            logger.error(f"❌ Failed to get chat completion: {e}")
            raise
    
    async def get_rag_response(
        self,
        query: str,
        context_chunks: List[str],
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate RAG response using context chunks
        
        Args:
            query: User's question
            context_chunks: Retrieved relevant text chunks
            temperature: Override temperature
            
        Returns:
            Generated answer with context
        """
        try:
            logger.info(f"🤖 Generating RAG response for query: '{query[:50]}...'")
            logger.info(f"📚 Using {len(context_chunks)} context chunks")
            
            # Combine context chunks
            context = "\n\n---\n\n".join(context_chunks)
            
            # Create RAG prompt
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", """You are a helpful AI assistant that answers questions based on the provided context.

Instructions:
- Answer the question using ONLY the information from the context provided
- If the context doesn't contain enough information to answer, say "I don't have enough information to answer this question"
- Be concise and accurate
- Cite specific parts of the context when possible
- If you quote from the context, use quotation marks

Context:
{context}"""),
                ("user", "{query}")
            ])
            
            # Format messages
            messages = prompt_template.format_messages(
                context=context,
                query=query
            )
            
            # Get completion
            if temperature is not None:
                self.chat.temperature = temperature
            
            response = await self.chat.ainvoke(messages)
            
            logger.info(f"✅ RAG response generated ({len(response.content)} chars)")
            return response.content
            
        except Exception as e:
            logger.error(f"❌ Failed to generate RAG response: {e}")
            raise

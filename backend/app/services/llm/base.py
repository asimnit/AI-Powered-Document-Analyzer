"""
Base LLM Provider Interface

Abstract base class for all LLM providers.
Defines the contract that all providers must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers
    
    All providers (Azure, OpenAI, Ollama, etc.) must implement these methods
    """
    
    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        pass
    
    @abstractmethod
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        pass
    
    @abstractmethod
    async def get_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Get chat completion from LLM
        
        Args:
            messages: List of chat messages [{"role": "user", "content": "..."}]
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            
        Returns:
            LLM response text
        """
        pass
    
    @abstractmethod
    async def get_rag_response(
        self,
        query: str,
        context_chunks: List[str],
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate RAG (Retrieval-Augmented Generation) response
        
        Args:
            query: User's question
            context_chunks: Retrieved relevant text chunks
            temperature: Sampling temperature
            
        Returns:
            Generated answer with context
        """
        pass

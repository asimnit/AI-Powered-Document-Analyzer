"""
LLM Service Layer

Multi-provider abstraction for LLM operations:
- Embeddings generation
- Chat completions
- RAG responses
"""

from app.services.llm.factory import get_llm_provider

__all__ = ["get_llm_provider"]

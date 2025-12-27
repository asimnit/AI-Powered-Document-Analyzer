"""
LLM Provider Factory

Factory pattern for creating LLM provider instances based on configuration
"""

import logging
from app.services.llm.base import BaseLLMProvider
from app.services.llm.azure_provider import AzureOpenAIProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_llm_provider() -> BaseLLMProvider:
    """
    Get LLM provider instance based on configuration
    
    Returns:
        BaseLLMProvider instance (Azure, OpenAI, Ollama, etc.)
        
    Raises:
        ValueError: If provider is not supported
    """
    provider_name = settings.LLM_PROVIDER.lower()
    
    logger.info(f"🏭 Creating LLM provider: {provider_name}")
    
    if provider_name == "azure":
        return AzureOpenAIProvider()
    # Future providers:
    # elif provider_name == "openai":
    #     return OpenAIProvider()
    # elif provider_name == "ollama":
    #     return OllamaProvider()
    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider_name}. "
            f"Supported providers: azure"
        )

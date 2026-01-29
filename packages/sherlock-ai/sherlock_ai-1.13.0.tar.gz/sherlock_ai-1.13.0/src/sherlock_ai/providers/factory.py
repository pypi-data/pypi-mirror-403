"""
LLM provider factory
"""

import os
import logging
import warnings
from typing import Optional
from .base import LLMProvider

logger = logging.getLogger("LLMProviderLogger")

_provider_instance: Optional[LLMProvider] = None

def get_provider() -> LLMProvider:
    """
    Get the configured LLM provider (singleton pattern).
    
    Uses LLM_PROVIDER environment variable to determine which provider to use.
    Defaults to 'groq' if not set.
    
    Supported values:
        - 'groq' (default)
        - 'azure_openai'
    
    Returns:
        LLMProvider: The configured provider instance
    """
    global _provider_instance
    
    if _provider_instance is None:
        provider_type = os.getenv("LLM_PROVIDER", "groq").lower()
        
        logger.info(f"Initializing LLM provider: {provider_type}")
        
        if provider_type == "azure_openai":
            from .azure_openai_provider import AzureOpenAIProvider
            _provider_instance = AzureOpenAIProvider()
        elif provider_type == "groq":
            from .groq_provider import GroqProvider
            _provider_instance = GroqProvider()
        else:
            warnings.warn(f"Invalid LLM provider: {provider_type}. Supported providers: azure_openai, groq", UserWarning)
            raise ValueError(f"Invalid LLM provider: {provider_type}. Supported providers: azure_openai, groq")
    
    return _provider_instance


def reset_provider() -> None:
    """Reset the provider instance (useful for testing)"""
    global _provider_instance
    _provider_instance = None
"""
Base class for LLM providers
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """Whether the provider is properly configured"""
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """The default model to use"""
        pass
    
    @property
    @abstractmethod
    def analysis_model(self) -> str:
        """The model to use for code analysis"""
        pass

    @abstractmethod
    def chat_completion(
        self, 
        messages: List[Dict[str, Any]], 
        model: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """Send a chat completion request to the provider
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Optional model override (uses default_model if not provided)
            **kwargs: Additional arguments (max_tokens, temperature, etc.)
        
        Returns:
            The response content string, or None if failed
        """
        pass
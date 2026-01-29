"""
Groq LLM provider implementation
"""

from groq import Groq
import os
import warnings
import logging
from typing import Optional, List, Dict, Any
from .base import LLMProvider

logger = logging.getLogger("LLMProviderLogger")

class GroqProvider(LLMProvider):
    # Centralized model configuration
    DEFAULT_MODEL = "openai/gpt-oss-20b"
    ANALYSIS_MODEL = "openai/gpt-oss-20b"  # For code analysis/constant naming
    def __init__(self, api_key: Optional[str] = None):
        """
        api_key: Groq API key (optional). 
        If not provided, LLM-powered features will be disabled.
        """
        self.api_key = api_key or (os.getenv("GROQ_API_KEY") if os.getenv("GROQ_API_KEY") else None)
        self._client = None
        self._enabled = False

        if self.api_key:
            self._client = Groq(api_key=self.api_key)
            self._enabled = True
            # print("✅ Groq API enabled for LLM-powered insights.")
        else:
            # Show warning to user
            warnings.warn(
                "GROQ_API_KEY not configured. LLM-powered features (error insights, "
                "performance analysis, code reviews) will be disabled. "
                "Set GROQ_API_KEY environment variable to enable AI features.",
                UserWarning,
            )

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def default_model(self):
        return self.DEFAULT_MODEL

    @property
    def analysis_model(self):
        return self.ANALYSIS_MODEL

    @property
    def client(self):
        """
        Direct client access for backward compatibility
        """
        return self._client

    def chat_completion(
        self, 
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        if not self._enabled:
            return None

        try:
            response = self._client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in Groq chat completion: {e}")
            return None
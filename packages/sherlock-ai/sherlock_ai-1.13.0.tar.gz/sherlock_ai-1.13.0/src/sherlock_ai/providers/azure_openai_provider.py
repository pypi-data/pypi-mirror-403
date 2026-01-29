"""
Azure OpenAI LLM provider implementation
"""

from openai import AzureOpenAI
import os
import warnings
import logging
from typing import Optional, List, Dict, Any
from .base import LLMProvider

logger = logging.getLogger("LLMProviderLogger")

class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI LLM provider implementation"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        api_version: Optional[str] = None,
        deployment_name: Optional[str] = None
    ):
        self._api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self._endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self._api_version = api_version or os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        self._deployment_name = deployment_name or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        
        self._client = None
        self._enabled = False
        
        if self._api_key and self._endpoint and self._deployment_name:
            self._client = AzureOpenAI(
                api_key=self._api_key,
                api_version=self._api_version,
                azure_endpoint=self._endpoint
            )
            self._enabled = True
        else:
            missing = []
            if not self._api_key:
                missing.append("AZURE_OPENAI_API_KEY")
            if not self._endpoint:
                missing.append("AZURE_OPENAI_ENDPOINT")
            if not self._deployment_name:
                missing.append("AZURE_OPENAI_DEPLOYMENT_NAME")
            
            warnings.warn(
                f"Azure OpenAI not configured. Missing: {', '.join(missing)}. "
                "LLM-powered features will be disabled.",
                UserWarning
            )
            raise ValueError(f"Azure OpenAI not configured. Missing: {', '.join(missing)}. Set the environment variables to enable Azure OpenAI.")
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    @property
    def default_model(self) -> str:
        return self._deployment_name or ""
    
    @property
    def analysis_model(self) -> str:
        return self._deployment_name or ""
    
    @property
    def client(self):
        """Direct client access for backward compatibility"""
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
            logger.error(f"Azure OpenAI API error: {e}")
            return None
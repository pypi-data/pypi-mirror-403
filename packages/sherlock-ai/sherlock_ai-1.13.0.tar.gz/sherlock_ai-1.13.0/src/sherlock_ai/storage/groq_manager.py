from groq import Groq
import os
import warnings

class GroqManager:
    # Centralized model configuration
    DEFAULT_MODEL = "openai/gpt-oss-20b"
    ANALYSIS_MODEL = "openai/gpt-oss-20b"  # For code analysis/constant naming
    def __init__(self, api_key=None):
        """
        api_key: Groq API key (optional). 
        If not provided, LLM-powered features will be disabled.
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
            self.enabled = True
            # print("✅ Groq API enabled for LLM-powered insights.")
        else:
            self.client = None
            self.enabled = False
            # Show warning to user
            warnings.warn(
                "GROQ_API_KEY not configured. LLM-powered features (error insights, "
                "performance analysis, code reviews) will be disabled. "
                "Set GROQ_API_KEY environment variable to enable AI features.",
                UserWarning,
                # stacklevel=2
            )

    def get_client(self):
        """
        Returns the Groq client if enabled, otherwise None.
        """
        return self.client if self.enabled else None

    @property
    def default_model(self):
        return self.DEFAULT_MODEL

    @property
    def analysis_model(self):
        return self.ANALYSIS_MODEL
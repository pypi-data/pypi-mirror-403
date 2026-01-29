import inspect
import functools
from typing import Callable, TypeVar, Any, Union
from groq import Groq
import os
import logging
import asyncio
from ..storage import GroqManager

# Type variable for better type hints
F = TypeVar("F", bound=Callable[..., Any])

# Set up logging
logger = logging.getLogger("MonitoringLogger")

# Initialize GroqManager once at module level
groq_manager = GroqManager()

def smart_check(func: F = None) -> Union[F, Callable[[F], F]]:
    def decorator(f: F) -> F:
        @functools.wraps(f)
        async def async_wrapper(*args, **kwargs):
            if not groq_manager.enabled:
                return await f(*args, **kwargs)
            # Get the source code of the function
            try:
                source_code = inspect.getsource(f)

                # Send to LLM for analysis
                response = groq_manager.client.chat.completions.create(
                    model=groq_manager.default_model,
                    messages=[
                        {"role": "system", "content": "You're a helpful code reviewer. Suggest improvements related to config management and type safety. Also keep the suggest short and concise"},
                        {"role": "user", "content": f"Here's a Python function:\n\n{source_code}\n\nPlease suggest improvements."}
                    ]
                )

                # Print the LLM's suggestions
                suggestions = response.choices[0].message.content
                logger.info(f"LLM Suggestions: {suggestions}")
            except Exception as e:
                logger.error(f"Error in LLM call for code analysis: {e}")

            # Continue with the original function
            return await f(*args, **kwargs)

        @functools.wraps(f)
        def sync_wrapper(*args, **kwargs):
            if not groq_manager.enabled:
                return f(*args, **kwargs)
            
            try:
                # Get the source code of the function
                source_code = inspect.getsource(f)

                # Send to LLM for analysis
                response = groq_manager.client.chat.completions.create(
                    model=groq_manager.default_model,
                    messages=[
                        {"role": "system", "content": "You're a helpful code reviewer. Suggest improvements related to config management and type safety. Also keep the suggest short and concise"},
                        {"role": "user", "content": f"Here's a Python function:\n\n{source_code}\n\nPlease suggest improvements."}
                    ]
                )

                # Print the LLM's suggestions - FIXED logging
                suggestions = response.choices[0].message.content
                logger.info(f"LLM Suggestions:{suggestions}")
            except Exception as e:
                logger.error(f"Error in LLM call for code analysis: {e}")

            # Continue with the original function - NO await for sync
            return f(*args, **kwargs)
        
        # Return the appropriate wrapper based on function type
        return async_wrapper if asyncio.iscoroutinefunction(f) else sync_wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)

"""
LLM Adapters Package
Provides Strategy pattern implementation for different LLM backends
"""

from .base import BaseLLMAdapter, LLMResponse, LLMConfig
from .base import LLMAdapterError, LLMTimeoutError, LLMConnectionError, LLMModelError, LLMAuthError
from .ollama_adapter import OllamaAdapter
from .openai_adapter import OpenAIAdapter
from .factory import LLMAdapterFactory, create_adapter, create_adapter_from_env

__all__ = [
    'BaseLLMAdapter',
    'LLMResponse',
    'LLMConfig',
    'LLMAdapterError',
    'LLMTimeoutError',
    'LLMConnectionError',
    'LLMModelError',
    'LLMAuthError',
    'OllamaAdapter',
    'OpenAIAdapter',
    'LLMAdapterFactory',
    'create_adapter',
    'create_adapter_from_env'
]
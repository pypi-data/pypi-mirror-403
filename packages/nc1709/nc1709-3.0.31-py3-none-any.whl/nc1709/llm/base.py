"""
Base LLM Adapter Interface
Defines the contract for all LLM adapters using Strategy pattern
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional, Union
from dataclasses import dataclass
import time


@dataclass
class LLMResponse:
    """Standardized response from any LLM adapter"""
    content: str
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    duration: Optional[float] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class LLMConfig:
    """Configuration for LLM adapters"""
    model: str
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    timeout: float = 300.0
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    extra_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extra_params is None:
            self.extra_params = {}


class BaseLLMAdapter(ABC):
    """
    Base class for all LLM adapters
    
    This implements the Strategy pattern, allowing the agent to work
    with different LLM backends through a common interface.
    """
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.model_name = config.model
        self._client = None
        
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]]) -> LLMResponse:
        """
        Send chat messages to the LLM
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            
        Returns:
            LLMResponse with the model's response
        """
        pass
    
    @abstractmethod
    async def complete(self, prompt: str) -> LLMResponse:
        """
        Complete a text prompt
        
        Args:
            prompt: Text prompt to complete
            
        Returns:
            LLMResponse with the completion
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the LLM service is healthy
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model
        
        Returns:
            Dictionary with model information
        """
        pass
    
    def __call__(self, prompt: str) -> str:
        """
        Sync wrapper for compatibility with existing code.

        This allows the adapter to be used as a simple callable.
        Handles both cases: called from sync context and called from async context.
        """
        import asyncio

        try:
            # Check if we're already in an async context
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop - safe to use asyncio.run()
            loop = None

        if loop is None:
            # We're in a sync context, use asyncio.run()
            response = asyncio.run(self.complete(prompt))
            return response.content
        else:
            # We're already in an async context - use thread pool
            import concurrent.futures

            def run_in_new_loop():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(self.complete(prompt))
                finally:
                    new_loop.close()

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_in_new_loop)
                response = future.result()
                return response.content
    
    async def stream_chat(self, messages: List[Dict[str, str]]) -> AsyncIterator[str]:
        """
        Stream chat responses (optional, not all adapters support this)
        
        Args:
            messages: List of message dicts
            
        Yields:
            Chunks of the response as they arrive
        """
        # Default implementation: just return the full response
        response = await self.chat(messages)
        yield response.content
    
    def close(self) -> None:
        """Clean up resources"""
        if self._client:
            try:
                if hasattr(self._client, 'close'):
                    self._client.close()
                elif hasattr(self._client, 'aclose'):
                    import asyncio
                    asyncio.run(self._client.aclose())
            except Exception:
                pass  # Ignore cleanup errors
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()


class LLMAdapterError(Exception):
    """Base exception for LLM adapter errors"""
    
    def __init__(self, message: str, adapter_type: str = None, model: str = None):
        super().__init__(message)
        self.adapter_type = adapter_type
        self.model = model


class LLMTimeoutError(LLMAdapterError):
    """LLM request timeout"""
    pass


class LLMConnectionError(LLMAdapterError):
    """LLM connection error"""
    pass


class LLMModelError(LLMAdapterError):
    """LLM model not found or unavailable"""
    pass


class LLMAuthError(LLMAdapterError):
    """LLM authentication error"""
    pass
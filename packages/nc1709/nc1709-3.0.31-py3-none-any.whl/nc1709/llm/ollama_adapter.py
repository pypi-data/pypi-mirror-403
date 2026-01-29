"""
Ollama LLM Adapter
Implements the LLM adapter interface for Ollama models
"""

import json
import time
import asyncio
from typing import Any, Dict, List, Optional, AsyncIterator
import httpx

from .base import (
    BaseLLMAdapter, LLMResponse, LLMConfig, 
    LLMAdapterError, LLMTimeoutError, LLMConnectionError, LLMModelError
)


class OllamaAdapter(BaseLLMAdapter):
    """Adapter for Ollama LLM service"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url or "http://localhost:11434"
        self.base_url = self.base_url.rstrip('/')
        
        # Initialize async HTTP client
        self._client = None
        
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout),
                limits=httpx.Limits(max_connections=10)
            )
        return self._client
    
    async def chat(self, messages: List[Dict[str, str]]) -> LLMResponse:
        """Send chat messages to Ollama"""
        start_time = time.time()
        
        try:
            client = await self._get_client()
            
            # Ollama chat API format
            payload = {
                "model": self.config.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                    **(self.config.extra_params or {})
                }
            }
            
            if self.config.max_tokens:
                payload["options"]["num_predict"] = self.config.max_tokens
            
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            
            if response.status_code == 404:
                raise LLMModelError(f"Model '{self.config.model}' not found in Ollama")
            elif response.status_code != 200:
                raise LLMConnectionError(f"Ollama request failed: {response.status_code} {response.text}")
            
            result = response.json()
            duration = time.time() - start_time
            
            return LLMResponse(
                content=result.get("message", {}).get("content", ""),
                model=self.config.model,
                duration=duration,
                tokens_used=result.get("eval_count", 0) + result.get("prompt_eval_count", 0),
                prompt_tokens=result.get("prompt_eval_count", 0),
                completion_tokens=result.get("eval_count", 0),
                metadata={
                    "eval_duration": result.get("eval_duration", 0),
                    "prompt_eval_duration": result.get("prompt_eval_duration", 0),
                    "total_duration": result.get("total_duration", 0),
                    "load_duration": result.get("load_duration", 0)
                }
            )
            
        except httpx.TimeoutException:
            raise LLMTimeoutError(f"Ollama request timed out after {self.config.timeout}s")
        except httpx.ConnectError:
            raise LLMConnectionError(f"Could not connect to Ollama at {self.base_url}")
        except json.JSONDecodeError as e:
            raise LLMAdapterError(f"Invalid JSON response from Ollama: {e}")
        except Exception as e:
            if isinstance(e, (LLMAdapterError, LLMTimeoutError, LLMConnectionError, LLMModelError)):
                raise
            raise LLMAdapterError(f"Unexpected error calling Ollama: {e}")
    
    async def complete(self, prompt: str) -> LLMResponse:
        """Complete a text prompt using Ollama generate API"""
        start_time = time.time()
        
        try:
            client = await self._get_client()
            
            payload = {
                "model": self.config.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                    **(self.config.extra_params or {})
                }
            }
            
            if self.config.max_tokens:
                payload["options"]["num_predict"] = self.config.max_tokens
            
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            
            if response.status_code == 404:
                raise LLMModelError(f"Model '{self.config.model}' not found in Ollama")
            elif response.status_code != 200:
                raise LLMConnectionError(f"Ollama request failed: {response.status_code} {response.text}")
            
            result = response.json()
            duration = time.time() - start_time
            
            return LLMResponse(
                content=result.get("response", ""),
                model=self.config.model,
                duration=duration,
                tokens_used=result.get("eval_count", 0) + result.get("prompt_eval_count", 0),
                prompt_tokens=result.get("prompt_eval_count", 0),
                completion_tokens=result.get("eval_count", 0),
                metadata={
                    "eval_duration": result.get("eval_duration", 0),
                    "prompt_eval_duration": result.get("prompt_eval_duration", 0),
                    "total_duration": result.get("total_duration", 0),
                    "load_duration": result.get("load_duration", 0),
                    "done": result.get("done", False)
                }
            )
            
        except httpx.TimeoutException:
            raise LLMTimeoutError(f"Ollama request timed out after {self.config.timeout}s")
        except httpx.ConnectError:
            raise LLMConnectionError(f"Could not connect to Ollama at {self.base_url}")
        except json.JSONDecodeError as e:
            raise LLMAdapterError(f"Invalid JSON response from Ollama: {e}")
        except Exception as e:
            if isinstance(e, (LLMAdapterError, LLMTimeoutError, LLMConnectionError, LLMModelError)):
                raise
            raise LLMAdapterError(f"Unexpected error calling Ollama: {e}")
    
    async def stream_chat(self, messages: List[Dict[str, str]]) -> AsyncIterator[str]:
        """Stream chat responses from Ollama"""
        try:
            client = await self._get_client()
            
            payload = {
                "model": self.config.model,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": self.config.temperature,
                    **(self.config.extra_params or {})
                }
            }
            
            if self.config.max_tokens:
                payload["options"]["num_predict"] = self.config.max_tokens
            
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                
                if response.status_code == 404:
                    raise LLMModelError(f"Model '{self.config.model}' not found in Ollama")
                elif response.status_code != 200:
                    raise LLMConnectionError(f"Ollama stream failed: {response.status_code}")
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                content = data["message"]["content"]
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue  # Skip invalid lines
                            
        except httpx.TimeoutException:
            raise LLMTimeoutError(f"Ollama stream timed out after {self.config.timeout}s")
        except httpx.ConnectError:
            raise LLMConnectionError(f"Could not connect to Ollama at {self.base_url}")
        except Exception as e:
            if isinstance(e, (LLMAdapterError, LLMTimeoutError, LLMConnectionError, LLMModelError)):
                raise
            raise LLMAdapterError(f"Unexpected error in Ollama stream: {e}")
    
    async def health_check(self) -> bool:
        """Check if Ollama service is healthy"""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current Ollama model"""
        return {
            "adapter": "ollama",
            "model": self.config.model,
            "base_url": self.base_url,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "timeout": self.config.timeout
        }
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models in Ollama"""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/api/tags")
            
            if response.status_code != 200:
                raise LLMConnectionError(f"Failed to list models: {response.status_code}")
            
            result = response.json()
            return result.get("models", [])
            
        except httpx.TimeoutException:
            raise LLMTimeoutError("Ollama list models timed out")
        except httpx.ConnectError:
            raise LLMConnectionError(f"Could not connect to Ollama at {self.base_url}")
        except Exception as e:
            raise LLMAdapterError(f"Failed to list Ollama models: {e}")
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull a model in Ollama"""
        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name}
            )
            return response.status_code == 200
        except Exception:
            return False
    
    async def aclose(self) -> None:
        """Async close the HTTP client - preferred method"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def close(self) -> None:
        """
        Sync close the HTTP client.
        Note: Prefer aclose() in async contexts for proper cleanup.
        """
        if self._client and not self._client.is_closed:
            try:
                # Try to get running loop
                loop = asyncio.get_running_loop()
                # Schedule cleanup without blocking
                loop.create_task(self._client.aclose())
            except RuntimeError:
                # No running loop - run synchronously
                try:
                    asyncio.run(self._client.aclose())
                except RuntimeError:
                    # Can't create new loop, just mark as None
                    pass
            self._client = None

    def __del__(self) -> None:
        """Cleanup on garbage collection"""
        if self._client and not self._client.is_closed:
            try:
                self.close()
            except Exception:
                pass  # Ignore cleanup errors in destructor
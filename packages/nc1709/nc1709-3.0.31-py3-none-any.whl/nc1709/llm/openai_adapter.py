"""
OpenAI LLM Adapter
Implements the LLM adapter interface for OpenAI models
"""

import json
import time
import asyncio
from typing import Any, Dict, List, Optional, AsyncIterator
import httpx

from .base import (
    BaseLLMAdapter, LLMResponse, LLMConfig,
    LLMAdapterError, LLMTimeoutError, LLMConnectionError, LLMModelError, LLMAuthError
)


class OpenAIAdapter(BaseLLMAdapter):
    """Adapter for OpenAI GPT models"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        
        if not config.api_key:
            raise LLMAuthError("OpenAI API key is required")
        
        self.api_key = config.api_key
        self.base_url = config.base_url or "https://api.openai.com/v1"
        self.base_url = self.base_url.rstrip('/')
        
        # Initialize async HTTP client
        self._client = None
        
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client with auth headers"""
        if self._client is None or self._client.is_closed:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout),
                limits=httpx.Limits(max_connections=10),
                headers=headers
            )
        return self._client
    
    async def chat(self, messages: List[Dict[str, str]]) -> LLMResponse:
        """Send chat messages to OpenAI"""
        start_time = time.time()
        
        try:
            client = await self._get_client()
            
            # OpenAI chat completions API format
            payload = {
                "model": self.config.model,
                "messages": messages,
                "temperature": self.config.temperature,
                "stream": False,
                **(self.config.extra_params or {})
            }
            
            if self.config.max_tokens:
                payload["max_tokens"] = self.config.max_tokens
            
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            
            if response.status_code == 401:
                raise LLMAuthError("Invalid OpenAI API key")
            elif response.status_code == 404:
                raise LLMModelError(f"Model '{self.config.model}' not found")
            elif response.status_code == 429:
                raise LLMAdapterError("OpenAI rate limit exceeded")
            elif response.status_code != 200:
                error_detail = response.text
                try:
                    error_data = response.json()
                    error_detail = error_data.get("error", {}).get("message", error_detail)
                except:
                    pass
                raise LLMConnectionError(f"OpenAI request failed: {response.status_code} {error_detail}")
            
            result = response.json()
            duration = time.time() - start_time
            
            # Extract response content
            choice = result.get("choices", [{}])[0]
            content = choice.get("message", {}).get("content", "")
            
            # Extract usage information
            usage = result.get("usage", {})
            
            return LLMResponse(
                content=content,
                model=result.get("model", self.config.model),
                duration=duration,
                tokens_used=usage.get("total_tokens", 0),
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                metadata={
                    "finish_reason": choice.get("finish_reason"),
                    "system_fingerprint": result.get("system_fingerprint"),
                    "created": result.get("created"),
                    "id": result.get("id")
                }
            )
            
        except httpx.TimeoutException:
            raise LLMTimeoutError(f"OpenAI request timed out after {self.config.timeout}s")
        except httpx.ConnectError:
            raise LLMConnectionError(f"Could not connect to OpenAI at {self.base_url}")
        except json.JSONDecodeError as e:
            raise LLMAdapterError(f"Invalid JSON response from OpenAI: {e}")
        except Exception as e:
            if isinstance(e, (LLMAdapterError, LLMTimeoutError, LLMConnectionError, LLMModelError, LLMAuthError)):
                raise
            raise LLMAdapterError(f"Unexpected error calling OpenAI: {e}")
    
    async def complete(self, prompt: str) -> LLMResponse:
        """Complete a text prompt using OpenAI (converts to chat format)"""
        # Convert completion to chat format for modern OpenAI API
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages)
    
    async def stream_chat(self, messages: List[Dict[str, str]]) -> AsyncIterator[str]:
        """Stream chat responses from OpenAI"""
        try:
            client = await self._get_client()
            
            payload = {
                "model": self.config.model,
                "messages": messages,
                "temperature": self.config.temperature,
                "stream": True,
                **(self.config.extra_params or {})
            }
            
            if self.config.max_tokens:
                payload["max_tokens"] = self.config.max_tokens
            
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload
            ) as response:
                
                if response.status_code == 401:
                    raise LLMAuthError("Invalid OpenAI API key")
                elif response.status_code == 404:
                    raise LLMModelError(f"Model '{self.config.model}' not found")
                elif response.status_code != 200:
                    raise LLMConnectionError(f"OpenAI stream failed: {response.status_code}")
                
                async for line in response.aiter_lines():
                    line = line.strip()
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        
                        if data_str == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue  # Skip invalid lines
                            
        except httpx.TimeoutException:
            raise LLMTimeoutError(f"OpenAI stream timed out after {self.config.timeout}s")
        except httpx.ConnectError:
            raise LLMConnectionError(f"Could not connect to OpenAI at {self.base_url}")
        except Exception as e:
            if isinstance(e, (LLMAdapterError, LLMTimeoutError, LLMConnectionError, LLMModelError, LLMAuthError)):
                raise
            raise LLMAdapterError(f"Unexpected error in OpenAI stream: {e}")
    
    async def health_check(self) -> bool:
        """Check if OpenAI service is healthy"""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/models")
            return response.status_code == 200
        except Exception:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current OpenAI model"""
        return {
            "adapter": "openai",
            "model": self.config.model,
            "base_url": self.base_url,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "timeout": self.config.timeout,
            "has_api_key": bool(self.api_key)
        }
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models in OpenAI"""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/models")
            
            if response.status_code == 401:
                raise LLMAuthError("Invalid OpenAI API key")
            elif response.status_code != 200:
                raise LLMConnectionError(f"Failed to list models: {response.status_code}")
            
            result = response.json()
            return result.get("data", [])
            
        except httpx.TimeoutException:
            raise LLMTimeoutError("OpenAI list models timed out")
        except httpx.ConnectError:
            raise LLMConnectionError(f"Could not connect to OpenAI at {self.base_url}")
        except Exception as e:
            if isinstance(e, (LLMAdapterError, LLMTimeoutError, LLMConnectionError, LLMAuthError)):
                raise
            raise LLMAdapterError(f"Failed to list OpenAI models: {e}")
    
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
                loop = asyncio.get_running_loop()
                loop.create_task(self._client.aclose())
            except RuntimeError:
                try:
                    asyncio.run(self._client.aclose())
                except RuntimeError:
                    pass
            self._client = None

    def __del__(self) -> None:
        """Cleanup on garbage collection"""
        if self._client and not self._client.is_closed:
            try:
                self.close()
            except Exception:
                pass

    async def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto"
    ) -> LLMResponse:
        """
        Send chat messages with function calling support.

        Args:
            messages: Chat messages
            tools: List of tool schemas (OpenAI function format)
            tool_choice: "auto", "none", or {"type": "function", "function": {"name": "..."}}

        Returns:
            LLMResponse with tool calls in metadata if applicable
        """
        start_time = time.time()

        try:
            client = await self._get_client()

            payload = {
                "model": self.config.model,
                "messages": messages,
                "temperature": self.config.temperature,
                "stream": False,
                **(self.config.extra_params or {})
            }

            if self.config.max_tokens:
                payload["max_tokens"] = self.config.max_tokens

            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = tool_choice

            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )

            if response.status_code == 401:
                raise LLMAuthError("Invalid OpenAI API key")
            elif response.status_code == 404:
                raise LLMModelError(f"Model '{self.config.model}' not found")
            elif response.status_code == 429:
                raise LLMAdapterError("OpenAI rate limit exceeded")
            elif response.status_code != 200:
                error_detail = response.text
                try:
                    error_data = response.json()
                    error_detail = error_data.get("error", {}).get("message", error_detail)
                except:
                    pass
                raise LLMConnectionError(f"OpenAI request failed: {response.status_code} {error_detail}")

            result = response.json()
            duration = time.time() - start_time

            choice = result.get("choices", [{}])[0]
            message = choice.get("message", {})
            content = message.get("content", "")
            tool_calls = message.get("tool_calls", [])

            usage = result.get("usage", {})

            return LLMResponse(
                content=content,
                model=result.get("model", self.config.model),
                duration=duration,
                tokens_used=usage.get("total_tokens", 0),
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                metadata={
                    "finish_reason": choice.get("finish_reason"),
                    "tool_calls": tool_calls,
                    "system_fingerprint": result.get("system_fingerprint"),
                    "created": result.get("created"),
                    "id": result.get("id")
                }
            )

        except httpx.TimeoutException:
            raise LLMTimeoutError(f"OpenAI request timed out after {self.config.timeout}s")
        except httpx.ConnectError:
            raise LLMConnectionError(f"Could not connect to OpenAI at {self.base_url}")
        except Exception as e:
            if isinstance(e, (LLMAdapterError, LLMTimeoutError, LLMConnectionError, LLMModelError, LLMAuthError)):
                raise
            raise LLMAdapterError(f"Unexpected error calling OpenAI: {e}")


class AzureOpenAIAdapter(OpenAIAdapter):
    """Adapter for Azure OpenAI Service"""
    
    def __init__(self, config: LLMConfig):
        # Azure OpenAI requires additional configuration
        if not config.base_url:
            raise LLMAdapterError("Azure OpenAI requires base_url to be set")
        
        # Extract deployment name and API version
        self.deployment_name = config.extra_params.get("deployment_name") or config.model
        self.api_version = config.extra_params.get("api_version", "2023-12-01-preview")
        
        super().__init__(config)
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get client with Azure-specific auth"""
        if self._client is None or self._client.is_closed:
            headers = {
                "api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout),
                limits=httpx.Limits(max_connections=10),
                headers=headers
            )
        return self._client
    
    async def chat(self, messages: List[Dict[str, str]]) -> LLMResponse:
        """Send chat messages to Azure OpenAI"""
        # Override URL for Azure format
        original_base = self.base_url
        self.base_url = f"{self.base_url}/openai/deployments/{self.deployment_name}"
        
        try:
            response = await super().chat(messages)
            response.metadata["deployment"] = self.deployment_name
            response.metadata["api_version"] = self.api_version
            return response
        finally:
            self.base_url = original_base
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Azure OpenAI model info"""
        info = super().get_model_info()
        info.update({
            "adapter": "azure_openai",
            "deployment_name": self.deployment_name,
            "api_version": self.api_version
        })
        return info
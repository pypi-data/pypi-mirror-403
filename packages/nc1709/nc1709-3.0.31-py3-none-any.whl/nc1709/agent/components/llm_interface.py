"""
LLM Interface Component
Handles all interactions with the language model using adapter pattern
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union
from dataclasses import dataclass
import asyncio

if TYPE_CHECKING:
    from ..core import AgentConfig

# Import LLM adapters
try:
    from ...llm import BaseLLMAdapter, LLMAdapterFactory, create_adapter_from_env
    from ...llm.base import LLMResponse as AdapterLLMResponse
    HAS_ADAPTERS = True
except ImportError:
    HAS_ADAPTERS = False


@dataclass  
class LLMResponse:
    """Structured response from LLM (legacy compatibility)"""
    content: str
    tokens_used: Optional[int] = None
    model: Optional[str] = None
    duration: Optional[float] = None


class LLMInterface:
    """Handles all LLM interactions for the agent using adapter pattern"""
    
    def __init__(self, config: 'AgentConfig'):
        self.config = config
        self.conversation_history: List[Dict[str, str]] = []
        
        # Initialize LLM adapter or fallback to legacy interface
        self.adapter = None
        self.legacy_llm = None
        
        self._setup_llm_interface()
    
    def _setup_llm_interface(self):
        """Setup LLM interface (adapter or legacy)"""
        if HAS_ADAPTERS:
            try:
                # Try to create adapter from config
                if hasattr(self.config, 'llm_adapter_type') and self.config.llm_adapter_type:
                    adapter_config = {
                        'model': getattr(self.config, 'model', None),
                        'temperature': getattr(self.config, 'temperature', 0.1),
                        'max_tokens': getattr(self.config, 'max_tokens', None),
                        'timeout': getattr(self.config, 'timeout', 300.0)
                    }
                    
                    # Add adapter-specific config
                    if hasattr(self.config, 'llm_config'):
                        adapter_config.update(self.config.llm_config)
                    
                    self.adapter = LLMAdapterFactory.create_adapter(
                        self.config.llm_adapter_type,
                        **adapter_config
                    )
                else:
                    # Try to auto-detect from environment
                    self.adapter = create_adapter_from_env()
                    
            except Exception as e:
                print(f"⚠️ Failed to create LLM adapter: {e}")
                # Fall back to legacy interface
                self.legacy_llm = self.config.llm
        else:
            # Use legacy interface
            self.legacy_llm = self.config.llm
    
    def get_response(self, user_request: str, context: str = "") -> LLMResponse:
        """Get response from LLM with current conversation context"""
        import time
        start_time = time.time()
        
        # Build conversation context
        messages = self._build_message_context(user_request, context)
        
        try:
            if self.adapter:
                # Use new adapter interface
                adapter_response = self._get_adapter_response(messages)
                response_content = adapter_response.content
                duration = adapter_response.duration or (time.time() - start_time)
                model = adapter_response.model
                tokens = adapter_response.tokens_used
            else:
                # Use legacy interface
                response_content = self._get_legacy_response(messages)
                duration = time.time() - start_time
                model = getattr(self.legacy_llm, 'model_name', 'unknown')
                tokens = None
            
            # Add to conversation history
            self.conversation_history.append({
                "role": "user", 
                "content": user_request
            })
            self.conversation_history.append({
                "role": "assistant", 
                "content": response_content
            })
            
            return LLMResponse(
                content=response_content,
                duration=duration,
                model=model,
                tokens_used=tokens
            )
            
        except Exception as e:
            # Import custom exceptions if available
            try:
                from ...exceptions import ModelError
                raise ModelError(f"LLM request failed: {e}")
            except ImportError:
                raise RuntimeError(f"LLM request failed: {e}")
    
    def _get_adapter_response(self, messages: List[Dict[str, str]]) -> 'AdapterLLMResponse':
        """Get response using new adapter interface"""
        if asyncio.iscoroutinefunction(self.adapter.chat):
            # Async adapter
            try:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(self.adapter.chat(messages))
            except RuntimeError:
                # No event loop running
                return asyncio.run(self.adapter.chat(messages))
        else:
            # Sync adapter (shouldn't happen with current implementation)
            return self.adapter.chat(messages)
    
    def _get_legacy_response(self, messages: List[Dict[str, str]]) -> str:
        """Get response using legacy interface"""
        if hasattr(self.legacy_llm, 'chat') and callable(self.legacy_llm.chat):
            # Chat-based interface
            return self.legacy_llm.chat(messages)
        elif hasattr(self.legacy_llm, '__call__'):
            # Direct callable interface
            full_prompt = self._format_prompt_from_messages(messages)
            return self.legacy_llm(full_prompt)
        else:
            raise ValueError(f"Unsupported LLM interface: {type(self.legacy_llm)}")
    
    def _build_message_context(self, user_request: str, context: str = "") -> List[Dict[str, str]]:
        """Build message context for the LLM"""
        messages = []
        
        # System message
        system_content = self._get_system_message()
        if context:
            system_content += f"\n\nCurrent Context:\n{context}"
        
        messages.append({"role": "system", "content": system_content})
        
        # Add conversation history (keep last N messages to stay within context limits)
        max_history = getattr(self.config, 'max_conversation_history', 10)
        recent_history = self.conversation_history[-max_history:]
        messages.extend(recent_history)
        
        # Current user request
        messages.append({"role": "user", "content": user_request})
        
        return messages
    
    def _get_system_message(self) -> str:
        """Get the system message for the agent"""
        return """You are NC1709, an advanced AI coding assistant with 99% tool-calling accuracy.

You have access to various tools for file operations, searching, running commands, and more. When you need to perform actions, use the available tools by formatting your response with tool calls.

Tool Call Format:
```
<tool_name>
parameter1: value1
parameter2: value2
</tool_name>
```

Available capabilities:
- File operations (read, write, edit files)
- Search and grep operations  
- Bash command execution
- Web fetching and searches
- Notebook operations
- Task delegation to specialized agents

Always:
1. Use tools when you need to perform actions
2. Provide clear explanations of what you're doing
3. Handle errors gracefully
4. Be concise but thorough in your responses

When you encounter issues:
- Check your tool usage syntax
- Verify file paths and parameters
- Provide alternative approaches if initial attempts fail"""
    
    def _format_prompt_from_messages(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages to a single prompt string for non-chat LLMs"""
        prompt_parts = []
        
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "system":
                prompt_parts.append(f"System: {content}\n")
            elif role == "user":
                prompt_parts.append(f"User: {content}\n")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}\n")
        
        prompt_parts.append("Assistant: ")
        return "\n".join(prompt_parts)
    
    def clear_history(self) -> None:
        """Clear conversation history"""
        self.conversation_history.clear()
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history"""
        return self.conversation_history.copy()
    
    def add_context(self, context: str) -> None:
        """Add context to the conversation without a user message"""
        self.conversation_history.append({
            "role": "system",
            "content": f"Context update: {context}"
        })
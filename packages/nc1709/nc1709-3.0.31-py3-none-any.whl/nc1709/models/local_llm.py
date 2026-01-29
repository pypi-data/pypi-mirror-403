"""
Local LLM Adapter for ECHO
Manages local Ollama models with intelligent routing and performance optimization
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, AsyncGenerator
from enum import Enum
import json
import subprocess
import httpx
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class TaskCategory(Enum):
    """Categories of tasks for model routing"""
    REASONING = "reasoning"
    CODE_GENERATION = "code_generation"
    REFACTORING = "refactoring"
    DEBUGGING = "debugging"
    EXPLANATION = "explanation"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    QUICK_ANSWER = "quick_answer"
    GENERAL = "general"


class ModelTier(Enum):
    """Performance tiers for model selection"""
    INSTANT = "instant"    # <100ms target
    FAST = "fast"         # <2s target
    SMART = "smart"       # <10s target
    DEEP = "deep"         # Unlimited time


@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    name: str
    tier: ModelTier
    categories: List[TaskCategory]
    context_window: int
    temperature: float = 0.7
    max_tokens: Optional[int] = None


class LocalLLMAdapter:
    """
    Manages local LLM inference with Ollama
    Provides intelligent routing, caching, and performance optimization
    """
    
    # Model mapping for available local models
    MODEL_CONFIGS = {
        "deepseek-r1:32b": ModelConfig(
            name="deepseek-r1:32b",
            tier=ModelTier.DEEP,
            categories=[TaskCategory.REASONING, TaskCategory.DEBUGGING],
            context_window=32768,
            temperature=0.3
        ),
        "qwen2.5-coder:32b": ModelConfig(
            name="qwen2.5-coder:32b",
            tier=ModelTier.SMART,
            categories=[TaskCategory.CODE_GENERATION, TaskCategory.REFACTORING],
            context_window=32768,
            temperature=0.5
        ),
        "qwen2.5-coder:7b": ModelConfig(
            name="qwen2.5-coder:7b",
            tier=ModelTier.FAST,
            categories=[TaskCategory.QUICK_ANSWER, TaskCategory.DOCUMENTATION],
            context_window=8192,
            temperature=0.7
        ),
        "mixtral:8x7b": ModelConfig(
            name="mixtral:8x7b-instruct-v0.1-q4_K_M",
            tier=ModelTier.SMART,
            categories=[TaskCategory.GENERAL, TaskCategory.EXPLANATION],
            context_window=32768,
            temperature=0.7
        ),
    }
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        """Initialize the local LLM adapter"""
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=300.0)
        self._model_cache = {}
        self._performance_stats = {}
        self._initialize_models()
        
    def _initialize_models(self):
        """Check available models and warm them up"""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                available = set()
                for line in lines:
                    if line:
                        parts = line.split()
                        if parts:
                            available.add(parts[0])
                
                # Update configs based on what's actually available
                self.available_models = {}
                for model_id, config in self.MODEL_CONFIGS.items():
                    if any(config.name in avail for avail in available):
                        self.available_models[model_id] = config
                        logger.info(f"✓ Model available: {model_id}")
                    else:
                        logger.warning(f"✗ Model not found: {model_id}")
                        
        except Exception as e:
            logger.error(f"Failed to check models: {e}")
            self.available_models = self.MODEL_CONFIGS
    
    def select_model(self, 
                     task_category: TaskCategory,
                     complexity: float = 0.5,
                     time_constraint: Optional[float] = None) -> str:
        """
        Select the best model for the task
        
        Args:
            task_category: Type of task to perform
            complexity: Task complexity (0-1)
            time_constraint: Maximum time in seconds
            
        Returns:
            Model name to use
        """
        # Filter models by category
        suitable_models = [
            (model_id, config) 
            for model_id, config in self.available_models.items()
            if task_category in config.categories
        ]
        
        if not suitable_models:
            # Fallback to most capable model
            if "qwen2.5-coder:32b" in self.available_models:
                return "qwen2.5-coder:32b"
            return list(self.available_models.keys())[0]
        
        # Apply time constraint filtering
        if time_constraint:
            if time_constraint < 2:
                tier_filter = ModelTier.FAST
            elif time_constraint < 10:
                tier_filter = ModelTier.SMART
            else:
                tier_filter = ModelTier.DEEP
                
            suitable_models = [
                (m_id, cfg) for m_id, cfg in suitable_models
                if cfg.tier.value <= tier_filter.value
            ]
        
        # Select based on complexity
        if complexity > 0.7:
            # High complexity - use most capable model
            deepest = max(suitable_models, key=lambda x: x[1].tier.value)
            return deepest[0]
        elif complexity < 0.3:
            # Low complexity - use fastest model
            fastest = min(suitable_models, key=lambda x: x[1].tier.value)
            return fastest[0]
        else:
            # Medium complexity - balanced choice
            return suitable_models[0][0]
    
    async def generate(self,
                      prompt: str,
                      model: Optional[str] = None,
                      task_category: Optional[TaskCategory] = None,
                      stream: bool = True,
                      **kwargs) -> AsyncGenerator[str, None]:
        """
        Generate a response from local LLM
        
        Args:
            prompt: Input prompt
            model: Specific model to use (optional)
            task_category: Category of task for auto-routing
            stream: Whether to stream the response
            **kwargs: Additional parameters
            
        Yields:
            Response tokens as they're generated
        """
        # Select model if not specified
        if not model:
            if task_category:
                model = self.select_model(task_category, kwargs.get('complexity', 0.5))
            else:
                model = "qwen2.5-coder:7b"  # Default fast model
        
        # Get model config
        config = self.available_models.get(model, self.MODEL_CONFIGS.get(model))
        
        # Prepare request
        data = {
            "model": config.name,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": kwargs.get("temperature", config.temperature),
                "num_predict": kwargs.get("max_tokens", config.max_tokens or 4096),
                "num_ctx": min(len(prompt) + 2000, config.context_window),
            }
        }
        
        # Record start time for performance tracking
        start_time = time.time()
        tokens_generated = 0
        
        try:
            # Make request to Ollama
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json=data,
                timeout=300.0
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            if "response" in chunk:
                                tokens_generated += 1
                                yield chunk["response"]
                                
                            if chunk.get("done", False):
                                # Track performance stats
                                elapsed = time.time() - start_time
                                self._update_stats(model, elapsed, tokens_generated)
                                break
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"Generation error with {model}: {e}")
            # Fallback to simpler model if available
            if model != "qwen2.5-coder:7b" and "qwen2.5-coder:7b" in self.available_models:
                logger.info("Falling back to qwen2.5-coder:7b")
                async for token in self.generate(prompt, "qwen2.5-coder:7b", stream=stream):
                    yield token
            else:
                yield f"Error: {str(e)}"
    
    def _update_stats(self, model: str, elapsed: float, tokens: int):
        """Update performance statistics for a model"""
        if model not in self._performance_stats:
            self._performance_stats[model] = {
                "calls": 0,
                "total_time": 0,
                "total_tokens": 0,
                "avg_time": 0,
                "avg_tps": 0  # Tokens per second
            }
        
        stats = self._performance_stats[model]
        stats["calls"] += 1
        stats["total_time"] += elapsed
        stats["total_tokens"] += tokens
        stats["avg_time"] = stats["total_time"] / stats["calls"]
        if elapsed > 0:
            stats["avg_tps"] = tokens / elapsed
            
        logger.debug(f"Model {model}: {tokens} tokens in {elapsed:.2f}s ({stats['avg_tps']:.1f} t/s)")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for all models"""
        return self._performance_stats
    
    async def preload_model(self, model: str):
        """Preload a model into memory for faster first inference"""
        try:
            # Send a minimal request to load the model
            data = {
                "model": self.available_models[model].name,
                "prompt": "test",
                "options": {"num_predict": 1}
            }
            
            async with self.client.post(
                f"{self.base_url}/api/generate",
                json=data,
                timeout=60.0
            ) as response:
                response.raise_for_status()
                logger.info(f"Preloaded model: {model}")
                
        except Exception as e:
            logger.warning(f"Failed to preload {model}: {e}")
    
    async def close(self):
        """Clean up resources"""
        await self.client.aclose()
    
    def estimate_time(self, prompt_length: int, model: str, output_tokens: int = 500) -> float:
        """
        Estimate generation time based on model and lengths
        
        Args:
            prompt_length: Number of characters in prompt
            model: Model to use
            output_tokens: Expected output tokens
            
        Returns:
            Estimated time in seconds
        """
        if model in self._performance_stats:
            stats = self._performance_stats[model]
            if stats["avg_tps"] > 0:
                return output_tokens / stats["avg_tps"]
        
        # Default estimates based on model tier
        config = self.available_models.get(model)
        if config:
            tier_estimates = {
                ModelTier.INSTANT: 0.1,
                ModelTier.FAST: 2.0,
                ModelTier.SMART: 8.0,
                ModelTier.DEEP: 20.0
            }
            return tier_estimates.get(config.tier, 5.0)
        
        return 5.0  # Default estimate
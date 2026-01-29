"""
ECHO 2.0 - Local LLM Adapter with Latest 2025 Models
Optimized for the newest generation of models
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
    COMPLEX_ANALYSIS = "complex_analysis"
    ARCHITECTURE = "architecture"


class ModelTier(Enum):
    """Performance tiers for model selection"""
    INSTANT = "instant"    # <100ms target (Codestral)
    FAST = "fast"         # <2s target (Small models)
    SMART = "smart"       # <10s target (Medium models)
    DEEP = "deep"         # Unlimited time (Large models)
    ULTIMATE = "ultimate" # DeepSeek-V3 tier


@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    name: str
    tier: ModelTier
    categories: List[TaskCategory]
    context_window: int
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    strengths: List[str] = None


class LocalLLMAdapter:
    """
    ECHO 2.0 - Manages local LLM inference with latest 2025 models
    Provides intelligent routing, caching, and performance optimization
    """
    
    # Updated model mapping for 2025 models
    MODEL_CONFIGS = {
        # === NEW 2025 MODELS ===
        "deepseek-r1:latest": ModelConfig(
            name="deepseek-r1:latest",
            tier=ModelTier.DEEP,
            categories=[
                TaskCategory.REASONING, 
                TaskCategory.DEBUGGING,
                TaskCategory.COMPLEX_ANALYSIS,
                TaskCategory.ARCHITECTURE
            ],
            context_window=128000,
            temperature=0.3,
            strengths=["o1-style reasoning", "chain of thought", "complex problem solving"]
        ),
        
        "qwen3:latest": ModelConfig(
            name="qwen3:latest",
            tier=ModelTier.SMART,
            categories=[
                TaskCategory.CODE_GENERATION, 
                TaskCategory.REFACTORING,
                TaskCategory.GENERAL,
                TaskCategory.EXPLANATION
            ],
            context_window=128000,
            temperature=0.5,
            strengths=["multilingual", "92+ languages", "latest generation coding"]
        ),
        
        "codestral:latest": ModelConfig(
            name="codestral:latest",
            tier=ModelTier.INSTANT,
            categories=[
                TaskCategory.QUICK_ANSWER,
                TaskCategory.CODE_GENERATION,
                TaskCategory.DOCUMENTATION,
                TaskCategory.TESTING
            ],
            context_window=256000,  # 256K context!
            temperature=0.7,
            strengths=["ultra-fast", "80+ languages", "massive context window"]
        ),
        
        "llama3.3:70b": ModelConfig(
            name="llama3.3:70b",
            tier=ModelTier.SMART,
            categories=[
                TaskCategory.GENERAL,
                TaskCategory.EXPLANATION,
                TaskCategory.REFACTORING
            ],
            context_window=128000,
            temperature=0.7,
            strengths=["balanced", "high quality", "general purpose"]
        ),
        
        "deepseek-v3": ModelConfig(
            name="deepseek-v3",
            tier=ModelTier.ULTIMATE,
            categories=[
                TaskCategory.COMPLEX_ANALYSIS,
                TaskCategory.ARCHITECTURE,
                TaskCategory.REASONING
            ],
            context_window=128000,
            temperature=0.3,
            strengths=["GPT-4o rival", "best overall", "671B parameters"]
        ),
        
        # === LEGACY MODELS (kept for compatibility) ===
        "deepseek-r1:32b": ModelConfig(
            name="deepseek-r1:32b",
            tier=ModelTier.SMART,
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
    }
    
    # Model selection priority (ordered by preference)
    MODEL_PRIORITY = {
        TaskCategory.REASONING: ["deepseek-r1:latest", "deepseek-v3", "deepseek-r1:32b"],
        TaskCategory.CODE_GENERATION: ["qwen3:latest", "codestral:latest", "qwen2.5-coder:32b"],
        TaskCategory.QUICK_ANSWER: ["codestral:latest", "qwen2.5-coder:7b"],
        TaskCategory.DEBUGGING: ["deepseek-r1:latest", "qwen3:latest", "deepseek-r1:32b"],
        TaskCategory.ARCHITECTURE: ["deepseek-v3", "deepseek-r1:latest", "llama3.3:70b"],
        TaskCategory.GENERAL: ["llama3.3:70b", "qwen3:latest", "qwen2.5-coder:32b"],
    }
    
    def __init__(self, base_url: str = "http://localhost:11434", prefer_new_models: bool = True):
        """
        Initialize the local LLM adapter
        
        Args:
            base_url: Ollama API URL
            prefer_new_models: Whether to prefer 2025 models over legacy ones
        """
        self.base_url = base_url
        self.prefer_new_models = prefer_new_models
        self.client = httpx.AsyncClient(timeout=600.0)  # Increased timeout for large models
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
                            # Extract model name and tag
                            model_full = parts[0]
                            available.add(model_full)
                
                # Update configs based on what's actually available
                self.available_models = {}
                for model_id, config in self.MODEL_CONFIGS.items():
                    # Check if model or its base name is available
                    model_base = config.name.split(':')[0]
                    if config.name in available or any(model_base in avail for avail in available):
                        self.available_models[model_id] = config
                        
                        # Log with model strengths if it's a new model
                        if config.strengths:
                            logger.info(f"✓ {model_id} available - Strengths: {', '.join(config.strengths)}")
                        else:
                            logger.info(f"✓ Model available: {model_id}")
                    else:
                        logger.debug(f"✗ Model not found: {model_id}")
                
                # Log summary
                new_models = ["deepseek-r1:latest", "qwen3:latest", "codestral:latest", 
                             "llama3.3:70b", "deepseek-v3"]
                available_new = [m for m in new_models if m in self.available_models]
                logger.info(f"\n🚀 ECHO 2.0 Ready with {len(available_new)}/{len(new_models)} new 2025 models!")
                        
        except Exception as e:
            logger.error(f"Failed to check models: {e}")
            self.available_models = self.MODEL_CONFIGS
    
    def select_model(self, 
                     task_category: TaskCategory,
                     complexity: float = 0.5,
                     time_constraint: Optional[float] = None,
                     prefer_new: Optional[bool] = None) -> str:
        """
        Select the best model for the task using intelligent routing
        
        Args:
            task_category: Type of task to perform
            complexity: Task complexity (0-1)
            time_constraint: Maximum time in seconds
            prefer_new: Override default preference for new models
            
        Returns:
            Model name to use
        """
        if prefer_new is None:
            prefer_new = self.prefer_new_models
        
        # Check for category-specific priority
        if task_category in self.MODEL_PRIORITY:
            priority_list = self.MODEL_PRIORITY[task_category]
            for model in priority_list:
                if model in self.available_models:
                    # Check time constraint
                    config = self.available_models[model]
                    if time_constraint:
                        if time_constraint < 1 and config.tier not in [ModelTier.INSTANT, ModelTier.FAST]:
                            continue
                        elif time_constraint < 10 and config.tier in [ModelTier.DEEP, ModelTier.ULTIMATE]:
                            continue
                    return model
        
        # Fallback to complexity-based selection
        if complexity > 0.8:
            # Very complex - use most capable model
            if "deepseek-r1:latest" in self.available_models:
                return "deepseek-r1:latest"
            elif "deepseek-v3" in self.available_models:
                return "deepseek-v3"
        elif complexity < 0.3:
            # Simple - use fastest model
            if "codestral:latest" in self.available_models:
                return "codestral:latest"
            elif "qwen2.5-coder:7b" in self.available_models:
                return "qwen2.5-coder:7b"
        else:
            # Medium complexity - balanced choice
            if "qwen3:latest" in self.available_models:
                return "qwen3:latest"
            elif "llama3.3:70b" in self.available_models:
                return "llama3.3:70b"
        
        # Ultimate fallback
        return list(self.available_models.keys())[0] if self.available_models else "qwen2.5-coder:7b"
    
    async def generate(self,
                      prompt: str,
                      model: Optional[str] = None,
                      task_category: Optional[TaskCategory] = None,
                      stream: bool = True,
                      **kwargs) -> AsyncGenerator[str, None]:
        """
        Generate a response from local LLM with performance tracking
        
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
                model = self.select_model(
                    task_category, 
                    kwargs.get('complexity', 0.5),
                    kwargs.get('time_constraint')
                )
            else:
                model = "codestral:latest" if "codestral:latest" in self.available_models else "qwen2.5-coder:7b"
        
        # Get model config
        config = self.available_models.get(model, self.MODEL_CONFIGS.get(model))
        
        # Log model selection
        logger.debug(f"Selected model: {model} for {task_category.value if task_category else 'general'} task")
        
        # Prepare request with optimized parameters
        data = {
            "model": config.name,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": kwargs.get("temperature", config.temperature),
                "num_predict": kwargs.get("max_tokens", config.max_tokens or 4096),
                "num_ctx": min(len(prompt) + 4000, config.context_window),
                "num_thread": 8,  # Optimize CPU usage
                "num_gpu": 99,    # Use all available GPU layers
            }
        }
        
        # Add model-specific optimizations
        if "codestral" in config.name:
            # Codestral optimizations for speed
            data["options"]["repeat_penalty"] = 1.0
            data["options"]["top_k"] = 10
            data["options"]["top_p"] = 0.9
        elif "deepseek-r1" in config.name:
            # DeepSeek-R1 optimizations for reasoning
            data["options"]["repeat_penalty"] = 1.1
            data["options"]["top_k"] = 40
            data["options"]["top_p"] = 0.95
        
        # Record start time for performance tracking
        start_time = time.time()
        tokens_generated = 0
        time_to_first_token = None
        
        try:
            # Make request to Ollama
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json=data,
                timeout=600.0
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            if "response" in chunk:
                                if time_to_first_token is None:
                                    time_to_first_token = time.time() - start_time
                                tokens_generated += 1
                                yield chunk["response"]
                                
                            if chunk.get("done", False):
                                # Track performance stats
                                elapsed = time.time() - start_time
                                self._update_stats(
                                    model, elapsed, tokens_generated, 
                                    time_to_first_token or elapsed
                                )
                                break
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"Generation error with {model}: {e}")
            # Fallback to simpler model if available
            fallback = "codestral:latest" if "codestral:latest" in self.available_models else "qwen2.5-coder:7b"
            if model != fallback and fallback in self.available_models:
                logger.info(f"Falling back to {fallback}")
                async for token in self.generate(prompt, fallback, stream=stream):
                    yield token
            else:
                yield f"Error: {str(e)}"
    
    def _update_stats(self, model: str, elapsed: float, tokens: int, ttft: float):
        """Update performance statistics for a model"""
        if model not in self._performance_stats:
            self._performance_stats[model] = {
                "calls": 0,
                "total_time": 0,
                "total_tokens": 0,
                "total_ttft": 0,
                "avg_time": 0,
                "avg_tps": 0,  # Tokens per second
                "avg_ttft": 0,  # Average time to first token
                "best_tps": 0,
                "worst_tps": float('inf')
            }
        
        stats = self._performance_stats[model]
        stats["calls"] += 1
        stats["total_time"] += elapsed
        stats["total_tokens"] += tokens
        stats["total_ttft"] += ttft
        stats["avg_time"] = stats["total_time"] / stats["calls"]
        stats["avg_ttft"] = stats["total_ttft"] / stats["calls"]
        
        if elapsed > 0:
            current_tps = tokens / elapsed
            stats["avg_tps"] = stats["total_tokens"] / stats["total_time"]
            stats["best_tps"] = max(stats["best_tps"], current_tps)
            stats["worst_tps"] = min(stats["worst_tps"], current_tps)
            
        logger.debug(
            f"{model}: {tokens} tokens in {elapsed:.2f}s "
            f"(TTFT: {ttft:.3f}s, {stats['avg_tps']:.1f} t/s avg)"
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for all models"""
        return self._performance_stats
    
    def get_performance_summary(self) -> str:
        """Get a formatted performance summary"""
        if not self._performance_stats:
            return "No performance data available yet."
        
        summary = "\n📊 ECHO 2.0 Performance Summary\n" + "="*50 + "\n"
        
        for model, stats in self._performance_stats.items():
            if stats["calls"] > 0:
                model_type = "🆕 2025" if model in ["deepseek-r1:latest", "qwen3:latest", 
                                                    "codestral:latest", "llama3.3:70b"] else "📦 Legacy"
                summary += f"\n{model_type} {model}:\n"
                summary += f"  • Calls: {stats['calls']}\n"
                summary += f"  • Avg TTFT: {stats['avg_ttft']:.3f}s\n"
                summary += f"  • Avg Speed: {stats['avg_tps']:.1f} tokens/sec\n"
                summary += f"  • Best Speed: {stats['best_tps']:.1f} tokens/sec\n"
        
        return summary
    
    async def benchmark_models(self, prompt: str = "Write a hello world function") -> Dict[str, Any]:
        """Quick benchmark of all available models"""
        results = {}
        
        for model_id in self.available_models:
            start = time.time()
            tokens = 0
            
            async for token in self.generate(prompt, model=model_id, stream=True):
                tokens += 1
                if tokens >= 50:  # Generate 50 tokens for comparison
                    break
            
            elapsed = time.time() - start
            results[model_id] = {
                "time": elapsed,
                "tokens": tokens,
                "tps": tokens / elapsed if elapsed > 0 else 0
            }
        
        return results
    
    async def preload_model(self, model: str):
        """Preload a model into memory for faster first inference"""
        try:
            # Send a minimal request to load the model
            config = self.available_models.get(model, self.MODEL_CONFIGS.get(model))
            data = {
                "model": config.name,
                "prompt": "test",
                "options": {"num_predict": 1}
            }
            
            async with self.client.post(
                f"{self.base_url}/api/generate",
                json=data,
                timeout=60.0
            ) as response:
                response.raise_for_status()
                logger.info(f"✓ Preloaded model: {model}")
                
        except Exception as e:
            logger.warning(f"Failed to preload {model}: {e}")
    
    async def close(self):
        """Clean up resources"""
        await self.client.aclose()
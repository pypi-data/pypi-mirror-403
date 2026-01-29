"""
NC1709 Enhanced Metrics Collection

Provides Prometheus-compatible metrics for monitoring system performance.
"""

import hashlib
import os
import time
from typing import Dict, Optional, Any
from prometheus_client import (
    Counter, Histogram, Gauge, Info, Enum,
    generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry
)


# =============================================================================
# NC1709-CAI: Color-Animal Identifier Algorithm
# =============================================================================
# Generates memorable, secure identifiers for API keys
# Formula: hash(key) → color + animal
# Example: "sk-abc123..." → "teal-hawk"
# =============================================================================

# 16 distinct colors (4-bit selection)
_CAI_COLORS = [
    "red", "blue", "green", "gold",
    "teal", "coral", "mint", "plum",
    "azure", "amber", "jade", "ruby",
    "slate", "ivory", "navy", "lime"
]

# 32 memorable animals (5-bit selection)
_CAI_ANIMALS = [
    "fox", "owl", "wolf", "bear", "hawk", "deer", "lion", "tiger",
    "eagle", "raven", "cobra", "falcon", "otter", "panda", "shark", "whale",
    "phoenix", "dragon", "griffin", "panther", "jaguar", "leopard", "viper", "lynx",
    "condor", "osprey", "heron", "crane", "swan", "dove", "finch", "sparrow"
]

# Owner identifier - reserved for asif-fas
_OWNER_KEY_HASH = "4f3162c4d8bcf80509dd7652c90670f3640863f09aa974b9ebd854093f0828cb"


def generate_api_key_id(api_key: str) -> str:
    """
    Generate a memorable Color-Animal identifier for an API key.

    Algorithm: NC1709-CAI (Color-Animal Identifier)
    -----------------------------------------------
    1. Hash the API key with SHA-256
    2. Use hash bytes to select color (16 options) and animal (32 options)
    3. Return "color-animal" format

    Properties:
    - Deterministic: Same key → same identifier (always)
    - Secure: Cannot reverse to get original key
    - Memorable: Easy to recognize ("my teal-hawk key")
    - Unique: 16 × 32 = 512 combinations

    Special Cases:
    - Owner key → "asif-fas" (reserved identifier)
    - Empty/None → "anon"

    Args:
        api_key: The API key to identify

    Returns:
        Memorable identifier string (e.g., "teal-hawk", "asif-fas")
    """
    if not api_key:
        return "anon"

    # Generate SHA-256 hash of the key
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # Check for owner key (by hash comparison - secure)
    if key_hash == _OWNER_KEY_HASH:
        return "asif-fas"

    # Also check environment variable for owner key
    owner_key_env = os.environ.get("NC1709_OWNER_KEY_HASH")
    if owner_key_env and key_hash == owner_key_env:
        return "asif-fas"

    # Select color using first 4 hex chars (16 options)
    color_idx = int(key_hash[:4], 16) % len(_CAI_COLORS)

    # Select animal using next 5 hex chars (32 options)
    animal_idx = int(key_hash[4:9], 16) % len(_CAI_ANIMALS)

    return f"{_CAI_COLORS[color_idx]}-{_CAI_ANIMALS[animal_idx]}"


def set_owner_key(api_key: str) -> str:
    """
    Generate the hash for an owner key (for configuration).

    Usage:
        hash_value = set_owner_key("your-actual-api-key")
        # Then set _OWNER_KEY_HASH = hash_value in this file
        # Or set NC1709_OWNER_KEY_HASH environment variable

    Args:
        api_key: The API key to designate as owner

    Returns:
        SHA-256 hash to store (never store the actual key!)
    """
    return hashlib.sha256(api_key.encode()).hexdigest()

# Global metrics registry
REGISTRY = CollectorRegistry()

# Request metrics
REQUEST_COUNT = Counter(
    'nc1709_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status_code', 'api_key_prefix'],
    registry=REGISTRY
)

REQUEST_DURATION = Histogram(
    'nc1709_request_duration_seconds',
    'Request processing time in seconds',
    ['endpoint', 'method'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, float('inf')],
    registry=REGISTRY
)

# Model inference metrics  
MODEL_INFERENCE_DURATION = Histogram(
    'nc1709_model_inference_seconds',
    'Model inference time in seconds',
    ['model_name', 'temperature'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 60.0, 120.0, float('inf')],
    registry=REGISTRY
)

MODEL_ERRORS = Counter(
    'nc1709_model_errors_total',
    'Model inference errors',
    ['error_type', 'model_name'],
    registry=REGISTRY
)

MODEL_TOKEN_COUNT = Counter(
    'nc1709_tokens_total',
    'Total tokens processed',
    ['type', 'model_name'],  # type: prompt, completion
    registry=REGISTRY
)

# Connection metrics
ACTIVE_CONNECTIONS = Gauge(
    'nc1709_active_connections',
    'Number of active connections',
    registry=REGISTRY
)

OLLAMA_HEALTH = Gauge(
    'nc1709_ollama_health',
    'Ollama service health (1=healthy, 0=unhealthy)',
    registry=REGISTRY
)

OLLAMA_RESPONSE_TIME = Histogram(
    'nc1709_ollama_response_seconds',
    'Ollama service response time',
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, float('inf')],
    registry=REGISTRY
)

# System metrics
MEMORY_USAGE = Gauge(
    'nc1709_memory_usage_bytes',
    'Memory usage in bytes',
    ['type'],  # rss, vms, shared
    registry=REGISTRY
)

CPU_USAGE = Gauge(
    'nc1709_cpu_usage_percent',
    'CPU usage percentage',
    registry=REGISTRY
)

DISK_USAGE = Gauge(
    'nc1709_disk_usage_percent',
    'Disk usage percentage',
    ['mount_point'],
    registry=REGISTRY
)

# Application-specific metrics
AGENT_EXECUTIONS = Counter(
    'nc1709_agent_executions_total',
    'Total agent executions',
    ['status', 'tool_count'],
    registry=REGISTRY
)

TOOL_EXECUTIONS = Counter(
    'nc1709_tool_executions_total', 
    'Total tool executions',
    ['tool_name', 'status'],
    registry=REGISTRY
)

TOOL_DURATION = Histogram(
    'nc1709_tool_duration_seconds',
    'Tool execution time',
    ['tool_name'],
    buckets=[0.01, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0, float('inf')],
    registry=REGISTRY
)

# Cache metrics
CACHE_HITS = Counter(
    'nc1709_cache_hits_total',
    'Cache hits',
    ['cache_type'],
    registry=REGISTRY
)

CACHE_MISSES = Counter(
    'nc1709_cache_misses_total', 
    'Cache misses',
    ['cache_type'],
    registry=REGISTRY
)

# Application info
APP_INFO = Info(
    'nc1709_application',
    'Application information',
    registry=REGISTRY
)

# Set application info
APP_INFO.info({
    'version': '2.1.7',
    'component': 'nc1709',
    'environment': 'production'
})


class MetricsCollector:
    """Centralized metrics collection and management"""
    
    def __init__(self):
        self.start_time = time.time()
        self.update_system_metrics()
    
    def record_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float,
        api_key: Optional[str] = None
    ):
        """Record HTTP request metrics"""
        # Use NC1709-CAI algorithm for memorable API key identification
        api_key_id = generate_api_key_id(api_key)

        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            api_key_prefix=api_key_id
        ).inc()
        
        REQUEST_DURATION.labels(
            endpoint=endpoint,
            method=method
        ).observe(duration)
    
    def record_model_inference(
        self,
        model_name: str,
        duration: float,
        temperature: float,
        prompt_tokens: int,
        completion_tokens: int,
        success: bool = True,
        error_type: Optional[str] = None
    ):
        """Record model inference metrics"""
        MODEL_INFERENCE_DURATION.labels(
            model_name=model_name,
            temperature=str(temperature)
        ).observe(duration)
        
        MODEL_TOKEN_COUNT.labels(
            type="prompt",
            model_name=model_name
        ).inc(prompt_tokens)
        
        MODEL_TOKEN_COUNT.labels(
            type="completion", 
            model_name=model_name
        ).inc(completion_tokens)
        
        if not success and error_type:
            MODEL_ERRORS.labels(
                error_type=error_type,
                model_name=model_name
            ).inc()
    
    def record_tool_execution(
        self,
        tool_name: str, 
        duration: float,
        success: bool = True
    ):
        """Record tool execution metrics"""
        status = "success" if success else "failure"
        
        TOOL_EXECUTIONS.labels(
            tool_name=tool_name,
            status=status
        ).inc()
        
        TOOL_DURATION.labels(tool_name=tool_name).observe(duration)
    
    def record_agent_execution(
        self,
        success: bool = True,
        tool_count: int = 0
    ):
        """Record agent execution metrics"""
        status = "success" if success else "failure"
        tool_bucket = self._get_tool_count_bucket(tool_count)
        
        AGENT_EXECUTIONS.labels(
            status=status,
            tool_count=tool_bucket
        ).inc()
    
    def _get_tool_count_bucket(self, count: int) -> str:
        """Convert tool count to bucket for metrics"""
        if count == 0:
            return "0"
        elif count <= 3:
            return "1-3"
        elif count <= 10:
            return "4-10"
        else:
            return "10+"
    
    def record_ollama_health(self, healthy: bool, response_time: Optional[float] = None):
        """Record Ollama service health"""
        OLLAMA_HEALTH.set(1 if healthy else 0)
        
        if response_time is not None:
            OLLAMA_RESPONSE_TIME.observe(response_time)
    
    def record_cache_access(self, cache_type: str, hit: bool):
        """Record cache access metrics"""
        if hit:
            CACHE_HITS.labels(cache_type=cache_type).inc()
        else:
            CACHE_MISSES.labels(cache_type=cache_type).inc()
    
    def update_connection_count(self, count: int):
        """Update active connection count"""
        ACTIVE_CONNECTIONS.set(count)
    
    def update_system_metrics(self):
        """Update system resource metrics"""
        try:
            import psutil
            
            # Memory metrics
            memory = psutil.virtual_memory()
            MEMORY_USAGE.labels(type="total").set(memory.total)
            MEMORY_USAGE.labels(type="available").set(memory.available)
            MEMORY_USAGE.labels(type="used").set(memory.used)
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            CPU_USAGE.set(cpu_percent)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            DISK_USAGE.labels(mount_point="/").set(disk_percent)
            
        except ImportError:
            # psutil not available, skip system metrics
            pass
        except Exception:
            # Error getting system metrics, skip
            pass
    
    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format"""
        return generate_latest(REGISTRY)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary for health checks"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "uptime_seconds": time.time() - self.start_time,
                "memory_usage_percent": memory.percent,
                "disk_usage_percent": (disk.used / disk.total) * 100,
                "cpu_usage_percent": psutil.cpu_percent(),
                "active_connections": ACTIVE_CONNECTIONS._value._value,
                "ollama_health": bool(OLLAMA_HEALTH._value._value),
                "total_requests": sum([
                    sample.value for family in REGISTRY.collect() 
                    for sample in family.samples
                    if sample.name == 'nc1709_requests_total'
                ])
            }
        except Exception:
            return {"error": "Could not collect metrics summary"}


# Global metrics collector instance
metrics_collector = MetricsCollector()
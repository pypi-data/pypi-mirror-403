"""
NC1709 Enhanced Monitoring Module

Provides comprehensive monitoring, metrics, and observability for NC1709.

Components:
- Metrics: Prometheus-compatible metrics collection
- Health: Health checks and readiness probes
- Tracing: OpenTelemetry-compatible distributed tracing (NC1709-TRC)
"""

from .metrics import (
    MetricsCollector,
    REQUEST_COUNT,
    REQUEST_DURATION,
    MODEL_INFERENCE_DURATION,
    MODEL_ERRORS,
    ACTIVE_CONNECTIONS,
    OLLAMA_HEALTH,
    generate_api_key_id,
)

from .middleware import MetricsMiddleware
from .health import HealthChecker

from .tracing import (
    Span,
    SpanContext,
    SpanKind,
    SpanStatus,
    Tracer,
    ConsoleExporter,
    InMemoryExporter,
    BatchSpanProcessor,
    get_tracer,
    set_tracer,
    traced,
    trace_llm_call,
    trace_tool_call,
    TracingMiddleware,
)

__all__ = [
    # Metrics
    'MetricsCollector',
    'MetricsMiddleware',
    'REQUEST_COUNT',
    'REQUEST_DURATION',
    'MODEL_INFERENCE_DURATION',
    'MODEL_ERRORS',
    'ACTIVE_CONNECTIONS',
    'OLLAMA_HEALTH',
    'generate_api_key_id',

    # Health
    'HealthChecker',

    # Tracing
    'Span',
    'SpanContext',
    'SpanKind',
    'SpanStatus',
    'Tracer',
    'ConsoleExporter',
    'InMemoryExporter',
    'BatchSpanProcessor',
    'get_tracer',
    'set_tracer',
    'traced',
    'trace_llm_call',
    'trace_tool_call',
    'TracingMiddleware',
]
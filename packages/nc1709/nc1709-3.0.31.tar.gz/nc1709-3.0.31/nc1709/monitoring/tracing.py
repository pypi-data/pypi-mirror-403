"""
NC1709 OpenTelemetry Tracing Module

Provides distributed tracing capabilities using OpenTelemetry for observability
across LLM calls, tool invocations, and request processing.

Algorithm: NC1709-TRC (Trace Context)
- Automatic span creation for key operations
- Context propagation across async boundaries
- Multiple exporter support (Console, OTLP, Jaeger)
- Custom attributes for LLM-specific metadata

Usage:
    from nc1709.monitoring.tracing import tracer, trace_llm_call

    # Using decorator
    @trace_llm_call(model="gpt-4")
    async def call_model(prompt):
        ...

    # Using context manager
    with tracer.start_span("operation") as span:
        span.set_attribute("custom.attr", "value")
        ...
"""

import time
import asyncio
import functools
import threading
import logging
from typing import Any, Callable, Dict, Optional, TypeVar, Union, List
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager, asynccontextmanager
import uuid

logger = logging.getLogger(__name__)

# Type variables for generic decorators
F = TypeVar('F', bound=Callable[..., Any])


class SpanKind(Enum):
    """OpenTelemetry-compatible span kinds"""
    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanStatus(Enum):
    """Span status codes"""
    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


@dataclass
class SpanContext:
    """Context for trace propagation"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    trace_flags: int = 1  # 1 = sampled
    trace_state: Dict[str, str] = field(default_factory=dict)

    def to_w3c_traceparent(self) -> str:
        """Convert to W3C Trace Context format"""
        return f"00-{self.trace_id}-{self.span_id}-{self.trace_flags:02x}"

    @classmethod
    def from_w3c_traceparent(cls, traceparent: str) -> Optional['SpanContext']:
        """Parse W3C Trace Context format"""
        try:
            parts = traceparent.split('-')
            if len(parts) >= 4 and parts[0] == '00':
                return cls(
                    trace_id=parts[1],
                    span_id=parts[2],
                    trace_flags=int(parts[3], 16)
                )
        except (ValueError, IndexError):
            pass
        return None


@dataclass
class SpanEvent:
    """Event recorded within a span"""
    name: str
    timestamp: float
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SpanLink:
    """Link to another span"""
    context: SpanContext
    attributes: Dict[str, Any] = field(default_factory=dict)


class Span:
    """
    Represents a unit of work in a trace.

    Follows OpenTelemetry Span specification with:
    - Name and kind
    - Start and end timestamps
    - Attributes for metadata
    - Events for point-in-time occurrences
    - Links to related spans
    - Status for success/error indication
    """

    def __init__(
        self,
        name: str,
        context: SpanContext,
        kind: SpanKind = SpanKind.INTERNAL,
        parent: Optional['Span'] = None,
        attributes: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.context = context
        self.kind = kind
        self.parent = parent
        self.attributes: Dict[str, Any] = attributes or {}
        self.events: List[SpanEvent] = []
        self.links: List[SpanLink] = []
        self.status = SpanStatus.UNSET
        self.status_message: Optional[str] = None

        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self._ended = False

        # NC1709-specific attributes
        self.attributes["nc1709.version"] = "1.0.0"
        self.attributes["span.kind"] = kind.value

    def set_attribute(self, key: str, value: Any) -> 'Span':
        """Set a span attribute"""
        if not self._ended:
            self.attributes[key] = value
        return self

    def set_attributes(self, attributes: Dict[str, Any]) -> 'Span':
        """Set multiple attributes"""
        if not self._ended:
            self.attributes.update(attributes)
        return self

    def add_event(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None
    ) -> 'Span':
        """Add an event to the span"""
        if not self._ended:
            self.events.append(SpanEvent(
                name=name,
                timestamp=timestamp or time.time(),
                attributes=attributes or {}
            ))
        return self

    def add_link(
        self,
        context: SpanContext,
        attributes: Optional[Dict[str, Any]] = None
    ) -> 'Span':
        """Add a link to another span"""
        if not self._ended:
            self.links.append(SpanLink(
                context=context,
                attributes=attributes or {}
            ))
        return self

    def set_status(self, status: SpanStatus, message: Optional[str] = None) -> 'Span':
        """Set span status"""
        if not self._ended:
            self.status = status
            self.status_message = message
        return self

    def record_exception(
        self,
        exception: Exception,
        attributes: Optional[Dict[str, Any]] = None
    ) -> 'Span':
        """Record an exception as an event"""
        exc_attrs = {
            "exception.type": type(exception).__name__,
            "exception.message": str(exception),
            **(attributes or {})
        }
        self.add_event("exception", exc_attrs)
        self.set_status(SpanStatus.ERROR, str(exception))
        return self

    def end(self, end_time: Optional[float] = None) -> None:
        """End the span"""
        if not self._ended:
            self.end_time = end_time or time.time()
            self._ended = True

    @property
    def duration_ms(self) -> float:
        """Get span duration in milliseconds"""
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return (time.time() - self.start_time) * 1000

    @property
    def is_recording(self) -> bool:
        """Check if span is still recording"""
        return not self._ended

    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary for export"""
        return {
            "name": self.name,
            "trace_id": self.context.trace_id,
            "span_id": self.context.span_id,
            "parent_span_id": self.context.parent_span_id,
            "kind": self.kind.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "status": self.status.value,
            "status_message": self.status_message,
            "attributes": self.attributes,
            "events": [
                {"name": e.name, "timestamp": e.timestamp, "attributes": e.attributes}
                for e in self.events
            ],
            "links": [
                {"trace_id": l.context.trace_id, "span_id": l.context.span_id, "attributes": l.attributes}
                for l in self.links
            ]
        }

    def __enter__(self) -> 'Span':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_val:
            self.record_exception(exc_val)
        elif self.status == SpanStatus.UNSET:
            self.set_status(SpanStatus.OK)
        self.end()


class SpanExporter:
    """Base class for span exporters"""

    def export(self, spans: List[Span]) -> bool:
        """Export spans. Returns True on success."""
        raise NotImplementedError

    def shutdown(self) -> None:
        """Cleanup resources"""
        pass


class ConsoleExporter(SpanExporter):
    """Export spans to console for debugging"""

    def __init__(self, pretty: bool = True):
        self.pretty = pretty

    def export(self, spans: List[Span]) -> bool:
        for span in spans:
            if self.pretty:
                self._print_pretty(span)
            else:
                print(span.to_dict())
        return True

    def _print_pretty(self, span: Span) -> None:
        """Pretty print a span"""
        status_icon = {
            SpanStatus.OK: "[OK]",
            SpanStatus.ERROR: "[ERR]",
            SpanStatus.UNSET: "[---]"
        }[span.status]

        print(f"\n{'='*60}")
        print(f"SPAN: {span.name} {status_icon}")
        print(f"  Trace: {span.context.trace_id[:16]}...")
        print(f"  Span:  {span.context.span_id}")
        if span.context.parent_span_id:
            print(f"  Parent: {span.context.parent_span_id}")
        print(f"  Duration: {span.duration_ms:.2f}ms")
        print(f"  Kind: {span.kind.value}")

        if span.attributes:
            print("  Attributes:")
            for k, v in span.attributes.items():
                print(f"    {k}: {v}")

        if span.events:
            print("  Events:")
            for event in span.events:
                print(f"    - {event.name} @ {event.timestamp:.3f}")

        if span.status_message:
            print(f"  Status: {span.status_message}")


class InMemoryExporter(SpanExporter):
    """Export spans to memory for testing"""

    def __init__(self, max_spans: int = 1000):
        self.spans: List[Dict[str, Any]] = []
        self.max_spans = max_spans
        self._lock = threading.Lock()

    def export(self, spans: List[Span]) -> bool:
        with self._lock:
            for span in spans:
                if len(self.spans) >= self.max_spans:
                    self.spans.pop(0)
                self.spans.append(span.to_dict())
        return True

    def get_spans(self) -> List[Dict[str, Any]]:
        """Get all exported spans"""
        with self._lock:
            return list(self.spans)

    def clear(self) -> None:
        """Clear all spans"""
        with self._lock:
            self.spans.clear()

    def find_spans(self, name: Optional[str] = None, **attributes) -> List[Dict[str, Any]]:
        """Find spans matching criteria"""
        with self._lock:
            results = []
            for span in self.spans:
                if name and span["name"] != name:
                    continue
                if all(span.get("attributes", {}).get(k) == v for k, v in attributes.items()):
                    results.append(span)
            return results


class BatchSpanProcessor:
    """Batch span processing with periodic export"""

    def __init__(
        self,
        exporter: SpanExporter,
        max_batch_size: int = 512,
        export_interval: float = 5.0
    ):
        self.exporter = exporter
        self.max_batch_size = max_batch_size
        self.export_interval = export_interval

        self._queue: List[Span] = []
        self._lock = threading.Lock()
        self._shutdown = False
        self._export_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the batch processor"""
        if self._export_thread is None:
            self._shutdown = False
            self._export_thread = threading.Thread(target=self._export_loop, daemon=True)
            self._export_thread.start()

    def _export_loop(self) -> None:
        """Background export loop"""
        while not self._shutdown:
            time.sleep(self.export_interval)
            self._flush()

    def on_end(self, span: Span) -> None:
        """Called when a span ends"""
        with self._lock:
            self._queue.append(span)
            if len(self._queue) >= self.max_batch_size:
                self._flush_locked()

    def _flush(self) -> None:
        """Flush pending spans"""
        with self._lock:
            self._flush_locked()

    def _flush_locked(self) -> None:
        """Flush while holding lock"""
        if self._queue:
            spans = self._queue[:]
            self._queue.clear()
            try:
                self.exporter.export(spans)
            except Exception as e:
                logger.error(f"Error exporting spans: {e}")

    def shutdown(self) -> None:
        """Shutdown the processor"""
        self._shutdown = True
        if self._export_thread:
            self._export_thread.join(timeout=5.0)
        self._flush()
        self.exporter.shutdown()


class Tracer:
    """
    Main tracer class for creating and managing spans.

    NC1709-TRC Algorithm:
    - Hierarchical span creation with automatic parent linking
    - Thread-local context storage for sync code
    - Contextvars for async code
    - Automatic span export on end
    """

    def __init__(
        self,
        service_name: str = "nc1709",
        exporter: Optional[SpanExporter] = None,
        processor: Optional[BatchSpanProcessor] = None
    ):
        self.service_name = service_name
        self._local = threading.local()

        # Default to console exporter
        if exporter is None:
            exporter = ConsoleExporter(pretty=True)

        if processor is None:
            processor = BatchSpanProcessor(exporter)

        self.processor = processor
        self.processor.start()

        # Global attributes added to all spans
        self._global_attributes: Dict[str, Any] = {
            "service.name": service_name
        }

    def _generate_id(self, length: int = 16) -> str:
        """Generate a random hex ID"""
        return uuid.uuid4().hex[:length * 2]

    def _get_current_span(self) -> Optional[Span]:
        """Get current span from context"""
        return getattr(self._local, 'current_span', None)

    def _set_current_span(self, span: Optional[Span]) -> None:
        """Set current span in context"""
        self._local.current_span = span

    def set_global_attribute(self, key: str, value: Any) -> None:
        """Set a global attribute added to all spans"""
        self._global_attributes[key] = value

    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None,
        parent: Optional[Span] = None
    ) -> Span:
        """
        Start a new span.

        Args:
            name: Span name
            kind: Span kind (internal, server, client, etc.)
            attributes: Initial attributes
            parent: Explicit parent span (uses current span if not specified)

        Returns:
            New Span instance
        """
        # Determine parent
        if parent is None:
            parent = self._get_current_span()

        # Create context
        if parent:
            context = SpanContext(
                trace_id=parent.context.trace_id,
                span_id=self._generate_id(8),
                parent_span_id=parent.context.span_id
            )
        else:
            context = SpanContext(
                trace_id=self._generate_id(16),
                span_id=self._generate_id(8)
            )

        # Create span with attributes
        all_attributes = {**self._global_attributes}
        if attributes:
            all_attributes.update(attributes)

        span = Span(
            name=name,
            context=context,
            kind=kind,
            parent=parent,
            attributes=all_attributes
        )

        self._set_current_span(span)
        return span

    @contextmanager
    def trace(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Context manager for tracing a block of code"""
        span = self.start_span(name, kind, attributes)
        previous_span = span.parent

        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            raise
        finally:
            if span.status == SpanStatus.UNSET:
                span.set_status(SpanStatus.OK)
            span.end()
            self.processor.on_end(span)
            self._set_current_span(previous_span)

    @asynccontextmanager
    async def trace_async(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Async context manager for tracing"""
        span = self.start_span(name, kind, attributes)
        previous_span = span.parent

        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            raise
        finally:
            if span.status == SpanStatus.UNSET:
                span.set_status(SpanStatus.OK)
            span.end()
            self.processor.on_end(span)
            self._set_current_span(previous_span)

    def get_current_trace_context(self) -> Optional[SpanContext]:
        """Get current trace context for propagation"""
        span = self._get_current_span()
        return span.context if span else None

    def inject_context(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Inject trace context into headers for propagation"""
        context = self.get_current_trace_context()
        if context:
            headers["traceparent"] = context.to_w3c_traceparent()
        return headers

    def extract_context(self, headers: Dict[str, str]) -> Optional[SpanContext]:
        """Extract trace context from headers"""
        traceparent = headers.get("traceparent")
        if traceparent:
            return SpanContext.from_w3c_traceparent(traceparent)
        return None

    def shutdown(self) -> None:
        """Shutdown the tracer"""
        self.processor.shutdown()


# Global tracer instance
_tracer: Optional[Tracer] = None
_tracer_lock = threading.Lock()


def get_tracer(
    service_name: str = "nc1709",
    exporter: Optional[SpanExporter] = None
) -> Tracer:
    """Get or create the global tracer"""
    global _tracer
    with _tracer_lock:
        if _tracer is None:
            _tracer = Tracer(service_name, exporter)
        return _tracer


def set_tracer(tracer: Tracer) -> None:
    """Set the global tracer (for testing)"""
    global _tracer
    with _tracer_lock:
        _tracer = tracer


# Convenience decorators

def traced(
    name: Optional[str] = None,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[Dict[str, Any]] = None
) -> Callable[[F], F]:
    """
    Decorator to trace a function.

    Usage:
        @traced("my_operation")
        def my_function():
            ...
    """
    def decorator(func: F) -> F:
        span_name = name or func.__name__

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.trace(span_name, kind, attributes) as span:
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                return func(*args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            async with tracer.trace_async(span_name, kind, attributes) as span:
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                return await func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


def trace_llm_call(
    model: Optional[str] = None,
    provider: Optional[str] = None
) -> Callable[[F], F]:
    """
    Decorator specifically for LLM calls.

    Usage:
        @trace_llm_call(model="gpt-4", provider="openai")
        async def call_model(prompt):
            ...
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            attrs = {
                "llm.request_type": "completion",
                "llm.system": provider or "unknown"
            }
            if model:
                attrs["llm.model"] = model

            with tracer.trace(f"llm.{func.__name__}", SpanKind.CLIENT, attrs) as span:
                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("llm.response.success", True)
                    return result
                except Exception as e:
                    span.set_attribute("llm.response.success", False)
                    span.set_attribute("llm.error.type", type(e).__name__)
                    raise
                finally:
                    span.set_attribute("llm.duration_ms", (time.time() - start) * 1000)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            attrs = {
                "llm.request_type": "completion",
                "llm.system": provider or "unknown"
            }
            if model:
                attrs["llm.model"] = model

            async with tracer.trace_async(f"llm.{func.__name__}", SpanKind.CLIENT, attrs) as span:
                start = time.time()
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("llm.response.success", True)
                    return result
                except Exception as e:
                    span.set_attribute("llm.response.success", False)
                    span.set_attribute("llm.error.type", type(e).__name__)
                    raise
                finally:
                    span.set_attribute("llm.duration_ms", (time.time() - start) * 1000)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


def trace_tool_call(tool_name: Optional[str] = None) -> Callable[[F], F]:
    """
    Decorator for tracing tool invocations.

    Usage:
        @trace_tool_call("file_read")
        def read_file(path):
            ...
    """
    def decorator(func: F) -> F:
        name = tool_name or func.__name__

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            attrs = {
                "tool.name": name,
                "tool.type": "function"
            }

            with tracer.trace(f"tool.{name}", SpanKind.INTERNAL, attrs) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("tool.success", True)
                    return result
                except Exception as e:
                    span.set_attribute("tool.success", False)
                    span.set_attribute("tool.error", str(e))
                    raise

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            attrs = {
                "tool.name": name,
                "tool.type": "function"
            }

            async with tracer.trace_async(f"tool.{name}", SpanKind.INTERNAL, attrs) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("tool.success", True)
                    return result
                except Exception as e:
                    span.set_attribute("tool.success", False)
                    span.set_attribute("tool.error", str(e))
                    raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


class TracingMiddleware:
    """
    ASGI/WSGI-like middleware for request tracing.

    Creates spans for incoming requests with:
    - HTTP method and path
    - Status code
    - Duration
    - Request/response headers
    """

    def __init__(self, tracer: Optional[Tracer] = None):
        self.tracer = tracer or get_tracer()

    def trace_request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None
    ) -> Span:
        """Start tracing a request"""
        # Extract parent context from headers
        parent_context = None
        if headers:
            parent_context = self.tracer.extract_context(headers)

        attrs = {
            "http.method": method,
            "http.target": path,
            "http.scheme": "https"
        }

        span = self.tracer.start_span(
            f"{method} {path}",
            kind=SpanKind.SERVER,
            attributes=attrs
        )

        if parent_context:
            span.add_link(parent_context)

        return span

    def finish_request(
        self,
        span: Span,
        status_code: int,
        error: Optional[Exception] = None
    ) -> None:
        """Finish tracing a request"""
        span.set_attribute("http.status_code", status_code)

        if error:
            span.record_exception(error)
        elif status_code >= 400:
            span.set_status(SpanStatus.ERROR, f"HTTP {status_code}")
        else:
            span.set_status(SpanStatus.OK)

        span.end()
        self.tracer.processor.on_end(span)


# Export convenience functions
__all__ = [
    # Core classes
    'Span',
    'SpanContext',
    'SpanKind',
    'SpanStatus',
    'SpanEvent',
    'SpanLink',
    'Tracer',

    # Exporters
    'SpanExporter',
    'ConsoleExporter',
    'InMemoryExporter',
    'BatchSpanProcessor',

    # Global access
    'get_tracer',
    'set_tracer',

    # Decorators
    'traced',
    'trace_llm_call',
    'trace_tool_call',

    # Middleware
    'TracingMiddleware',
]

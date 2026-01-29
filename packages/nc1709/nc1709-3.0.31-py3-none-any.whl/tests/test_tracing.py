"""
NC1709 Tracing Tests

Tests for the OpenTelemetry-compatible distributed tracing implementation.
"""

import pytest
import asyncio
import time
import threading
from unittest.mock import Mock, patch, MagicMock

from nc1709.monitoring.tracing import (
    Span,
    SpanContext,
    SpanKind,
    SpanStatus,
    SpanEvent,
    SpanLink,
    Tracer,
    SpanExporter,
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


class TestSpanContext:
    """Test SpanContext functionality"""

    def test_create_context(self):
        """Context stores trace and span IDs"""
        context = SpanContext(
            trace_id="abc123",
            span_id="def456"
        )

        assert context.trace_id == "abc123"
        assert context.span_id == "def456"
        assert context.parent_span_id is None

    def test_context_with_parent(self):
        """Context can have parent span ID"""
        context = SpanContext(
            trace_id="abc123",
            span_id="def456",
            parent_span_id="parent789"
        )

        assert context.parent_span_id == "parent789"

    def test_to_w3c_traceparent(self):
        """Converts to W3C Trace Context format"""
        context = SpanContext(
            trace_id="0af7651916cd43dd8448eb211c80319c",
            span_id="b7ad6b7169203331",
            trace_flags=1
        )

        traceparent = context.to_w3c_traceparent()
        assert traceparent == "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"

    def test_from_w3c_traceparent(self):
        """Parses W3C Trace Context format"""
        traceparent = "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"

        context = SpanContext.from_w3c_traceparent(traceparent)

        assert context is not None
        assert context.trace_id == "0af7651916cd43dd8448eb211c80319c"
        assert context.span_id == "b7ad6b7169203331"
        assert context.trace_flags == 1

    def test_invalid_traceparent_returns_none(self):
        """Invalid traceparent returns None"""
        assert SpanContext.from_w3c_traceparent("invalid") is None
        assert SpanContext.from_w3c_traceparent("") is None
        assert SpanContext.from_w3c_traceparent("01-abc-def-00") is None


class TestSpan:
    """Test Span functionality"""

    @pytest.fixture
    def span(self):
        context = SpanContext(trace_id="trace123", span_id="span456")
        return Span(name="test_span", context=context)

    def test_span_creation(self, span):
        """Span is created with correct defaults"""
        assert span.name == "test_span"
        assert span.kind == SpanKind.INTERNAL
        assert span.status == SpanStatus.UNSET
        assert span.is_recording
        assert span.start_time > 0

    def test_set_attribute(self, span):
        """Can set attributes"""
        result = span.set_attribute("key", "value")

        assert result is span  # Fluent API
        assert span.attributes["key"] == "value"

    def test_set_multiple_attributes(self, span):
        """Can set multiple attributes at once"""
        span.set_attributes({
            "key1": "value1",
            "key2": "value2"
        })

        assert span.attributes["key1"] == "value1"
        assert span.attributes["key2"] == "value2"

    def test_add_event(self, span):
        """Can add events"""
        span.add_event("event_name", {"attr": "value"})

        assert len(span.events) == 1
        assert span.events[0].name == "event_name"
        assert span.events[0].attributes["attr"] == "value"

    def test_add_link(self, span):
        """Can add links to other spans"""
        linked_context = SpanContext(trace_id="other_trace", span_id="other_span")
        span.add_link(linked_context, {"link_attr": "value"})

        assert len(span.links) == 1
        assert span.links[0].context.trace_id == "other_trace"
        assert span.links[0].attributes["link_attr"] == "value"

    def test_set_status(self, span):
        """Can set status"""
        span.set_status(SpanStatus.OK, "Success")

        assert span.status == SpanStatus.OK
        assert span.status_message == "Success"

    def test_record_exception(self, span):
        """Records exception as event and sets error status"""
        error = ValueError("test error")
        span.record_exception(error)

        assert span.status == SpanStatus.ERROR
        assert len(span.events) == 1
        assert span.events[0].name == "exception"
        assert span.events[0].attributes["exception.type"] == "ValueError"
        assert span.events[0].attributes["exception.message"] == "test error"

    def test_end_span(self, span):
        """End finalizes the span"""
        span.end()

        assert span.end_time is not None
        assert not span.is_recording
        assert span.duration_ms >= 0

    def test_cannot_modify_after_end(self, span):
        """Cannot modify span after ending"""
        span.end()

        span.set_attribute("key", "value")
        span.add_event("event")

        assert "key" not in span.attributes
        assert len(span.events) == 0

    def test_context_manager(self):
        """Span works as context manager"""
        context = SpanContext(trace_id="trace", span_id="span")
        span = Span(name="test", context=context)

        with span:
            span.set_attribute("inside", True)

        assert span.end_time is not None
        assert span.status == SpanStatus.OK

    def test_context_manager_records_exception(self):
        """Context manager records exceptions"""
        context = SpanContext(trace_id="trace", span_id="span")
        span = Span(name="test", context=context)

        with pytest.raises(ValueError):
            with span:
                raise ValueError("error")

        assert span.status == SpanStatus.ERROR
        assert len(span.events) == 1

    def test_to_dict(self, span):
        """Converts to dictionary"""
        span.set_attribute("key", "value")
        span.add_event("event")
        span.end()

        data = span.to_dict()

        assert data["name"] == "test_span"
        assert data["trace_id"] == "trace123"
        assert data["span_id"] == "span456"
        assert data["attributes"]["key"] == "value"
        assert len(data["events"]) == 1


class TestInMemoryExporter:
    """Test InMemoryExporter functionality"""

    @pytest.fixture
    def exporter(self):
        return InMemoryExporter()

    def test_export_spans(self, exporter):
        """Exports spans to memory"""
        context = SpanContext(trace_id="trace", span_id="span")
        span = Span(name="test", context=context)
        span.end()

        result = exporter.export([span])

        assert result is True
        assert len(exporter.get_spans()) == 1

    def test_max_spans_limit(self):
        """Respects max spans limit"""
        exporter = InMemoryExporter(max_spans=3)

        for i in range(5):
            context = SpanContext(trace_id="trace", span_id=f"span{i}")
            span = Span(name=f"test{i}", context=context)
            span.end()
            exporter.export([span])

        spans = exporter.get_spans()
        assert len(spans) == 3
        # Oldest should be removed
        assert spans[0]["name"] == "test2"

    def test_find_spans(self, exporter):
        """Finds spans by criteria"""
        for i in range(3):
            context = SpanContext(trace_id="trace", span_id=f"span{i}")
            span = Span(name=f"test{i}", context=context)
            span.set_attribute("index", i)
            span.end()
            exporter.export([span])

        results = exporter.find_spans(name="test1")
        assert len(results) == 1
        assert results[0]["name"] == "test1"

        results = exporter.find_spans(index=2)
        assert len(results) == 1
        assert results[0]["attributes"]["index"] == 2

    def test_clear(self, exporter):
        """Clears all spans"""
        context = SpanContext(trace_id="trace", span_id="span")
        span = Span(name="test", context=context)
        span.end()
        exporter.export([span])

        exporter.clear()

        assert len(exporter.get_spans()) == 0


class TestBatchSpanProcessor:
    """Test BatchSpanProcessor functionality"""

    def test_on_end_queues_span(self):
        """Spans are queued on end"""
        exporter = Mock(spec=SpanExporter)
        processor = BatchSpanProcessor(exporter, max_batch_size=10)

        context = SpanContext(trace_id="trace", span_id="span")
        span = Span(name="test", context=context)
        span.end()

        processor.on_end(span)

        assert len(processor._queue) == 1

    def test_auto_flush_on_batch_size(self):
        """Flushes when batch size reached"""
        exporter = Mock(spec=SpanExporter)
        exporter.export.return_value = True
        processor = BatchSpanProcessor(exporter, max_batch_size=3)

        for i in range(5):
            context = SpanContext(trace_id="trace", span_id=f"span{i}")
            span = Span(name=f"test{i}", context=context)
            span.end()
            processor.on_end(span)

        # Should have exported at least once (at batch size 3)
        assert exporter.export.called

    def test_shutdown_flushes_remaining(self):
        """Shutdown flushes remaining spans"""
        exporter = Mock(spec=SpanExporter)
        exporter.export.return_value = True
        processor = BatchSpanProcessor(exporter, max_batch_size=100)

        context = SpanContext(trace_id="trace", span_id="span")
        span = Span(name="test", context=context)
        span.end()
        processor.on_end(span)

        processor.shutdown()

        assert exporter.export.called
        assert exporter.shutdown.called


class TestTracer:
    """Test Tracer functionality"""

    @pytest.fixture
    def exporter(self):
        return InMemoryExporter()

    @pytest.fixture
    def tracer(self, exporter):
        processor = BatchSpanProcessor(exporter, max_batch_size=100)
        return Tracer(service_name="test_service", processor=processor)

    def test_start_span(self, tracer):
        """Creates new span"""
        span = tracer.start_span("test_operation")

        assert span.name == "test_operation"
        assert span.context.trace_id is not None
        assert span.context.span_id is not None
        assert span.attributes["service.name"] == "test_service"

    def test_parent_child_spans(self, tracer):
        """Child spans link to parent"""
        parent = tracer.start_span("parent")
        child = tracer.start_span("child")

        assert child.context.trace_id == parent.context.trace_id
        assert child.context.parent_span_id == parent.context.span_id

    def test_trace_context_manager(self, tracer, exporter):
        """Trace context manager works"""
        with tracer.trace("operation") as span:
            span.set_attribute("inside", True)

        # Give processor time to queue
        tracer.processor._flush()
        spans = exporter.get_spans()

        assert len(spans) == 1
        assert spans[0]["name"] == "operation"
        assert spans[0]["status"] == "ok"

    def test_trace_records_exception(self, tracer, exporter):
        """Trace context manager records exceptions"""
        with pytest.raises(ValueError):
            with tracer.trace("failing") as span:
                raise ValueError("error")

        tracer.processor._flush()
        spans = exporter.get_spans()

        assert len(spans) == 1
        assert spans[0]["status"] == "error"

    @pytest.mark.asyncio
    async def test_trace_async(self, tracer, exporter):
        """Async trace context manager works"""
        async with tracer.trace_async("async_op") as span:
            span.set_attribute("async", True)
            await asyncio.sleep(0.01)

        tracer.processor._flush()
        spans = exporter.get_spans()

        assert len(spans) == 1
        assert spans[0]["name"] == "async_op"

    def test_inject_context(self, tracer):
        """Injects trace context into headers"""
        with tracer.trace("parent"):
            headers = {}
            tracer.inject_context(headers)

            assert "traceparent" in headers
            assert headers["traceparent"].startswith("00-")

    def test_extract_context(self, tracer):
        """Extracts trace context from headers"""
        headers = {"traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"}

        context = tracer.extract_context(headers)

        assert context is not None
        assert context.trace_id == "0af7651916cd43dd8448eb211c80319c"

    def test_set_global_attribute(self, tracer):
        """Global attributes added to all spans"""
        tracer.set_global_attribute("env", "test")

        span = tracer.start_span("test")

        assert span.attributes["env"] == "test"


class TestTracedDecorator:
    """Test traced decorator"""

    @pytest.fixture(autouse=True)
    def setup_tracer(self):
        exporter = InMemoryExporter()
        processor = BatchSpanProcessor(exporter, max_batch_size=100)
        tracer = Tracer(service_name="test", processor=processor)
        set_tracer(tracer)
        self.tracer = tracer
        self.exporter = exporter
        yield
        tracer.shutdown()

    def test_sync_function(self):
        """Traces sync functions"""
        @traced("sync_op")
        def my_function():
            return "result"

        result = my_function()

        assert result == "result"

        self.tracer.processor._flush()
        spans = self.exporter.get_spans()
        assert len(spans) == 1
        assert spans[0]["name"] == "sync_op"

    @pytest.mark.asyncio
    async def test_async_function(self):
        """Traces async functions"""
        @traced("async_op")
        async def my_async_function():
            await asyncio.sleep(0.01)
            return "async_result"

        result = await my_async_function()

        assert result == "async_result"

        self.tracer.processor._flush()
        spans = self.exporter.get_spans()
        assert len(spans) == 1
        assert spans[0]["name"] == "async_op"

    def test_uses_function_name_by_default(self):
        """Uses function name if no name specified"""
        @traced()
        def named_function():
            pass

        named_function()

        self.tracer.processor._flush()
        spans = self.exporter.get_spans()
        assert spans[0]["name"] == "named_function"


class TestTraceLLMCallDecorator:
    """Test trace_llm_call decorator"""

    @pytest.fixture(autouse=True)
    def setup_tracer(self):
        exporter = InMemoryExporter()
        processor = BatchSpanProcessor(exporter, max_batch_size=100)
        tracer = Tracer(service_name="test", processor=processor)
        set_tracer(tracer)
        self.tracer = tracer
        self.exporter = exporter
        yield
        tracer.shutdown()

    def test_llm_call_success(self):
        """Traces successful LLM call"""
        @trace_llm_call(model="gpt-4", provider="openai")
        def call_model(prompt):
            return {"response": "Hello!"}

        result = call_model("Hi")

        assert result["response"] == "Hello!"

        self.tracer.processor._flush()
        spans = self.exporter.get_spans()
        assert len(spans) == 1
        assert spans[0]["attributes"]["llm.model"] == "gpt-4"
        assert spans[0]["attributes"]["llm.system"] == "openai"
        assert spans[0]["attributes"]["llm.response.success"] is True

    def test_llm_call_error(self):
        """Traces LLM call errors"""
        @trace_llm_call(model="gpt-4", provider="openai")
        def failing_call(prompt):
            raise ValueError("API Error")

        with pytest.raises(ValueError):
            failing_call("Hi")

        self.tracer.processor._flush()
        spans = self.exporter.get_spans()
        assert spans[0]["attributes"]["llm.response.success"] is False
        assert spans[0]["attributes"]["llm.error.type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_async_llm_call(self):
        """Traces async LLM calls"""
        @trace_llm_call(model="claude-3", provider="anthropic")
        async def async_call(prompt):
            await asyncio.sleep(0.01)
            return {"response": "Hi!"}

        result = await async_call("Hello")

        assert result["response"] == "Hi!"

        self.tracer.processor._flush()
        spans = self.exporter.get_spans()
        assert spans[0]["attributes"]["llm.model"] == "claude-3"


class TestTraceToolCallDecorator:
    """Test trace_tool_call decorator"""

    @pytest.fixture(autouse=True)
    def setup_tracer(self):
        exporter = InMemoryExporter()
        processor = BatchSpanProcessor(exporter, max_batch_size=100)
        tracer = Tracer(service_name="test", processor=processor)
        set_tracer(tracer)
        self.tracer = tracer
        self.exporter = exporter
        yield
        tracer.shutdown()

    def test_tool_call_success(self):
        """Traces successful tool call"""
        @trace_tool_call("file_read")
        def read_file(path):
            return "file contents"

        result = read_file("/path/to/file")

        assert result == "file contents"

        self.tracer.processor._flush()
        spans = self.exporter.get_spans()
        assert spans[0]["name"] == "tool.file_read"
        assert spans[0]["attributes"]["tool.name"] == "file_read"
        assert spans[0]["attributes"]["tool.success"] is True

    def test_tool_call_error(self):
        """Traces tool call errors"""
        @trace_tool_call("file_read")
        def failing_read(path):
            raise FileNotFoundError("Not found")

        with pytest.raises(FileNotFoundError):
            failing_read("/missing")

        self.tracer.processor._flush()
        spans = self.exporter.get_spans()
        assert spans[0]["attributes"]["tool.success"] is False


class TestTracingMiddleware:
    """Test TracingMiddleware functionality"""

    @pytest.fixture(autouse=True)
    def setup_tracer(self):
        exporter = InMemoryExporter()
        processor = BatchSpanProcessor(exporter, max_batch_size=100)
        tracer = Tracer(service_name="test", processor=processor)
        set_tracer(tracer)
        self.tracer = tracer
        self.exporter = exporter
        self.middleware = TracingMiddleware(tracer)
        yield
        tracer.shutdown()

    def test_trace_request(self):
        """Traces HTTP requests"""
        span = self.middleware.trace_request("GET", "/api/users")

        assert span.name == "GET /api/users"
        assert span.kind == SpanKind.SERVER
        assert span.attributes["http.method"] == "GET"
        assert span.attributes["http.target"] == "/api/users"

    def test_finish_request_success(self):
        """Finishes request with success status"""
        span = self.middleware.trace_request("GET", "/api/users")
        self.middleware.finish_request(span, 200)

        assert span.attributes["http.status_code"] == 200
        assert span.status == SpanStatus.OK

    def test_finish_request_error(self):
        """Finishes request with error status"""
        span = self.middleware.trace_request("POST", "/api/users")
        self.middleware.finish_request(span, 500)

        assert span.attributes["http.status_code"] == 500
        assert span.status == SpanStatus.ERROR

    def test_finish_request_with_exception(self):
        """Records exception on request failure"""
        span = self.middleware.trace_request("PUT", "/api/users/1")
        error = ValueError("Database error")
        self.middleware.finish_request(span, 500, error)

        assert len(span.events) == 1
        assert span.events[0].name == "exception"

    def test_propagates_context(self):
        """Extracts and links parent context from headers"""
        headers = {
            "traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
        }

        span = self.middleware.trace_request("GET", "/api/data", headers)

        assert len(span.links) == 1
        assert span.links[0].context.trace_id == "0af7651916cd43dd8448eb211c80319c"


class TestGlobalTracerFunctions:
    """Test global tracer access functions"""

    def test_get_tracer_returns_tracer(self):
        """get_tracer returns a Tracer instance"""
        tracer = get_tracer("my_service")
        assert isinstance(tracer, Tracer)

    def test_set_tracer_overrides_global(self):
        """set_tracer overrides global tracer"""
        exporter = InMemoryExporter()
        processor = BatchSpanProcessor(exporter)
        custom_tracer = Tracer(service_name="custom", processor=processor)

        set_tracer(custom_tracer)

        assert get_tracer() is custom_tracer
        custom_tracer.shutdown()


class TestConsoleExporter:
    """Test ConsoleExporter functionality"""

    def test_export_returns_true(self):
        """Export always returns True"""
        exporter = ConsoleExporter(pretty=False)

        context = SpanContext(trace_id="trace", span_id="span")
        span = Span(name="test", context=context)
        span.end()

        result = exporter.export([span])
        assert result is True

    def test_pretty_print(self, capsys):
        """Pretty print outputs formatted span"""
        exporter = ConsoleExporter(pretty=True)

        context = SpanContext(trace_id="abcd1234abcd1234", span_id="span1234")
        span = Span(name="test_span", context=context)
        span.set_attribute("key", "value")
        span.set_status(SpanStatus.OK)
        span.end()

        exporter.export([span])

        captured = capsys.readouterr()
        assert "SPAN: test_span" in captured.out
        assert "[OK]" in captured.out
        assert "key: value" in captured.out


class TestConcurrency:
    """Test thread safety of tracing"""

    def test_concurrent_span_creation(self):
        """Spans can be created concurrently"""
        exporter = InMemoryExporter()
        processor = BatchSpanProcessor(exporter, max_batch_size=1000)
        tracer = Tracer(service_name="test", processor=processor)

        errors = []
        spans_created = []

        def worker():
            try:
                for i in range(50):
                    with tracer.trace(f"span_{threading.current_thread().name}_{i}"):
                        time.sleep(0.001)
                    spans_created.append(1)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(spans_created) == 500

        tracer.shutdown()

    @pytest.mark.asyncio
    async def test_concurrent_async_spans(self):
        """Async spans can be created concurrently"""
        exporter = InMemoryExporter()
        processor = BatchSpanProcessor(exporter, max_batch_size=1000)
        tracer = Tracer(service_name="test", processor=processor)

        async def worker(worker_id):
            for i in range(20):
                async with tracer.trace_async(f"async_span_{worker_id}_{i}"):
                    await asyncio.sleep(0.001)

        await asyncio.gather(*[worker(i) for i in range(20)])

        tracer.processor._flush()
        spans = exporter.get_spans()

        assert len(spans) == 400  # 20 workers * 20 spans

        tracer.shutdown()

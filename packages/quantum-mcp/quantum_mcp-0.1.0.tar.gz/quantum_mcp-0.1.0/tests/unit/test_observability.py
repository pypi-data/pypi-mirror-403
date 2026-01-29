# Description: Tests for observability and tracing infrastructure.
# Description: Validates spans, metrics collection, and event emission.
"""Tests for observability and tracing infrastructure."""

import time

import pytest

from quantum_mcp.orchestration.observability import (
    Event,
    EventEmitter,
    EventSeverity,
    MetricsCollector,
    Span,
    SpanContext,
    SpanStatus,
    Tracer,
)


class TestSpanContext:
    """Test SpanContext model."""

    def test_context_generation(self):
        """Test span context generates unique IDs."""
        ctx1 = SpanContext()
        ctx2 = SpanContext()

        assert ctx1.trace_id != ctx2.trace_id
        assert ctx1.span_id != ctx2.span_id

    def test_context_with_parent(self):
        """Test creating child context."""
        parent = SpanContext()
        child = SpanContext(trace_id=parent.trace_id, parent_id=parent.span_id)

        assert child.trace_id == parent.trace_id
        assert child.parent_id == parent.span_id


class TestSpan:
    """Test Span model."""

    def test_span_creation(self):
        """Test creating a span."""
        span = Span(name="test_operation")

        assert span.name == "test_operation"
        assert span.status == SpanStatus.UNSET
        assert span.context is not None

    def test_span_timing(self):
        """Test span records timing."""
        span = Span(name="timed_operation")
        span.start()
        time.sleep(0.01)  # 10ms
        span.end()

        assert span.duration_ms is not None
        assert span.duration_ms >= 10

    def test_span_attributes(self):
        """Test span attributes."""
        span = Span(name="attributed_operation")
        span.set_attribute("key", "value")
        span.set_attribute("count", 42)

        assert span.attributes["key"] == "value"
        assert span.attributes["count"] == 42

    def test_span_status(self):
        """Test span status transitions."""
        span = Span(name="status_test")
        span.start()
        span.set_status(SpanStatus.OK)
        span.end()

        assert span.status == SpanStatus.OK

    def test_span_error(self):
        """Test span error recording."""
        span = Span(name="error_test")
        span.start()
        span.record_exception(ValueError("test error"))
        span.end()

        assert span.status == SpanStatus.ERROR
        assert span.error_message == "test error"


class TestTracer:
    """Test Tracer for creating spans."""

    @pytest.fixture
    def tracer(self) -> Tracer:
        """Create a tracer."""
        return Tracer(service_name="test-service")

    def test_create_span(self, tracer):
        """Test creating a span."""
        span = tracer.create_span("test_operation")

        assert span is not None
        assert span.name == "test_operation"

    def test_create_child_span(self, tracer):
        """Test creating a child span."""
        parent = tracer.create_span("parent")
        child = tracer.create_span("child", parent=parent)

        assert child.context.trace_id == parent.context.trace_id
        assert child.context.parent_id == parent.context.span_id

    def test_context_manager(self, tracer):
        """Test span as context manager."""
        with tracer.span("context_op") as span:
            span.set_attribute("test", True)
            time.sleep(0.01)

        assert span.duration_ms is not None
        assert span.status == SpanStatus.OK

    def test_context_manager_error(self, tracer):
        """Test span captures exceptions."""
        with pytest.raises(ValueError):
            with tracer.span("error_op") as span:
                raise ValueError("test error")

        assert span.status == SpanStatus.ERROR

    def test_get_active_spans(self, tracer):
        """Test tracking active spans via context manager."""
        # Active spans are tracked through context manager
        with tracer.span("span1") as span1:
            assert len(tracer.get_active_spans()) == 1
            assert tracer.get_active_spans()[0] == span1

        # After context exits, span is no longer active
        assert len(tracer.get_active_spans()) == 0


class TestMetricsCollector:
    """Test MetricsCollector for metrics."""

    @pytest.fixture
    def collector(self) -> MetricsCollector:
        """Create a metrics collector."""
        return MetricsCollector()

    def test_counter_increment(self, collector):
        """Test counter increment."""
        collector.counter("requests", 1)
        collector.counter("requests", 1)
        collector.counter("requests", 1)

        value = collector.get_counter("requests")
        assert value == 3

    def test_counter_with_labels(self, collector):
        """Test counter with labels."""
        collector.counter("requests", 1, labels={"method": "GET"})
        collector.counter("requests", 1, labels={"method": "POST"})
        collector.counter("requests", 1, labels={"method": "GET"})

        assert collector.get_counter("requests", labels={"method": "GET"}) == 2
        assert collector.get_counter("requests", labels={"method": "POST"}) == 1

    def test_gauge_set(self, collector):
        """Test gauge set."""
        collector.gauge("active_agents", 5)
        assert collector.get_gauge("active_agents") == 5

        collector.gauge("active_agents", 3)
        assert collector.get_gauge("active_agents") == 3

    def test_histogram_record(self, collector):
        """Test histogram record."""
        collector.histogram("latency_ms", 100)
        collector.histogram("latency_ms", 150)
        collector.histogram("latency_ms", 200)

        stats = collector.get_histogram_stats("latency_ms")
        assert stats["count"] == 3
        assert stats["sum"] == 450
        assert stats["min"] == 100
        assert stats["max"] == 200

    def test_reset_metrics(self, collector):
        """Test resetting metrics."""
        collector.counter("test", 10)
        collector.reset()

        assert collector.get_counter("test") == 0

    def test_export_metrics(self, collector):
        """Test exporting all metrics."""
        collector.counter("requests", 5)
        collector.gauge("agents", 2)
        collector.histogram("latency", 100)

        exported = collector.export()

        assert "counters" in exported
        assert "gauges" in exported
        assert "histograms" in exported


class TestEventEmitter:
    """Test EventEmitter for structured events."""

    @pytest.fixture
    def emitter(self) -> EventEmitter:
        """Create an event emitter."""
        return EventEmitter()

    def test_emit_event(self, emitter):
        """Test emitting an event."""
        emitter.emit("task.started", {"task_id": "t-123"})

        events = emitter.get_events()
        assert len(events) == 1
        assert events[0].name == "task.started"

    def test_event_severity(self, emitter):
        """Test event severity levels."""
        emitter.emit("info.event", severity=EventSeverity.INFO)
        emitter.emit("error.event", severity=EventSeverity.ERROR)

        events = emitter.get_events()
        assert events[0].severity == EventSeverity.INFO
        assert events[1].severity == EventSeverity.ERROR

    def test_event_subscriber(self, emitter):
        """Test event subscription."""
        received = []

        def handler(event: Event):
            received.append(event)

        emitter.subscribe("task.*", handler)
        emitter.emit("task.started", {})
        emitter.emit("task.completed", {})
        emitter.emit("agent.started", {})

        # Should only receive task.* events
        assert len(received) == 2

    def test_event_buffer_limit(self):
        """Test event buffer respects limit."""
        emitter = EventEmitter(buffer_size=5)

        for i in range(10):
            emitter.emit(f"event.{i}", {})

        events = emitter.get_events()
        assert len(events) == 5
        # Should keep most recent
        assert events[-1].name == "event.9"

    def test_clear_events(self, emitter):
        """Test clearing event buffer."""
        emitter.emit("test", {})
        emitter.clear()

        assert len(emitter.get_events()) == 0


class TestEvent:
    """Test Event model."""

    def test_event_creation(self):
        """Test creating an event."""
        event = Event(
            name="test.event",
            data={"key": "value"},
            severity=EventSeverity.INFO,
        )

        assert event.name == "test.event"
        assert event.data["key"] == "value"
        assert event.timestamp is not None

    def test_event_severity_ordering(self):
        """Test event severity ordering."""
        assert EventSeverity.DEBUG.value < EventSeverity.INFO.value
        assert EventSeverity.INFO.value < EventSeverity.WARNING.value
        assert EventSeverity.WARNING.value < EventSeverity.ERROR.value

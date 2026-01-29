# Description: Observability and tracing infrastructure for the collective.
# Description: Provides spans, metrics collection, and structured event emission.
"""Observability and tracing infrastructure for the collective."""

from __future__ import annotations

import fnmatch
import time
import uuid
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger()


class SpanStatus(str, Enum):
    """Status of a span."""

    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


class SpanContext(BaseModel):
    """Context for distributed tracing."""

    trace_id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
        description="Trace identifier (shared across spans)",
    )
    span_id: str = Field(
        default_factory=lambda: uuid.uuid4().hex[:16],
        description="Unique span identifier",
    )
    parent_id: str | None = Field(
        default=None,
        description="Parent span ID (if this is a child span)",
    )


class Span(BaseModel):
    """A span representing a unit of work."""

    name: str = Field(..., description="Name of the operation")
    context: SpanContext = Field(
        default_factory=SpanContext,
        description="Tracing context",
    )
    status: SpanStatus = Field(
        default=SpanStatus.UNSET,
        description="Span status",
    )
    start_time: float | None = Field(
        default=None,
        description="Start time (monotonic)",
    )
    end_time: float | None = Field(
        default=None,
        description="End time (monotonic)",
    )
    duration_ms: float | None = Field(
        default=None,
        description="Duration in milliseconds",
    )
    attributes: dict[str, Any] = Field(
        default_factory=dict,
        description="Span attributes",
    )
    error_message: str | None = Field(
        default=None,
        description="Error message if status is ERROR",
    )

    def start(self) -> None:
        """Start the span timing."""
        self.start_time = time.monotonic()

    def end(self) -> None:
        """End the span timing."""
        if self.start_time is not None:
            self.end_time = time.monotonic()
            self.duration_ms = (self.end_time - self.start_time) * 1000
            if self.status == SpanStatus.UNSET:
                self.status = SpanStatus.OK

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a span attribute.

        Args:
            key: Attribute key
            value: Attribute value
        """
        self.attributes[key] = value

    def set_status(self, status: SpanStatus) -> None:
        """Set span status.

        Args:
            status: New status
        """
        self.status = status

    def record_exception(self, exception: Exception) -> None:
        """Record an exception on this span.

        Args:
            exception: The exception to record
        """
        self.status = SpanStatus.ERROR
        self.error_message = str(exception)
        self.set_attribute("exception.type", type(exception).__name__)
        self.set_attribute("exception.message", str(exception))


class Tracer:
    """Tracer for creating and managing spans."""

    def __init__(self, service_name: str = "quantum-collective") -> None:
        """Initialize tracer.

        Args:
            service_name: Name of the service being traced
        """
        self._service_name = service_name
        self._active_spans: dict[str, Span] = {}
        self._logger = logger.bind(component="Tracer", service=service_name)

    def create_span(
        self,
        name: str,
        parent: Span | None = None,
    ) -> Span:
        """Create a new span.

        Args:
            name: Name of the operation
            parent: Optional parent span for creating child spans

        Returns:
            New span instance
        """
        if parent:
            context = SpanContext(
                trace_id=parent.context.trace_id,
                parent_id=parent.context.span_id,
            )
        else:
            context = SpanContext()

        span = Span(name=name, context=context)
        span.set_attribute("service.name", self._service_name)

        return span

    @contextmanager
    def span(self, name: str, parent: Span | None = None):
        """Context manager for creating and managing a span.

        Args:
            name: Name of the operation
            parent: Optional parent span

        Yields:
            The created span
        """
        span = self.create_span(name, parent)
        span.start()
        self._active_spans[span.context.span_id] = span

        try:
            yield span
            span.set_status(SpanStatus.OK)
        except Exception as e:
            span.record_exception(e)
            raise
        finally:
            span.end()
            self._active_spans.pop(span.context.span_id, None)

            self._logger.debug(
                "Span completed",
                span_name=span.name,
                duration_ms=span.duration_ms,
                status=span.status.value,
            )

    def get_active_spans(self) -> list[Span]:
        """Get currently active spans.

        Returns:
            List of active spans
        """
        return list(self._active_spans.values())


class MetricsCollector:
    """Collector for metrics (counters, gauges, histograms)."""

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._logger = logger.bind(component="MetricsCollector")

    def _make_key(self, name: str, labels: dict[str, str] | None = None) -> str:
        """Create a key with optional labels.

        Args:
            name: Metric name
            labels: Optional labels

        Returns:
            Key string
        """
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def counter(
        self,
        name: str,
        value: float = 1,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Increment a counter.

        Args:
            name: Counter name
            value: Value to add
            labels: Optional labels
        """
        key = self._make_key(name, labels)
        self._counters[key] += value

    def get_counter(
        self,
        name: str,
        labels: dict[str, str] | None = None,
    ) -> float:
        """Get counter value.

        Args:
            name: Counter name
            labels: Optional labels

        Returns:
            Counter value
        """
        key = self._make_key(name, labels)
        return self._counters.get(key, 0)

    def gauge(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Set a gauge value.

        Args:
            name: Gauge name
            value: Current value
            labels: Optional labels
        """
        key = self._make_key(name, labels)
        self._gauges[key] = value

    def get_gauge(
        self,
        name: str,
        labels: dict[str, str] | None = None,
    ) -> float:
        """Get gauge value.

        Args:
            name: Gauge name
            labels: Optional labels

        Returns:
            Gauge value
        """
        key = self._make_key(name, labels)
        return self._gauges.get(key, 0)

    def histogram(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Record a histogram value.

        Args:
            name: Histogram name
            value: Value to record
            labels: Optional labels
        """
        key = self._make_key(name, labels)
        self._histograms[key].append(value)

    def get_histogram_stats(
        self,
        name: str,
        labels: dict[str, str] | None = None,
    ) -> dict[str, float]:
        """Get histogram statistics.

        Args:
            name: Histogram name
            labels: Optional labels

        Returns:
            Dictionary with count, sum, min, max, avg
        """
        key = self._make_key(name, labels)
        values = self._histograms.get(key, [])

        if not values:
            return {"count": 0, "sum": 0, "min": 0, "max": 0, "avg": 0}

        return {
            "count": len(values),
            "sum": sum(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()

    def export(self) -> dict[str, Any]:
        """Export all metrics.

        Returns:
            Dictionary with all metrics
        """
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                k: self.get_histogram_stats(k) for k in self._histograms.keys()
            },
        }


class EventSeverity(int, Enum):
    """Severity level for events."""

    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class Event(BaseModel):
    """A structured event."""

    name: str = Field(..., description="Event name (e.g., task.started)")
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Event data",
    )
    severity: EventSeverity = Field(
        default=EventSeverity.INFO,
        description="Event severity",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Event timestamp",
    )


class EventEmitter:
    """Emitter for structured events with subscription support."""

    def __init__(self, buffer_size: int = 1000) -> None:
        """Initialize event emitter.

        Args:
            buffer_size: Maximum events to buffer
        """
        self._buffer_size = buffer_size
        self._events: list[Event] = []
        self._subscribers: list[tuple[str, Callable[[Event], None]]] = []
        self._logger = logger.bind(component="EventEmitter")

    def emit(
        self,
        name: str,
        data: dict[str, Any] | None = None,
        severity: EventSeverity = EventSeverity.INFO,
    ) -> Event:
        """Emit an event.

        Args:
            name: Event name
            data: Event data
            severity: Event severity

        Returns:
            The emitted event
        """
        event = Event(
            name=name,
            data=data or {},
            severity=severity,
        )

        # Add to buffer
        self._events.append(event)
        if len(self._events) > self._buffer_size:
            self._events = self._events[-self._buffer_size:]

        # Notify subscribers
        for pattern, handler in self._subscribers:
            if fnmatch.fnmatch(name, pattern):
                try:
                    handler(event)
                except Exception as e:
                    self._logger.error(
                        "Subscriber error",
                        pattern=pattern,
                        error=str(e),
                    )

        return event

    def subscribe(
        self,
        pattern: str,
        handler: Callable[[Event], None],
    ) -> None:
        """Subscribe to events matching a pattern.

        Args:
            pattern: Event name pattern (supports wildcards)
            handler: Function to call for matching events
        """
        self._subscribers.append((pattern, handler))

    def unsubscribe(self, handler: Callable[[Event], None]) -> None:
        """Unsubscribe a handler.

        Args:
            handler: Handler to remove
        """
        self._subscribers = [
            (p, h) for p, h in self._subscribers if h != handler
        ]

    def get_events(
        self,
        name_filter: str | None = None,
        severity_min: EventSeverity | None = None,
    ) -> list[Event]:
        """Get buffered events.

        Args:
            name_filter: Optional name pattern filter
            severity_min: Optional minimum severity filter

        Returns:
            List of matching events
        """
        events = self._events

        if name_filter:
            events = [e for e in events if fnmatch.fnmatch(e.name, name_filter)]

        if severity_min:
            events = [e for e in events if e.severity.value >= severity_min.value]

        return events

    def clear(self) -> None:
        """Clear event buffer."""
        self._events.clear()

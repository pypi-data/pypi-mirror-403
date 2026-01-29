"""
Loggy Distributed Tracing - Track requests across services with spans and traces.
"""

import os
import re
import secrets
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar

import requests

T = TypeVar("T")


class SpanKind(str, Enum):
    CLIENT = "client"
    SERVER = "server"
    PRODUCER = "producer"
    CONSUMER = "consumer"
    INTERNAL = "internal"


class SpanStatus(str, Enum):
    OK = "ok"
    ERROR = "error"
    UNSET = "unset"


@dataclass
class SpanContext:
    trace_id: str
    span_id: str
    trace_flags: int = 1  # Sampled by default
    trace_state: Optional[str] = None


@dataclass
class SpanEvent:
    name: str
    timestamp: str
    attributes: Optional[Dict[str, Any]] = None


@dataclass
class SpanData:
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    service_name: str
    span_kind: str
    start_time: str
    end_time: Optional[str]
    status: str
    status_message: Optional[str]
    attributes: Optional[Dict[str, Any]]
    events: Optional[List[Dict[str, Any]]]
    resource_attributes: Optional[Dict[str, Any]]


@dataclass
class SpanOptions:
    kind: SpanKind = SpanKind.INTERNAL
    attributes: Optional[Dict[str, Any]] = None
    parent: Optional[SpanContext] = None
    start_time: Optional[datetime] = None


@dataclass
class TracerConfig:
    service_name: str
    service_version: Optional[str] = None
    environment: Optional[str] = None
    remote: Optional[Dict[str, Any]] = None


# W3C Trace Context constants
TRACEPARENT_HEADER = "traceparent"
TRACESTATE_HEADER = "tracestate"
TRACE_VERSION = "00"
TRACEPARENT_REGEX = re.compile(r"^([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$")


def generate_trace_id() -> str:
    """Generate a random 128-bit trace ID (32 hex chars)."""
    return secrets.token_hex(16)


def generate_span_id() -> str:
    """Generate a random 64-bit span ID (16 hex chars)."""
    return secrets.token_hex(8)


def parse_traceparent(header: str) -> Optional[SpanContext]:
    """
    Parse a traceparent header into a SpanContext.
    Format: {version}-{trace-id}-{parent-id}-{trace-flags}
    Example: 00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01
    """
    if not header:
        return None

    match = TRACEPARENT_REGEX.match(header.strip())
    if not match:
        return None

    version, trace_id, span_id, flags = match.groups()

    if version != TRACE_VERSION:
        return None

    # Validate not all zeros
    if trace_id == "0" * 32 or span_id == "0" * 16:
        return None

    return SpanContext(
        trace_id=trace_id,
        span_id=span_id,
        trace_flags=int(flags, 16),
    )


def format_traceparent(context: SpanContext) -> str:
    """Format a SpanContext into a traceparent header."""
    flags = f"{context.trace_flags:02x}"
    return f"{TRACE_VERSION}-{context.trace_id}-{context.span_id}-{flags}"


def inject_context(
    context: SpanContext,
    carrier: Dict[str, str],
    trace_state: Optional[str] = None,
) -> Dict[str, str]:
    """Inject trace context into carrier (HTTP headers)."""
    carrier[TRACEPARENT_HEADER] = format_traceparent(context)
    if trace_state:
        carrier[TRACESTATE_HEADER] = trace_state
    return carrier


def extract_context(carrier: Dict[str, str]) -> Optional[SpanContext]:
    """Extract trace context from carrier (HTTP headers)."""
    # Try lowercase first (standard), then other cases
    traceparent = (
        carrier.get(TRACEPARENT_HEADER)
        or carrier.get("Traceparent")
        or carrier.get("TRACEPARENT")
    )

    if not traceparent:
        return None

    return parse_traceparent(traceparent)


class Span:
    """A single span in a trace."""

    def __init__(
        self,
        operation_name: str,
        service_name: str,
        trace_id: str,
        parent_span_id: Optional[str] = None,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None,
        start_time: Optional[datetime] = None,
        resource_attributes: Optional[Dict[str, Any]] = None,
        on_end: Optional[Callable[["Span"], None]] = None,
    ):
        self._context = SpanContext(
            trace_id=trace_id,
            span_id=generate_span_id(),
            trace_flags=1,
        )
        self._operation_name = operation_name
        self._service_name = service_name
        self._span_kind = kind
        self._start_time = start_time or datetime.utcnow()
        self._end_time: Optional[datetime] = None
        self._status = SpanStatus.UNSET
        self._status_message: Optional[str] = None
        self._attributes: Dict[str, Any] = attributes.copy() if attributes else {}
        self._events: List[SpanEvent] = []
        self._parent_span_id = parent_span_id
        self._resource_attributes = resource_attributes
        self._recording = True
        self._on_end = on_end
        self._lock = threading.Lock()

    @property
    def context(self) -> SpanContext:
        return self._context

    @property
    def operation_name(self) -> str:
        return self._operation_name

    @property
    def service_name(self) -> str:
        return self._service_name

    @property
    def start_time(self) -> datetime:
        return self._start_time

    @property
    def end_time(self) -> Optional[datetime]:
        return self._end_time

    @property
    def status(self) -> SpanStatus:
        return self._status

    @property
    def parent_span_id(self) -> Optional[str]:
        return self._parent_span_id

    def set_status(self, status: SpanStatus, message: Optional[str] = None) -> None:
        """Set the span status."""
        with self._lock:
            if not self._recording:
                return
            self._status = status
            self._status_message = message

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a single attribute."""
        with self._lock:
            if not self._recording:
                return
            self._attributes[key] = value

    def set_attributes(self, attributes: Dict[str, Any]) -> None:
        """Set multiple attributes."""
        with self._lock:
            if not self._recording:
                return
            self._attributes.update(attributes)

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add an event to the span."""
        with self._lock:
            if not self._recording:
                return
            self._events.append(SpanEvent(
                name=name,
                timestamp=datetime.utcnow().isoformat() + "Z",
                attributes=attributes,
            ))

    def end(self, end_time: Optional[datetime] = None) -> None:
        """End the span."""
        with self._lock:
            if not self._recording:
                return
            self._end_time = end_time or datetime.utcnow()
            self._recording = False
            on_end = self._on_end

        if on_end:
            on_end(self)

    def is_recording(self) -> bool:
        """Check if the span is still recording."""
        with self._lock:
            return self._recording

    def to_data(self) -> Dict[str, Any]:
        """Convert span to data format for sending to server."""
        with self._lock:
            data: Dict[str, Any] = {
                "traceId": self._context.trace_id,
                "spanId": self._context.span_id,
                "parentSpanId": self._parent_span_id,
                "operationName": self._operation_name,
                "serviceName": self._service_name,
                "spanKind": self._span_kind.value,
                "startTime": self._start_time.isoformat() + "Z",
                "status": self._status.value,
            }

            if self._end_time:
                data["endTime"] = self._end_time.isoformat() + "Z"

            if self._status_message:
                data["statusMessage"] = self._status_message

            if self._attributes:
                data["attributes"] = self._attributes

            if self._events:
                data["events"] = [
                    {
                        "name": e.name,
                        "timestamp": e.timestamp,
                        "attributes": e.attributes,
                    }
                    for e in self._events
                ]

            if self._resource_attributes:
                data["resourceAttributes"] = self._resource_attributes

            return data

    def __enter__(self) -> "Span":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            self.set_status(SpanStatus.ERROR, str(exc_val) if exc_val else None)
            self.add_event("exception", {
                "exception.type": exc_type.__name__ if exc_type else "Error",
                "exception.message": str(exc_val) if exc_val else "",
            })
        else:
            if self._status == SpanStatus.UNSET:
                self.set_status(SpanStatus.OK)
        self.end()


class Tracer:
    """Distributed tracing tracer for Python applications."""

    def __init__(
        self,
        service_name: str,
        service_version: Optional[str] = None,
        environment: Optional[str] = None,
        remote: Optional[Dict[str, Any]] = None,
    ):
        """
        Create a new tracer instance.

        Args:
            service_name: Name of your service (required)
            service_version: Version of your service
            environment: Deployment environment
            remote: Remote configuration dict with keys:
                - token: Project token from loggy.dev (required)
                - endpoint: API endpoint (default: https://loggy.dev/api/traces/ingest)
                - batch_size: Spans to batch before sending (default: 100)
                - flush_interval: Seconds between auto-flushes (default: 5.0)
                - public_key: RSA public key for encryption (optional)
        """
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment

        # Remote config
        self._token: Optional[str] = None
        self._endpoint = "https://loggy.dev/api/traces/ingest"
        self._batch_size = 100
        self._flush_interval = 5.0
        self._public_key: Optional[str] = None

        if remote:
            self._token = remote.get("token")
            self._endpoint = remote.get("endpoint", self._endpoint)
            self._batch_size = remote.get("batch_size", self._batch_size)
            self._flush_interval = remote.get("flush_interval", self._flush_interval)
            self._public_key = remote.get("public_key")

        # Build resource attributes
        self._resource_attributes: Dict[str, Any] = {
            "service.name": service_name,
        }
        if service_version:
            self._resource_attributes["service.version"] = service_version
        if environment:
            self._resource_attributes["deployment.environment"] = environment

        # Span buffer and active spans
        self._span_buffer: List[Dict[str, Any]] = []
        self._buffer_lock = threading.Lock()
        self._active_spans: Dict[str, Span] = {}
        self._active_spans_lock = threading.RLock()
        self._flush_timer: Optional[threading.Timer] = None
        self._stopped = False

        if self._token:
            self._start_flush_timer()

    def _start_flush_timer(self) -> None:
        """Start the periodic flush timer."""
        if self._stopped or not self._token:
            return
        self._flush_timer = threading.Timer(self._flush_interval, self._flush_timer_callback)
        self._flush_timer.daemon = True
        self._flush_timer.start()

    def _flush_timer_callback(self) -> None:
        """Timer callback that flushes and restarts the timer."""
        self.flush()
        self._start_flush_timer()

    def _on_span_end(self, span: Span) -> None:
        """Called when a span ends."""
        # Remove from active spans
        with self._active_spans_lock:
            self._active_spans.pop(span.context.span_id, None)

        # Queue for remote sending
        if self._token:
            with self._buffer_lock:
                self._span_buffer.append(span.to_data())
                should_flush = len(self._span_buffer) >= self._batch_size

            if should_flush:
                threading.Thread(target=self.flush, daemon=True).start()

    def start_span(
        self,
        operation_name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None,
        parent: Optional[SpanContext] = None,
        start_time: Optional[datetime] = None,
    ) -> Span:
        """
        Start a new span.

        Args:
            operation_name: Name of the operation
            kind: Type of span (client, server, internal, etc.)
            attributes: Initial attributes for the span
            parent: Parent span context for trace propagation
            start_time: Custom start time (defaults to now)

        Returns:
            A new Span instance
        """
        # Determine trace ID - either from parent or generate new
        if parent:
            trace_id = parent.trace_id
            parent_span_id = parent.span_id
        else:
            trace_id = generate_trace_id()
            parent_span_id = None

        span = Span(
            operation_name=operation_name,
            service_name=self.service_name,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            kind=kind,
            attributes=attributes,
            start_time=start_time,
            resource_attributes=self._resource_attributes,
            on_end=self._on_span_end,
        )

        # Store as active span
        with self._active_spans_lock:
            self._active_spans[span.context.span_id] = span

        return span

    def inject(self, carrier: Dict[str, str]) -> Dict[str, str]:
        """Inject trace context into carrier (HTTP headers)."""
        with self._active_spans_lock:
            if not self._active_spans:
                return carrier
            # Get the most recently created active span
            current_span = list(self._active_spans.values())[-1]

        return inject_context(current_span.context, carrier)

    def extract(self, carrier: Dict[str, str]) -> Optional[SpanContext]:
        """Extract trace context from carrier (HTTP headers)."""
        return extract_context(carrier)

    def get_current_span(self) -> Optional[Span]:
        """Get the current active span (if any)."""
        with self._active_spans_lock:
            if not self._active_spans:
                return None
            return list(self._active_spans.values())[-1]

    def get_current_context(self) -> Dict[str, Optional[str]]:
        """Get current trace context for log correlation."""
        span = self.get_current_span()
        if not span:
            return {"trace_id": None, "span_id": None}
        return {
            "trace_id": span.context.trace_id,
            "span_id": span.context.span_id,
        }

    def flush(self) -> None:
        """Flush all buffered spans to the server."""
        if not self._token:
            return

        with self._buffer_lock:
            if not self._span_buffer:
                return
            spans_to_send = self._span_buffer.copy()
            self._span_buffer.clear()

        try:
            headers = {
                "Content-Type": "application/json",
                "x-loggy-token": self._token,
            }

            body: Dict[str, Any] = {"spans": spans_to_send}

            if self._public_key:
                from .crypto import encrypt_payload
                encrypted = encrypt_payload(body, self._public_key)
                body = encrypted
                headers["Content-Type"] = "application/json+encrypted"

            response = requests.post(
                self._endpoint,
                json=body,
                headers=headers,
                timeout=10,
            )

            if not response.ok:
                # Put spans back in buffer for retry
                with self._buffer_lock:
                    self._span_buffer = spans_to_send + self._span_buffer

        except Exception:
            # Put spans back in buffer for retry
            with self._buffer_lock:
                self._span_buffer = spans_to_send + self._span_buffer

    def destroy(self) -> None:
        """Stop the tracer and flush remaining spans."""
        self._stopped = True
        if self._flush_timer:
            self._flush_timer.cancel()
            self._flush_timer = None
        self.flush()

    def __enter__(self) -> "Tracer":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.destroy()


def with_span(
    tracer: Tracer,
    operation_name: str,
    fn: Callable[[], T],
    attributes: Optional[Dict[str, Any]] = None,
    kind: SpanKind = SpanKind.INTERNAL,
) -> T:
    """
    Wrap a function with a span.

    Example:
        result = with_span(tracer, "fetch_user", lambda: db.get_user(id))
    """
    parent = tracer.get_current_span()
    span = tracer.start_span(
        operation_name,
        kind=kind,
        attributes=attributes,
        parent=parent.context if parent else None,
    )

    try:
        result = fn()
        span.set_status(SpanStatus.OK)
        return result
    except Exception as e:
        span.set_status(SpanStatus.ERROR, str(e))
        span.add_event("exception", {
            "exception.type": type(e).__name__,
            "exception.message": str(e),
        })
        raise
    finally:
        span.end()

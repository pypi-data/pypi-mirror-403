"""Tests for the Loggy distributed tracing."""

from unittest.mock import MagicMock, patch

import pytest

from loggy import (
    Tracer,
    Span,
    SpanContext,
    SpanKind,
    SpanStatus,
    generate_trace_id,
    generate_span_id,
    parse_traceparent,
    format_traceparent,
    inject_context,
    extract_context,
    with_span,
)


class TestTraceContext:
    """Test cases for W3C Trace Context functions."""

    def test_generate_trace_id(self):
        """Test trace ID generation."""
        trace_id = generate_trace_id()
        assert len(trace_id) == 32
        assert all(c in "0123456789abcdef" for c in trace_id)

    def test_generate_span_id(self):
        """Test span ID generation."""
        span_id = generate_span_id()
        assert len(span_id) == 16
        assert all(c in "0123456789abcdef" for c in span_id)

    def test_parse_traceparent_valid(self):
        """Test parsing a valid traceparent header."""
        header = "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
        context = parse_traceparent(header)

        assert context is not None
        assert context.trace_id == "0af7651916cd43dd8448eb211c80319c"
        assert context.span_id == "b7ad6b7169203331"
        assert context.trace_flags == 1

    def test_parse_traceparent_invalid(self):
        """Test parsing invalid traceparent headers."""
        assert parse_traceparent("") is None
        assert parse_traceparent("invalid") is None
        assert parse_traceparent("00-invalid-invalid-00") is None
        # All zeros is invalid
        assert parse_traceparent("00-00000000000000000000000000000000-0000000000000000-00") is None

    def test_format_traceparent(self):
        """Test formatting a SpanContext to traceparent."""
        context = SpanContext(
            trace_id="0af7651916cd43dd8448eb211c80319c",
            span_id="b7ad6b7169203331",
            trace_flags=1,
        )
        header = format_traceparent(context)
        assert header == "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"

    def test_inject_context(self):
        """Test injecting context into carrier."""
        context = SpanContext(
            trace_id="0af7651916cd43dd8448eb211c80319c",
            span_id="b7ad6b7169203331",
            trace_flags=1,
        )
        carrier = {}
        inject_context(context, carrier)

        assert "traceparent" in carrier
        assert carrier["traceparent"] == "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"

    def test_extract_context(self):
        """Test extracting context from carrier."""
        carrier = {
            "traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
        }
        context = extract_context(carrier)

        assert context is not None
        assert context.trace_id == "0af7651916cd43dd8448eb211c80319c"

    def test_extract_context_case_insensitive(self):
        """Test that context extraction is case insensitive."""
        carrier = {
            "Traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
        }
        context = extract_context(carrier)
        assert context is not None


class TestSpan:
    """Test cases for Span."""

    def test_create_span(self):
        """Test creating a span."""
        span = Span(
            operation_name="test-operation",
            service_name="test-service",
            trace_id=generate_trace_id(),
        )

        assert span.operation_name == "test-operation"
        assert span.service_name == "test-service"
        assert span.is_recording() is True

    def test_span_set_status(self):
        """Test setting span status."""
        span = Span(
            operation_name="test",
            service_name="test",
            trace_id=generate_trace_id(),
        )

        span.set_status(SpanStatus.OK)
        assert span.status == SpanStatus.OK

        span.set_status(SpanStatus.ERROR, "Something went wrong")
        assert span.status == SpanStatus.ERROR

    def test_span_set_attributes(self):
        """Test setting span attributes."""
        span = Span(
            operation_name="test",
            service_name="test",
            trace_id=generate_trace_id(),
        )

        span.set_attribute("key1", "value1")
        span.set_attributes({"key2": "value2", "key3": 123})

        data = span.to_data()
        assert data["attributes"]["key1"] == "value1"
        assert data["attributes"]["key2"] == "value2"
        assert data["attributes"]["key3"] == 123

    def test_span_add_event(self):
        """Test adding events to span."""
        span = Span(
            operation_name="test",
            service_name="test",
            trace_id=generate_trace_id(),
        )

        span.add_event("test-event", {"key": "value"})

        data = span.to_data()
        assert len(data["events"]) == 1
        assert data["events"][0]["name"] == "test-event"

    def test_span_end(self):
        """Test ending a span."""
        span = Span(
            operation_name="test",
            service_name="test",
            trace_id=generate_trace_id(),
        )

        assert span.is_recording() is True
        span.end()
        assert span.is_recording() is False
        assert span.end_time is not None

    def test_span_context_manager(self):
        """Test using span as context manager."""
        with Span(
            operation_name="test",
            service_name="test",
            trace_id=generate_trace_id(),
        ) as span:
            span.set_attribute("key", "value")

        assert span.is_recording() is False
        assert span.status == SpanStatus.OK

    def test_span_context_manager_with_exception(self):
        """Test span context manager handles exceptions."""
        try:
            with Span(
                operation_name="test",
                service_name="test",
                trace_id=generate_trace_id(),
            ) as span:
                raise ValueError("Test error")
        except ValueError:
            pass

        assert span.status == SpanStatus.ERROR


class TestTracer:
    """Test cases for Tracer."""

    def test_create_tracer(self):
        """Test creating a tracer."""
        tracer = Tracer(
            service_name="test-service",
            service_version="1.0.0",
            environment="test",
        )

        assert tracer.service_name == "test-service"
        tracer.destroy()

    def test_start_span(self):
        """Test starting a span."""
        tracer = Tracer(service_name="test-service")
        span = tracer.start_span("test-operation")

        assert span.operation_name == "test-operation"
        assert span.service_name == "test-service"

        span.end()
        tracer.destroy()

    def test_start_span_with_parent(self):
        """Test starting a span with parent context."""
        tracer = Tracer(service_name="test-service")

        parent_context = SpanContext(
            trace_id="0af7651916cd43dd8448eb211c80319c",
            span_id="b7ad6b7169203331",
            trace_flags=1,
        )

        span = tracer.start_span("child-operation", parent=parent_context)

        assert span.context.trace_id == parent_context.trace_id
        assert span.parent_span_id == parent_context.span_id

        span.end()
        tracer.destroy()

    def test_get_current_span(self):
        """Test getting current active span."""
        tracer = Tracer(service_name="test-service")

        assert tracer.get_current_span() is None

        span = tracer.start_span("test-operation")
        assert tracer.get_current_span() == span

        span.end()
        assert tracer.get_current_span() is None

        tracer.destroy()

    def test_context_manager(self):
        """Test using tracer as context manager."""
        with Tracer(service_name="test-service") as tracer:
            span = tracer.start_span("test")
            span.end()


class TestWithSpan:
    """Test cases for with_span helper."""

    def test_with_span_success(self):
        """Test with_span with successful function."""
        tracer = Tracer(service_name="test-service")

        result = with_span(
            tracer,
            "test-operation",
            lambda: "success",
        )

        assert result == "success"
        tracer.destroy()

    def test_with_span_exception(self):
        """Test with_span with function that raises."""
        tracer = Tracer(service_name="test-service")

        with pytest.raises(ValueError):
            with_span(
                tracer,
                "test-operation",
                lambda: (_ for _ in ()).throw(ValueError("Test error")),
            )

        tracer.destroy()

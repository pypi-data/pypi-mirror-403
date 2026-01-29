"""
Loggy Python SDK - A lightweight logger with remote logging, metrics, and tracing.

Usage:
    from loggy import Loggy, Metrics, Tracer

    # Logging
    logger = Loggy(identifier="my-app", remote={"token": "your-token"})
    logger.info("Hello, world!")

    # Metrics
    metrics = Metrics(token="your-token")
    end = metrics.start_request()
    # ... handle request ...
    end(status_code=200)

    # Tracing
    tracer = Tracer(service_name="my-service", remote={"token": "your-token"})
    span = tracer.start_span("operation")
    # ... do work ...
    span.end()
"""

from .loggy import Loggy, LogLevel, LogEntry, RemoteConfig, LoggyConfig
from .metrics import Metrics, MetricsConfig, RequestEndOptions
from .tracing import (
    Tracer,
    Span,
    SpanContext,
    SpanKind,
    SpanStatus,
    TracerConfig,
    SpanOptions,
    generate_trace_id,
    generate_span_id,
    parse_traceparent,
    format_traceparent,
    inject_context,
    extract_context,
    with_span,
)
from .middleware import (
    flask_tracing_middleware,
    flask_metrics_middleware,
    flask_logging_middleware,
    fastapi_tracing_middleware,
    fastapi_metrics_middleware,
    fastapi_logging_middleware,
)
from .crypto import encrypt_payload

__version__ = "0.1.1"
__all__ = [
    # Logging
    "Loggy",
    "LogLevel",
    "LogEntry",
    "RemoteConfig",
    "LoggyConfig",
    # Metrics
    "Metrics",
    "MetricsConfig",
    "RequestEndOptions",
    # Tracing
    "Tracer",
    "Span",
    "SpanContext",
    "SpanKind",
    "SpanStatus",
    "TracerConfig",
    "SpanOptions",
    "generate_trace_id",
    "generate_span_id",
    "parse_traceparent",
    "format_traceparent",
    "inject_context",
    "extract_context",
    "with_span",
    # Middleware
    "flask_tracing_middleware",
    "flask_metrics_middleware",
    "flask_logging_middleware",
    "fastapi_tracing_middleware",
    "fastapi_metrics_middleware",
    "fastapi_logging_middleware",
    # Crypto
    "encrypt_payload",
]

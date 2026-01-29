"""
Middleware for Flask and FastAPI applications.
Provides automatic tracing, metrics, and logging for HTTP requests.
"""

import time
from datetime import datetime
from typing import Any, Callable, List, Optional

from .loggy import Loggy
from .metrics import Metrics
from .tracing import SpanKind, SpanStatus, Tracer


# ============================================================================
# Flask Middleware
# ============================================================================


def flask_tracing_middleware(
    tracer: Tracer,
    ignore_routes: Optional[List[str]] = None,
    record_request_body: bool = False,
    record_response_body: bool = False,
) -> Callable:
    """
    Create Flask middleware for automatic request tracing.

    Args:
        tracer: The Tracer instance to use
        ignore_routes: List of route prefixes to ignore
        record_request_body: Whether to record request body (default: False)
        record_response_body: Whether to record response body (default: False)

    Returns:
        A Flask before_request/after_request middleware setup function

    Usage:
        from flask import Flask
        from loggy import Tracer, flask_tracing_middleware

        app = Flask(__name__)
        tracer = Tracer(service_name="my-service", remote={"token": "..."})
        flask_tracing_middleware(tracer)(app)
    """
    ignore_routes = ignore_routes or []

    def setup(app):
        @app.before_request
        def before_request():
            from flask import g, request

            # Skip ignored routes
            for route in ignore_routes:
                if request.path.startswith(route):
                    return

            # Extract parent context from incoming headers
            headers = {k: v for k, v in request.headers}
            parent_context = tracer.extract(headers)

            # Build operation name
            operation_name = f"{request.method} {request.path}"

            # Start span
            span = tracer.start_span(
                operation_name,
                kind=SpanKind.SERVER,
                parent=parent_context,
                attributes={
                    "http.method": request.method,
                    "http.url": request.url,
                    "http.target": request.path,
                    "http.host": request.host,
                    "http.scheme": request.scheme,
                    "http.user_agent": request.user_agent.string or "",
                    "net.peer.ip": request.remote_addr or "",
                },
            )

            # Record request body if enabled
            if record_request_body and request.data:
                try:
                    body_str = request.data.decode("utf-8")
                    if len(body_str) <= 1024:
                        span.set_attribute("http.request.body", body_str)
                    span.set_attribute("http.request_content_length", len(body_str))
                except Exception:
                    pass

            g.loggy_span = span

        @app.after_request
        def after_request(response):
            from flask import g

            span = getattr(g, "loggy_span", None)
            if span:
                span.set_attribute("http.status_code", response.status_code)

                if response.status_code >= 400:
                    span.set_status(SpanStatus.ERROR, f"HTTP {response.status_code}")
                else:
                    span.set_status(SpanStatus.OK)

                span.end()

            return response

        @app.teardown_request
        def teardown_request(exception):
            from flask import g

            span = getattr(g, "loggy_span", None)
            if span and span.is_recording():
                if exception:
                    span.set_status(SpanStatus.ERROR, str(exception))
                    span.add_event("exception", {
                        "exception.type": type(exception).__name__,
                        "exception.message": str(exception),
                    })
                span.end()

    return setup


def flask_metrics_middleware(metrics: Metrics) -> Callable:
    """
    Create Flask middleware for automatic metrics tracking.

    Args:
        metrics: The Metrics instance to use

    Returns:
        A Flask middleware setup function

    Usage:
        from flask import Flask
        from loggy import Metrics, flask_metrics_middleware

        app = Flask(__name__)
        metrics = Metrics(token="...")
        flask_metrics_middleware(metrics)(app)
    """

    def setup(app):
        @app.before_request
        def before_request():
            from flask import g

            g.loggy_metrics_timer = metrics.start_request()

        @app.after_request
        def after_request(response):
            from flask import g, request

            timer = getattr(g, "loggy_metrics_timer", None)
            if timer:
                timer.end(
                    status_code=response.status_code,
                    path=request.path,
                    method=request.method,
                    bytes_out=response.content_length,
                )

            return response

    return setup


def flask_logging_middleware(logger: Loggy) -> Callable:
    """
    Create Flask middleware for request logging.

    Args:
        logger: The Loggy instance to use

    Returns:
        A Flask middleware setup function

    Usage:
        from flask import Flask
        from loggy import Loggy, flask_logging_middleware

        app = Flask(__name__)
        logger = Loggy(identifier="my-app")
        flask_logging_middleware(logger)(app)
    """

    def setup(app):
        @app.before_request
        def before_request():
            from flask import g

            g.loggy_start_time = time.time()

        @app.after_request
        def after_request(response):
            from flask import g, request

            start_time = getattr(g, "loggy_start_time", None)
            if start_time:
                duration = time.time() - start_time
                logger.info(
                    f"{request.method} {request.path}",
                    metadata={
                        "status": response.status_code,
                        "duration": f"{duration * 1000:.2f}ms",
                        "method": request.method,
                        "path": request.path,
                        "ip": request.remote_addr,
                    },
                )

            return response

    return setup


# ============================================================================
# FastAPI/Starlette Middleware
# ============================================================================


def fastapi_tracing_middleware(
    tracer: Tracer,
    ignore_routes: Optional[List[str]] = None,
    record_request_body: bool = False,
    record_response_body: bool = False,
) -> Any:
    """
    Create FastAPI/Starlette middleware for automatic request tracing.

    Args:
        tracer: The Tracer instance to use
        ignore_routes: List of route prefixes to ignore
        record_request_body: Whether to record request body (default: False)
        record_response_body: Whether to record response body (default: False)

    Returns:
        A Starlette middleware class

    Usage:
        from fastapi import FastAPI
        from loggy import Tracer, fastapi_tracing_middleware

        app = FastAPI()
        tracer = Tracer(service_name="my-service", remote={"token": "..."})
        app.add_middleware(fastapi_tracing_middleware(tracer))
    """
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request

    ignore_routes = ignore_routes or []

    class TracingMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            # Skip ignored routes
            for route in ignore_routes:
                if request.url.path.startswith(route):
                    return await call_next(request)

            # Extract parent context from incoming headers
            headers = dict(request.headers)
            parent_context = tracer.extract(headers)

            # Build operation name
            operation_name = f"{request.method} {request.url.path}"

            # Start span
            span = tracer.start_span(
                operation_name,
                kind=SpanKind.SERVER,
                parent=parent_context,
                attributes={
                    "http.method": request.method,
                    "http.url": str(request.url),
                    "http.target": request.url.path,
                    "http.host": request.url.hostname or "",
                    "http.scheme": request.url.scheme,
                    "http.user_agent": request.headers.get("user-agent", ""),
                    "net.peer.ip": request.client.host if request.client else "",
                },
            )

            try:
                response = await call_next(request)

                span.set_attribute("http.status_code", response.status_code)

                if response.status_code >= 400:
                    span.set_status(SpanStatus.ERROR, f"HTTP {response.status_code}")
                else:
                    span.set_status(SpanStatus.OK)

                return response

            except Exception as e:
                span.set_status(SpanStatus.ERROR, str(e))
                span.add_event("exception", {
                    "exception.type": type(e).__name__,
                    "exception.message": str(e),
                })
                raise

            finally:
                span.end()

    return TracingMiddleware


def fastapi_metrics_middleware(metrics: Metrics) -> Any:
    """
    Create FastAPI/Starlette middleware for automatic metrics tracking.

    Args:
        metrics: The Metrics instance to use

    Returns:
        A Starlette middleware class

    Usage:
        from fastapi import FastAPI
        from loggy import Metrics, fastapi_metrics_middleware

        app = FastAPI()
        metrics = Metrics(token="...")
        app.add_middleware(fastapi_metrics_middleware(metrics))
    """
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request

    class MetricsMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            timer = metrics.start_request()

            response = await call_next(request)

            timer.end(
                status_code=response.status_code,
                path=request.url.path,
                method=request.method,
            )

            return response

    return MetricsMiddleware


def fastapi_logging_middleware(logger: Loggy) -> Any:
    """
    Create FastAPI/Starlette middleware for request logging.

    Args:
        logger: The Loggy instance to use

    Returns:
        A Starlette middleware class

    Usage:
        from fastapi import FastAPI
        from loggy import Loggy, fastapi_logging_middleware

        app = FastAPI()
        logger = Loggy(identifier="my-app")
        app.add_middleware(fastapi_logging_middleware(logger))
    """
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request

    class LoggingMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            start_time = time.time()

            response = await call_next(request)

            duration = time.time() - start_time
            logger.info(
                f"{request.method} {request.url.path}",
                metadata={
                    "status": response.status_code,
                    "duration": f"{duration * 1000:.2f}ms",
                    "method": request.method,
                    "path": request.url.path,
                    "ip": request.client.host if request.client else "",
                },
            )

            return response

    return LoggingMiddleware

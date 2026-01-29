"""
Loggy Performance Metrics - Framework-agnostic performance tracking for Python.
"""

import json
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypeVar

import requests

T = TypeVar("T")


@dataclass
class MetricsConfig:
    token: str
    endpoint: str = "https://loggy.dev/api/metrics/ingest"
    flush_interval: float = 60.0  # seconds
    disabled: bool = False


@dataclass
class RequestEndOptions:
    status_code: Optional[int] = None
    bytes_in: Optional[int] = None
    bytes_out: Optional[int] = None
    path: Optional[str] = None
    method: Optional[str] = None


@dataclass
class MetricBucket:
    timestamp: datetime
    path: Optional[str] = None
    method: Optional[str] = None
    request_count: int = 0
    total_duration_ms: int = 0
    min_duration_ms: Optional[int] = None
    max_duration_ms: Optional[int] = None
    total_bytes_in: int = 0
    total_bytes_out: int = 0
    status_2xx: int = 0
    status_3xx: int = 0
    status_4xx: int = 0
    status_5xx: int = 0


def _round_to_minute(dt: datetime) -> datetime:
    """Round a datetime to the start of its minute."""
    return dt.replace(second=0, microsecond=0)


def _get_bucket_key(dt: datetime, path: Optional[str], method: Optional[str]) -> str:
    """Get the bucket key for a timestamp, path, and method."""
    time_key = _round_to_minute(dt).isoformat()
    return f"{time_key}|{path or ''}|{method or ''}"


def _get_status_category(status_code: int) -> Optional[str]:
    """Categorize a status code into 2xx, 3xx, 4xx, or 5xx."""
    if 200 <= status_code < 300:
        return "2xx"
    elif 300 <= status_code < 400:
        return "3xx"
    elif 400 <= status_code < 500:
        return "4xx"
    elif 500 <= status_code < 600:
        return "5xx"
    return None


class RequestTimer:
    """Timer returned by start_request() to end the measurement."""

    def __init__(self, metrics: "Metrics", start_time: datetime, start_ns: int):
        self._metrics = metrics
        self._start_time = start_time
        self._start_ns = start_ns

    def end(
        self,
        status_code: Optional[int] = None,
        bytes_in: Optional[int] = None,
        bytes_out: Optional[int] = None,
        path: Optional[str] = None,
        method: Optional[str] = None,
    ) -> None:
        """End the request measurement and record the metrics."""
        duration_ms = int((time.time_ns() - self._start_ns) / 1_000_000)
        self._metrics._record_request(
            self._start_time,
            duration_ms,
            RequestEndOptions(
                status_code=status_code,
                bytes_in=bytes_in,
                bytes_out=bytes_out,
                path=path,
                method=method,
            ),
        )

    def __call__(
        self,
        status_code: Optional[int] = None,
        bytes_in: Optional[int] = None,
        bytes_out: Optional[int] = None,
        path: Optional[str] = None,
        method: Optional[str] = None,
    ) -> None:
        """Allow calling the timer directly as a function."""
        self.end(status_code, bytes_in, bytes_out, path, method)


class Metrics:
    """Performance metrics tracker for Python applications."""

    def __init__(
        self,
        token: str,
        endpoint: str = "https://loggy.dev/api/metrics/ingest",
        flush_interval: float = 60.0,
        disabled: bool = False,
    ):
        """
        Create a new metrics tracker.

        Args:
            token: Project token from loggy.dev
            endpoint: API endpoint for metrics ingestion
            flush_interval: Seconds between auto-flushes (default: 60.0)
            disabled: Disable metrics collection
        """
        self.token = token
        self.endpoint = endpoint
        self.flush_interval = flush_interval
        self.disabled = disabled

        self._buckets: Dict[str, MetricBucket] = {}
        self._bucket_lock = threading.Lock()
        self._flush_timer: Optional[threading.Timer] = None
        self._stopped = False

        if not disabled and token:
            self._start_flush_timer()

    def _start_flush_timer(self) -> None:
        """Start the periodic flush timer."""
        if self._stopped or self.disabled:
            return
        self._flush_timer = threading.Timer(self.flush_interval, self._flush_timer_callback)
        self._flush_timer.daemon = True
        self._flush_timer.start()

    def _flush_timer_callback(self) -> None:
        """Timer callback that flushes and restarts the timer."""
        self.flush()
        self._start_flush_timer()

    def _get_or_create_bucket(
        self, timestamp: datetime, path: Optional[str], method: Optional[str]
    ) -> MetricBucket:
        """Get or create a bucket for the given timestamp, path, and method."""
        key = _get_bucket_key(timestamp, path, method)
        if key not in self._buckets:
            self._buckets[key] = MetricBucket(
                timestamp=_round_to_minute(timestamp),
                path=path,
                method=method,
            )
        return self._buckets[key]

    def _record_request(
        self, start_time: datetime, duration_ms: int, options: RequestEndOptions
    ) -> None:
        """Record a completed request into the appropriate bucket."""
        with self._bucket_lock:
            path = options.path
            method = options.method.upper() if options.method else None
            bucket = self._get_or_create_bucket(start_time, path, method)

            bucket.request_count += 1
            bucket.total_duration_ms += duration_ms

            if bucket.min_duration_ms is None or duration_ms < bucket.min_duration_ms:
                bucket.min_duration_ms = duration_ms
            if bucket.max_duration_ms is None or duration_ms > bucket.max_duration_ms:
                bucket.max_duration_ms = duration_ms

            if options.bytes_in:
                bucket.total_bytes_in += options.bytes_in
            if options.bytes_out:
                bucket.total_bytes_out += options.bytes_out

            if options.status_code:
                category = _get_status_category(options.status_code)
                if category == "2xx":
                    bucket.status_2xx += 1
                elif category == "3xx":
                    bucket.status_3xx += 1
                elif category == "4xx":
                    bucket.status_4xx += 1
                elif category == "5xx":
                    bucket.status_5xx += 1

    def start_request(self) -> RequestTimer:
        """
        Start tracking a request. Returns a timer to call when the request ends.

        Example:
            end = metrics.start_request()
            # ... handle request ...
            end(status_code=200, bytes_in=1024, bytes_out=2048)
        """
        return RequestTimer(self, datetime.now(), time.time_ns())

    def record(
        self,
        duration_ms: int,
        status_code: Optional[int] = None,
        bytes_in: Optional[int] = None,
        bytes_out: Optional[int] = None,
        path: Optional[str] = None,
        method: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Record a pre-measured request.

        Example:
            metrics.record(
                duration_ms=150,
                status_code=200,
                bytes_in=1024,
                bytes_out=4096,
            )
        """
        self._record_request(
            timestamp or datetime.now(),
            duration_ms,
            RequestEndOptions(
                status_code=status_code,
                bytes_in=bytes_in,
                bytes_out=bytes_out,
                path=path,
                method=method,
            ),
        )

    def track_request(self, handler: Callable[[], T]) -> T:
        """
        Track a request by wrapping a handler function.

        Example:
            result = metrics.track_request(lambda: handle_request(req))
        """
        timer = self.start_request()
        try:
            result = handler()
            # Try to extract status_code from result if it's a dict
            status_code = None
            bytes_in = None
            bytes_out = None
            if isinstance(result, dict):
                status_code = result.get("status_code")
                bytes_in = result.get("bytes_in")
                bytes_out = result.get("bytes_out")
            timer.end(status_code=status_code, bytes_in=bytes_in, bytes_out=bytes_out)
            return result
        except Exception:
            timer.end(status_code=500)
            raise

    def flush(self) -> None:
        """Flush all collected metrics to the server."""
        if self.disabled or not self.token:
            return

        with self._bucket_lock:
            if not self._buckets:
                return

            # Get all buckets except the current minute (still collecting)
            current_time_key = _round_to_minute(datetime.now()).isoformat()
            buckets_to_send: List[MetricBucket] = []
            keys_to_delete: List[str] = []

            for key, bucket in self._buckets.items():
                if not key.startswith(current_time_key):
                    buckets_to_send.append(bucket)
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                del self._buckets[key]

        if not buckets_to_send:
            return

        # Transform to API format
        metrics = []
        for b in buckets_to_send:
            m: Dict[str, Any] = {
                "timestamp": b.timestamp.isoformat() + "Z",
                "requestCount": b.request_count,
                "totalDurationMs": b.total_duration_ms,
                "totalBytesIn": b.total_bytes_in,
                "totalBytesOut": b.total_bytes_out,
                "status2xx": b.status_2xx,
                "status3xx": b.status_3xx,
                "status4xx": b.status_4xx,
                "status5xx": b.status_5xx,
            }
            if b.path:
                m["path"] = b.path
            if b.method:
                m["method"] = b.method
            if b.min_duration_ms is not None:
                m["minDurationMs"] = b.min_duration_ms
            if b.max_duration_ms is not None:
                m["maxDurationMs"] = b.max_duration_ms
            metrics.append(m)

        try:
            response = requests.post(
                self.endpoint,
                json={"metrics": metrics},
                headers={
                    "Content-Type": "application/json",
                    "x-loggy-token": self.token,
                },
                timeout=10,
            )

            if not response.ok:
                # Re-add failed buckets for retry
                with self._bucket_lock:
                    for bucket in buckets_to_send:
                        key = _get_bucket_key(bucket.timestamp, bucket.path, bucket.method)
                        if key not in self._buckets:
                            self._buckets[key] = bucket

        except Exception:
            # Re-add failed buckets for retry
            with self._bucket_lock:
                for bucket in buckets_to_send:
                    key = _get_bucket_key(bucket.timestamp, bucket.path, bucket.method)
                    if key not in self._buckets:
                        self._buckets[key] = bucket

    def get_pending_count(self) -> int:
        """Get current pending metrics count (for debugging)."""
        with self._bucket_lock:
            return sum(b.request_count for b in self._buckets.values())

    def destroy(self) -> None:
        """Flush and stop the metrics tracker."""
        self._stopped = True
        if self._flush_timer:
            self._flush_timer.cancel()
            self._flush_timer = None

        # Force flush all buckets including current
        with self._bucket_lock:
            all_buckets = list(self._buckets.values())
            self._buckets.clear()

        if not all_buckets or self.disabled:
            return

        metrics = []
        for b in all_buckets:
            m: Dict[str, Any] = {
                "timestamp": b.timestamp.isoformat() + "Z",
                "requestCount": b.request_count,
                "totalDurationMs": b.total_duration_ms,
                "totalBytesIn": b.total_bytes_in,
                "totalBytesOut": b.total_bytes_out,
                "status2xx": b.status_2xx,
                "status3xx": b.status_3xx,
                "status4xx": b.status_4xx,
                "status5xx": b.status_5xx,
            }
            if b.path:
                m["path"] = b.path
            if b.method:
                m["method"] = b.method
            if b.min_duration_ms is not None:
                m["minDurationMs"] = b.min_duration_ms
            if b.max_duration_ms is not None:
                m["maxDurationMs"] = b.max_duration_ms
            metrics.append(m)

        try:
            requests.post(
                self.endpoint,
                json={"metrics": metrics},
                headers={
                    "Content-Type": "application/json",
                    "x-loggy-token": self.token,
                },
                timeout=10,
            )
        except Exception:
            pass  # Ignore errors on shutdown

    def __enter__(self) -> "Metrics":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.destroy()

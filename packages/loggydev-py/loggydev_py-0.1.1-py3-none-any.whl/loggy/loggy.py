"""
Loggy - A lightweight and colorful logger for Python applications.
"""

import json
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import requests

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


@dataclass
class LogEntry:
    level: str
    message: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


@dataclass
class RemoteConfig:
    token: str
    endpoint: str = "https://loggy.dev/api/logs/ingest"
    batch_size: int = 50
    flush_interval: float = 5.0  # seconds
    public_key: Optional[str] = None


@dataclass
class LoggyConfig:
    identifier: str
    color: bool = True
    compact: bool = False
    timestamp: bool = True
    remote: Optional[RemoteConfig] = None


# Color mappings
LEVEL_COLORS = {
    "LOG": "\033[38;2;173;216;230m",    # Light blue
    "INFO": "\033[38;2;173;216;230m",   # Light blue
    "WARN": "\033[38;2;255;191;0m",     # Amber
    "ERROR": "\033[38;2;204;85;0m",     # Burnt orange
}

DATE_COLOR = "\033[38;2;159;43;104m"    # Magenta
TIME_COLOR = "\033[38;2;194;178;128m"   # Tan
ID_COLOR = "\033[38;2;178;190;181m"     # Silver
RESET = "\033[0m"


class Loggy:
    """A lightweight and colorful logger for Python applications."""

    def __init__(
        self,
        identifier: str,
        color: bool = True,
        compact: bool = False,
        timestamp: bool = True,
        remote: Optional[Dict[str, Any]] = None,
        capture_stdout: bool = False,
        capture_exceptions: bool = False,
    ):
        """
        Create a new Loggy logger instance.

        Args:
            identifier: Label for your app/service
            color: Enable colored output (default: True)
            compact: Compact mode for object inspection (default: False)
            timestamp: Show timestamps in log output (default: True)
            remote: Remote logging configuration dict with keys:
                - token: Project token from loggy.dev (required)
                - endpoint: API endpoint (default: https://loggy.dev/api/logs/ingest)
                - batch_size: Logs to batch before sending (default: 50)
                - flush_interval: Seconds between auto-flushes (default: 5.0)
                - public_key: RSA public key for encryption (optional)
            capture_stdout: Intercept print() calls and send to Loggy (default: False)
            capture_exceptions: Capture uncaught exceptions (default: False)
        """
        self.identifier = identifier
        self.color = color and COLORAMA_AVAILABLE or color
        self.compact = compact
        self.timestamp = timestamp

        # Remote logging setup
        self.remote: Optional[RemoteConfig] = None
        self._log_buffer: List[LogEntry] = []
        self._buffer_lock = threading.Lock()
        self._flush_timer: Optional[threading.Timer] = None
        self._stopped = False

        # Capture settings
        self._capture_stdout = capture_stdout
        self._capture_exceptions = capture_exceptions
        self._original_stdout: Optional[Any] = None
        self._original_stderr: Optional[Any] = None
        self._original_excepthook: Optional[Callable] = None
        self._stdout_captured = False
        self._exceptions_captured = False

        if remote and remote.get("token"):
            self.remote = RemoteConfig(
                token=remote["token"],
                endpoint=remote.get("endpoint", "https://loggy.dev/api/logs/ingest"),
                batch_size=remote.get("batch_size", 50),
                flush_interval=remote.get("flush_interval", 5.0),
                public_key=remote.get("public_key"),
            )
            self._start_flush_timer()

        # Set up capture if enabled
        if self._capture_stdout:
            self._setup_stdout_capture()
        if self._capture_exceptions:
            self._setup_exception_capture()

    def _start_flush_timer(self) -> None:
        """Start the periodic flush timer."""
        if self._stopped or not self.remote:
            return
        self._flush_timer = threading.Timer(self.remote.flush_interval, self._flush_timer_callback)
        self._flush_timer.daemon = True
        self._flush_timer.start()

    def _flush_timer_callback(self) -> None:
        """Timer callback that flushes and restarts the timer."""
        self.flush()
        self._start_flush_timer()

    def _format_timestamp(self) -> str:
        """Format the current timestamp."""
        now = datetime.now()
        date_str = now.strftime("%m/%d/%Y")
        time_str = now.strftime("%H:%M:%S")

        if not self.color:
            return f"{date_str} {time_str}"

        return f"{DATE_COLOR}{date_str}{RESET} {TIME_COLOR}{time_str}{RESET}"

    def _format_level(self, level: str) -> str:
        """Format the log level."""
        if not self.color:
            return f"[{level}]"

        color = LEVEL_COLORS.get(level, "")
        return f"[{color}{level}{RESET}]"

    def _format_identifier(self) -> str:
        """Format the identifier."""
        if not self.color:
            return self.identifier
        return f"{ID_COLOR}{self.identifier}{RESET}"

    def _format_metadata(self, metadata: Optional[Dict[str, Any]]) -> str:
        """Format metadata as JSON."""
        if not metadata:
            return ""

        if self.compact:
            return "\n" + json.dumps(metadata, default=str)
        return "\n" + json.dumps(metadata, indent=2, default=str)

    def _log(
        self,
        level_label: str,
        level: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        file: Any = None,
    ) -> None:
        """Internal logging method."""
        # Format and print to console
        parts = []
        if self.timestamp:
            parts.append(self._format_timestamp())
        parts.append(self._format_level(level_label))
        parts.append(f"{self._format_identifier()}: {message}")

        output = " ".join(parts) + self._format_metadata(metadata)

        if file is None:
            file = sys.stderr if level == "error" else sys.stdout
        print(output, file=file)

        # Queue for remote logging
        self._queue_log(LogEntry(
            level=level,
            message=message,
            metadata=metadata,
            tags=tags,
            timestamp=datetime.utcnow().isoformat() + "Z",
        ))

    def _queue_log(self, entry: LogEntry) -> None:
        """Queue a log entry for remote sending."""
        if not self.remote:
            return

        with self._buffer_lock:
            self._log_buffer.append(entry)
            should_flush = len(self._log_buffer) >= self.remote.batch_size

        if should_flush:
            threading.Thread(target=self.flush, daemon=True).start()

    def log(
        self,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> None:
        """Log a message at debug level."""
        self._log("LOG", "debug", message, metadata, tags)

    def debug(
        self,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> None:
        """Log a message at debug level (alias for log)."""
        self._log("LOG", "debug", message, metadata, tags)

    def info(
        self,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> None:
        """Log a message at info level."""
        self._log("INFO", "info", message, metadata, tags)

    def warn(
        self,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> None:
        """Log a message at warn level."""
        self._log("WARN", "warn", message, metadata, tags)

    def warning(
        self,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> None:
        """Log a message at warn level (alias for warn)."""
        self._log("WARN", "warn", message, metadata, tags)

    def error(
        self,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> None:
        """Log a message at error level."""
        self._log("ERROR", "error", message, metadata, tags, file=sys.stderr)

    def blank(self, lines: int = 1) -> None:
        """Print blank lines."""
        print("\n" * lines, end="")

    def flush(self) -> None:
        """Flush all buffered logs to the remote server."""
        if not self.remote:
            return

        with self._buffer_lock:
            if not self._log_buffer:
                return
            logs_to_send = self._log_buffer.copy()
            self._log_buffer.clear()

        try:
            # Convert LogEntry objects to dicts
            logs_data = []
            for entry in logs_to_send:
                log_dict = {
                    "level": entry.level,
                    "message": entry.message,
                    "timestamp": entry.timestamp,
                }
                if entry.metadata:
                    log_dict["metadata"] = entry.metadata
                if entry.tags:
                    log_dict["tags"] = entry.tags
                logs_data.append(log_dict)

            headers = {
                "Content-Type": "application/json",
                "x-loggy-token": self.remote.token,
            }

            body = {"logs": logs_data}

            # Encrypt if public key is provided
            if self.remote.public_key:
                from .crypto import encrypt_payload
                encrypted = encrypt_payload(body, self.remote.public_key)
                body = encrypted
                headers["Content-Type"] = "application/json+encrypted"

            response = requests.post(
                self.remote.endpoint,
                json=body,
                headers=headers,
                timeout=10,
            )

            if not response.ok:
                # Put logs back in buffer for retry
                with self._buffer_lock:
                    self._log_buffer = logs_to_send + self._log_buffer

        except Exception:
            # Put logs back in buffer for retry
            with self._buffer_lock:
                self._log_buffer = logs_to_send + self._log_buffer

    def _setup_stdout_capture(self) -> None:
        """Set up stdout/stderr capture to intercept print() calls."""
        if self._stdout_captured:
            return

        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr

        # Create wrapper classes that intercept writes
        loggy_instance = self

        class LoggyStdoutWrapper:
            def __init__(self, original, level: str):
                self._original = original
                self._level = level
                self._buffer = ""

            def write(self, text: str) -> int:
                # Write to original stdout/stderr
                result = self._original.write(text)
                # Buffer the text and log complete lines
                self._buffer += text
                while "\n" in self._buffer:
                    line, self._buffer = self._buffer.split("\n", 1)
                    if line.strip():  # Don't log empty lines
                        loggy_instance._queue_log(LogEntry(
                            level=self._level,
                            message=line.strip(),
                            timestamp=datetime.utcnow().isoformat() + "Z",
                        ))
                return result

            def flush(self) -> None:
                self._original.flush()
                # Flush any remaining buffer content
                if self._buffer.strip():
                    loggy_instance._queue_log(LogEntry(
                        level=self._level,
                        message=self._buffer.strip(),
                        timestamp=datetime.utcnow().isoformat() + "Z",
                    ))
                    self._buffer = ""

            def __getattr__(self, name: str) -> Any:
                return getattr(self._original, name)

        sys.stdout = LoggyStdoutWrapper(self._original_stdout, "info")
        sys.stderr = LoggyStdoutWrapper(self._original_stderr, "error")
        self._stdout_captured = True

    def _setup_exception_capture(self) -> None:
        """Set up exception hook to capture uncaught exceptions."""
        if self._exceptions_captured:
            return

        self._original_excepthook = sys.excepthook
        loggy_instance = self

        def loggy_excepthook(exc_type, exc_value, exc_traceback):
            import traceback
            tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            tb_str = "".join(tb_lines)

            loggy_instance._queue_log(LogEntry(
                level="error",
                message=f"Uncaught Exception: {exc_type.__name__}: {exc_value}",
                metadata={"traceback": tb_str, "exception_type": exc_type.__name__},
                timestamp=datetime.utcnow().isoformat() + "Z",
            ))
            # Flush immediately on exception
            loggy_instance.flush()

            # Call original excepthook
            if loggy_instance._original_excepthook:
                loggy_instance._original_excepthook(exc_type, exc_value, exc_traceback)

        sys.excepthook = loggy_excepthook
        self._exceptions_captured = True

    def restore_stdout(self) -> None:
        """Restore original stdout/stderr."""
        if not self._stdout_captured:
            return
        if self._original_stdout:
            sys.stdout = self._original_stdout
        if self._original_stderr:
            sys.stderr = self._original_stderr
        self._stdout_captured = False

    def restore_excepthook(self) -> None:
        """Restore original exception hook."""
        if not self._exceptions_captured:
            return
        if self._original_excepthook:
            sys.excepthook = self._original_excepthook
        self._exceptions_captured = False

    def enable_stdout_capture(self) -> None:
        """Enable stdout capture after initialization."""
        self._capture_stdout = True
        self._setup_stdout_capture()

    def enable_exception_capture(self) -> None:
        """Enable exception capture after initialization."""
        self._capture_exceptions = True
        self._setup_exception_capture()

    def destroy(self) -> None:
        """Stop the logger and flush remaining logs."""
        self._stopped = True
        if self._flush_timer:
            self._flush_timer.cancel()
            self._flush_timer = None
        self.restore_stdout()
        self.restore_excepthook()
        self.flush()

    def __enter__(self) -> "Loggy":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.destroy()

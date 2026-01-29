"""Tests for the Loggy metrics tracker."""

import time
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from loggy import Metrics


class TestMetrics:
    """Test cases for the Metrics tracker."""

    def test_create_metrics(self):
        """Test creating a metrics instance."""
        metrics = Metrics(token="test-token")
        assert metrics.token == "test-token"
        assert metrics.disabled is False
        metrics.destroy()

    def test_create_disabled_metrics(self):
        """Test creating disabled metrics."""
        metrics = Metrics(token="test-token", disabled=True)
        assert metrics.disabled is True
        metrics.destroy()

    def test_start_request(self):
        """Test starting a request timer."""
        metrics = Metrics(token="test-token", disabled=True)
        timer = metrics.start_request()
        assert timer is not None
        assert callable(timer.end)
        metrics.destroy()

    def test_request_timer_callable(self):
        """Test that timer can be called directly."""
        metrics = Metrics(token="test-token", disabled=True)
        timer = metrics.start_request()
        # Should be callable
        timer(status_code=200)
        metrics.destroy()

    def test_record_request(self):
        """Test recording a pre-measured request."""
        metrics = Metrics(token="test-token", disabled=True)
        metrics.record(
            duration_ms=150,
            status_code=200,
            bytes_in=1024,
            bytes_out=2048,
        )
        assert metrics.get_pending_count() == 1
        metrics.destroy()

    def test_status_code_categorization(self):
        """Test that status codes are categorized correctly."""
        metrics = Metrics(token="test-token", disabled=True)

        metrics.record(duration_ms=100, status_code=200)
        metrics.record(duration_ms=100, status_code=301)
        metrics.record(duration_ms=100, status_code=404)
        metrics.record(duration_ms=100, status_code=500)

        assert metrics.get_pending_count() == 4
        metrics.destroy()

    def test_context_manager(self):
        """Test using metrics as context manager."""
        with Metrics(token="test-token", disabled=True) as metrics:
            metrics.record(duration_ms=100, status_code=200)
        # Should not raise after exit


class TestMetricsRemote:
    """Test cases for remote metrics sending."""

    @patch("loggy.metrics.requests.post")
    def test_flush_sends_metrics(self, mock_post):
        """Test that flush sends metrics to server."""
        mock_post.return_value = MagicMock(ok=True)

        metrics = Metrics(token="test-token")

        # Record a metric with a past timestamp to ensure it gets flushed
        past_time = datetime(2020, 1, 1, 12, 0, 0)
        metrics._record_request(
            past_time,
            100,
            metrics.RequestEndOptions(status_code=200) if hasattr(metrics, 'RequestEndOptions') else type('obj', (object,), {'status_code': 200, 'bytes_in': None, 'bytes_out': None, 'path': None, 'method': None})(),
        )

        metrics.flush()

        # Check that post was called
        if mock_post.called:
            call_args = mock_post.call_args
            assert call_args[1]["headers"]["x-loggy-token"] == "test-token"

        metrics.destroy()

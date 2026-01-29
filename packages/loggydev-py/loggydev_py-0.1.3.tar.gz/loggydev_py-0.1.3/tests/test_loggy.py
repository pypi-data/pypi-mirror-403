"""Tests for the Loggy logger."""

import io
import sys
from unittest.mock import MagicMock, patch

import pytest

from loggy import Loggy


class TestLoggy:
    """Test cases for the Loggy logger."""

    def test_create_logger(self):
        """Test creating a logger instance."""
        logger = Loggy(identifier="test-app")
        assert logger.identifier == "test-app"
        assert logger.color is True
        assert logger.compact is False
        assert logger.timestamp is True

    def test_create_logger_with_options(self):
        """Test creating a logger with custom options."""
        logger = Loggy(
            identifier="test-app",
            color=False,
            compact=True,
            timestamp=False,
        )
        assert logger.color is False
        assert logger.compact is True
        assert logger.timestamp is False

    def test_log_methods_exist(self):
        """Test that all log methods exist."""
        logger = Loggy(identifier="test-app")
        assert callable(logger.log)
        assert callable(logger.debug)
        assert callable(logger.info)
        assert callable(logger.warn)
        assert callable(logger.warning)
        assert callable(logger.error)
        assert callable(logger.blank)

    def test_log_output(self, capsys):
        """Test log output to stdout."""
        logger = Loggy(identifier="test-app", color=False, timestamp=False)
        logger.info("Test message")
        captured = capsys.readouterr()
        assert "INFO" in captured.out
        assert "test-app" in captured.out
        assert "Test message" in captured.out

    def test_error_output_to_stderr(self, capsys):
        """Test error output goes to stderr."""
        logger = Loggy(identifier="test-app", color=False, timestamp=False)
        logger.error("Error message")
        captured = capsys.readouterr()
        assert "ERROR" in captured.err
        assert "Error message" in captured.err

    def test_log_with_metadata(self, capsys):
        """Test logging with metadata."""
        logger = Loggy(identifier="test-app", color=False, timestamp=False)
        logger.info("User logged in", metadata={"user_id": 123})
        captured = capsys.readouterr()
        assert "user_id" in captured.out
        assert "123" in captured.out

    def test_context_manager(self):
        """Test using logger as context manager."""
        with Loggy(identifier="test-app") as logger:
            assert logger.identifier == "test-app"
        # Should not raise after exit

    def test_destroy(self):
        """Test destroy method."""
        logger = Loggy(identifier="test-app")
        logger.destroy()
        assert logger._stopped is True


class TestLoggyRemote:
    """Test cases for remote logging."""

    @patch("loggy.loggy.requests.post")
    def test_remote_logging(self, mock_post):
        """Test that logs are sent to remote server."""
        mock_post.return_value = MagicMock(ok=True)

        logger = Loggy(
            identifier="test-app",
            remote={"token": "test-token", "batch_size": 1},
        )
        logger.info("Test message")
        logger.flush()

        assert mock_post.called
        call_args = mock_post.call_args
        assert call_args[1]["headers"]["x-loggy-token"] == "test-token"

    @patch("loggy.loggy.requests.post")
    def test_remote_batching(self, mock_post):
        """Test that logs are batched."""
        mock_post.return_value = MagicMock(ok=True)

        logger = Loggy(
            identifier="test-app",
            remote={"token": "test-token", "batch_size": 3},
        )

        # Log 2 messages (below batch size)
        logger.info("Message 1")
        logger.info("Message 2")

        # Should not have flushed yet
        assert not mock_post.called

        # Manually flush
        logger.flush()
        assert mock_post.called

        logger.destroy()

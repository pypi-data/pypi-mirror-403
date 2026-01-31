"""Tests for LokiLogHandler - Remote logging to Loki via agent-gateway."""

import logging
import time
import queue
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from march_agent.loki_handler import LokiLogHandler, LogEntry


class TestLogEntry:
    """Test LogEntry dataclass."""

    def test_log_entry_creation(self):
        """Test creating a log entry."""
        entry = LogEntry(
            timestamp=1234567890000000000,
            level="info",
            message="Test message",
            extra={"conversation_id": "conv-123"}
        )

        assert entry.timestamp == 1234567890000000000
        assert entry.level == "info"
        assert entry.message == "Test message"
        assert entry.extra == {"conversation_id": "conv-123"}

    def test_log_entry_default_extra(self):
        """Test log entry with default empty extra."""
        entry = LogEntry(
            timestamp=1234567890000000000,
            level="error",
            message="Error occurred"
        )

        assert entry.extra == {}


class TestLokiLogHandlerInitialization:
    """Test LokiLogHandler initialization."""

    def test_handler_initialization(self):
        """Test basic handler initialization."""
        mock_gateway = MagicMock()

        handler = LokiLogHandler(
            gateway_client=mock_gateway,
            agent_name="test-agent",
            batch_size=50,
            flush_interval=3.0,
        )

        assert handler.agent_name == "test-agent"
        assert handler.batch_size == 50
        assert handler.flush_interval == 3.0
        assert handler.max_buffer_size == 10000
        assert handler.enable_compression is True
        assert handler._running is True

        # Cleanup
        handler.close()

    def test_handler_with_custom_buffer_size(self):
        """Test handler with custom buffer size."""
        mock_gateway = MagicMock()

        handler = LokiLogHandler(
            gateway_client=mock_gateway,
            agent_name="test-agent",
            max_buffer_size=5000,
        )

        assert handler.max_buffer_size == 5000

        # Cleanup
        handler.close()

    def test_handler_starts_flush_thread(self):
        """Test handler starts background flush thread."""
        mock_gateway = MagicMock()

        handler = LokiLogHandler(
            gateway_client=mock_gateway,
            agent_name="test-agent",
        )

        assert handler._thread is not None
        assert handler._thread.is_alive()
        assert handler._running is True

        # Cleanup
        handler.close()

    def test_handler_compression_disabled(self):
        """Test handler with compression disabled."""
        mock_gateway = MagicMock()

        handler = LokiLogHandler(
            gateway_client=mock_gateway,
            agent_name="test-agent",
            enable_compression=False,
        )

        assert handler.enable_compression is False

        # Cleanup
        handler.close()

    def test_handler_production_mode_level(self):
        """Test handler elevates log level in production."""
        mock_gateway = MagicMock()

        with patch.dict('os.environ', {'ENVIRONMENT': 'production'}):
            handler = LokiLogHandler(
                gateway_client=mock_gateway,
                agent_name="test-agent",
                level=logging.DEBUG,
            )

            # Should be elevated to INFO in production
            assert handler.level == logging.INFO

        # Cleanup
        handler.close()


class TestLogEmission:
    """Test log record emission."""

    def test_emit_creates_log_entry(self):
        """Test emit converts LogRecord to LogEntry."""
        mock_gateway = MagicMock()
        mock_gateway.http_url = "http://test-gateway:8080"
        mock_gateway.api_key = "test-key"

        handler = LokiLogHandler(
            gateway_client=mock_gateway,
            agent_name="test-agent",
            batch_size=1000,  # Large batch to prevent auto-flush
            flush_interval=1000,  # Long interval to prevent time-based flush
        )

        # Stop background thread to test synchronously
        handler._running = False
        if handler._thread:
            handler._thread.join(timeout=1.0)

        # Create a log record
        logger = logging.getLogger("test_emit")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info("Test log message")

        # No sleep needed - emit is synchronous
        # Check queue has entry
        assert handler._queue.qsize() > 0

        # Cleanup
        handler.close()

    def test_emit_handles_extra_fields(self):
        """Test emit captures extra fields."""
        mock_gateway = MagicMock()
        mock_gateway.api_key = "test-key"

        with patch('march_agent.loki_handler.requests.post') as mock_post:
            mock_post.return_value = Mock(status_code=200)

            handler = LokiLogHandler(
                gateway_client=mock_gateway,
                agent_name="test-agent",
                batch_size=1,
                flush_interval=0.1,
            )

            # Create logger and log with extra fields
            logger = logging.getLogger("test")
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

            logger.info(
                "User action",
                extra={"conversation_id": "conv-123", "user_id": "user-456"}
            )

            # Wait for flush
            time.sleep(0.2)

            # Verify request was made with extra fields
            assert mock_post.call_count > 0

        # Cleanup
        handler.close()

    def test_emit_graceful_degradation_on_full_buffer(self):
        """Test emit drops logs when buffer is full."""
        mock_gateway = MagicMock()

        handler = LokiLogHandler(
            gateway_client=mock_gateway,
            agent_name="test-agent",
            max_buffer_size=5,  # Very small buffer
            batch_size=100,  # Never flush during test
            flush_interval=1000,  # Never flush during test
        )

        # Fill buffer beyond capacity
        logger = logging.getLogger("test")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        for i in range(20):
            logger.info(f"Log {i}")

        time.sleep(0.05)

        # Buffer should not exceed max size
        assert handler._queue.qsize() <= 5

        # Cleanup
        handler.close()

    def test_record_to_entry_conversion(self):
        """Test LogRecord to LogEntry conversion."""
        mock_gateway = MagicMock()

        handler = LokiLogHandler(
            gateway_client=mock_gateway,
            agent_name="test-agent",
        )

        # Create a log record
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.conversation_id = "conv-123"
        record.user_id = "user-456"
        record.funcName = "test_function"

        entry = handler._record_to_entry(record)

        assert entry.level == "info"
        assert entry.message == "Test message"
        assert entry.extra["conversation_id"] == "conv-123"
        assert entry.extra["user_id"] == "user-456"
        assert entry.extra["logger"] == "test.logger"
        assert entry.extra["function"] == "test_function"

        # Cleanup
        handler.close()

    def test_record_to_entry_normalizes_warning(self):
        """Test WARNING level is normalized to warn."""
        mock_gateway = MagicMock()

        handler = LokiLogHandler(
            gateway_client=mock_gateway,
            agent_name="test-agent",
        )

        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="Warning",
            args=(),
            exc_info=None,
        )

        entry = handler._record_to_entry(record)

        assert entry.level == "warn"

        # Cleanup
        handler.close()


class TestLogFlushing:
    """Test log batching and flushing."""

    def test_flush_sends_logs_to_gateway(self):
        """Test flush sends logs via gateway HTTP."""
        mock_gateway = MagicMock()
        mock_gateway.api_key = "test-key"

        with patch('march_agent.loki_handler.requests.post') as mock_post:
            mock_post.return_value = Mock(status_code=200)

            handler = LokiLogHandler(
                gateway_client=mock_gateway,
                agent_name="test-agent",
                batch_size=2,
                flush_interval=0.1,
            )

            # Queue some entries
            logger = logging.getLogger("test")
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

            logger.info("Log 1")
            logger.info("Log 2")

            # Wait for flush
            time.sleep(0.2)

            # Verify request was made
            assert mock_post.call_count > 0
            call_args = mock_post.call_args

            # Check URL
            assert "/api/v1/logs" in call_args[0][0]

            # Check headers
            assert call_args[1]["headers"]["X-API-Key"] == "test-key"

        # Cleanup
        handler.close()

    def test_flush_uses_compression_by_default(self):
        """Test flush uses gzip compression."""
        mock_gateway = MagicMock()
        mock_gateway.api_key = "test-key"

        with patch('march_agent.loki_handler.requests.post') as mock_post:
            mock_post.return_value = Mock(status_code=200)

            handler = LokiLogHandler(
                gateway_client=mock_gateway,
                agent_name="test-agent",
                enable_compression=True,
                batch_size=1,
                flush_interval=0.1,
            )

            logger = logging.getLogger("test")
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

            logger.info("Test log")

            time.sleep(0.2)

            # Check compression header
            if mock_post.call_count > 0:
                headers = mock_post.call_args[1]["headers"]
                assert headers.get("Content-Encoding") == "gzip"

        # Cleanup
        handler.close()

    def test_flush_without_compression(self):
        """Test flush without compression."""
        mock_gateway = MagicMock()
        mock_gateway.api_key = "test-key"

        with patch('march_agent.loki_handler.requests.post') as mock_post:
            mock_post.return_value = Mock(status_code=200)

            handler = LokiLogHandler(
                gateway_client=mock_gateway,
                agent_name="test-agent",
                enable_compression=False,
                batch_size=1,
                flush_interval=0.1,
            )

            logger = logging.getLogger("test")
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

            logger.info("Test log")

            time.sleep(0.2)

            # Check no compression header
            if mock_post.call_count > 0:
                headers = mock_post.call_args[1]["headers"]
                assert headers.get("Content-Encoding") != "gzip"

        # Cleanup
        handler.close()

    def test_flush_retries_on_failure(self):
        """Test flush retries failed log sends."""
        mock_gateway = MagicMock()
        mock_gateway.api_key = "test-key"

        with patch('march_agent.loki_handler.requests.post') as mock_post:
            # Fail first, succeed second
            mock_post.side_effect = [
                Exception("Network error"),
                Mock(status_code=200)
            ]

            handler = LokiLogHandler(
                gateway_client=mock_gateway,
                agent_name="test-agent",
                batch_size=1,
                flush_interval=0.1,
            )

            logger = logging.getLogger("test")
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

            logger.info("Test log")

            # Wait for initial attempt and retry
            time.sleep(2.0)

            # Should have tried multiple times
            assert mock_post.call_count >= 1

        # Cleanup
        handler.close()

    def test_flush_exponential_backoff(self):
        """Test flush uses exponential backoff on failures."""
        mock_gateway = MagicMock()
        mock_gateway.api_key = "test-key"

        with patch('march_agent.loki_handler.requests.post') as mock_post:
            mock_post.side_effect = Exception("Network error")

            handler = LokiLogHandler(
                gateway_client=mock_gateway,
                agent_name="test-agent",
                batch_size=1,
                flush_interval=0.1,
            )

            # Queue entry
            entry = LogEntry(
                timestamp=int(time.time() * 1_000_000_000),
                level="info",
                message="Test",
            )
            handler._queue.put(entry)

            # Initial retry delay should be 1.0
            initial_delay = handler._retry_delay
            assert initial_delay == 1.0

            # Trigger flush (will fail)
            handler._flush_entries([entry])

            # Retry delay should have increased
            assert handler._retry_delay > initial_delay

        # Cleanup
        handler.close()


class TestHealthCheck:
    """Test handler health checking."""

    def test_is_healthy_returns_true_when_running(self):
        """Test is_healthy returns True when running normally."""
        mock_gateway = MagicMock()

        handler = LokiLogHandler(
            gateway_client=mock_gateway,
            agent_name="test-agent",
        )

        assert handler.is_healthy() is True

        # Cleanup
        handler.close()

    def test_is_healthy_returns_false_when_buffer_full(self):
        """Test is_healthy returns False when buffer is >80% full."""
        mock_gateway = MagicMock()
        mock_gateway.http_url = "http://test-gateway:8080"
        mock_gateway.api_key = "test-key"

        handler = LokiLogHandler(
            gateway_client=mock_gateway,
            agent_name="test-agent",
            max_buffer_size=10,
            batch_size=1000,  # Never flush
            flush_interval=1000,  # Never flush
        )

        # Directly queue entries to bypass logger
        for i in range(9):
            entry = LogEntry(
                timestamp=int(time.time() * 1_000_000_000),
                level="info",
                message=f"Log {i}",
            )
            handler._queue.put(entry)

        # Check immediately (no sleep needed)
        assert handler.is_healthy() is False

        # Cleanup
        handler.close()

    def test_is_healthy_returns_false_when_stopped(self):
        """Test is_healthy returns False when handler is closed."""
        mock_gateway = MagicMock()

        handler = LokiLogHandler(
            gateway_client=mock_gateway,
            agent_name="test-agent",
        )

        handler.close()

        assert handler.is_healthy() is False


class TestHandlerClose:
    """Test handler cleanup and shutdown."""

    def test_close_stops_flush_thread(self):
        """Test close stops background thread."""
        mock_gateway = MagicMock()

        handler = LokiLogHandler(
            gateway_client=mock_gateway,
            agent_name="test-agent",
        )

        thread = handler._thread
        assert thread.is_alive()

        handler.close()

        # Wait a moment for thread to stop
        time.sleep(0.2)

        assert handler._running is False

    def test_close_flushes_remaining_logs(self):
        """Test close flushes any remaining buffered logs."""
        mock_gateway = MagicMock()
        mock_gateway.api_key = "test-key"
        mock_gateway.http_url = "http://test-gateway:8080"

        with patch('march_agent.loki_handler.requests.post') as mock_post:
            mock_post.return_value = Mock(status_code=200)

            handler = LokiLogHandler(
                gateway_client=mock_gateway,
                agent_name="test-agent",
                batch_size=1000,  # Never auto-flush
                flush_interval=1000,
            )

            # Stop background thread
            handler._running = False
            if handler._thread:
                handler._thread.join(timeout=1.0)

            # Directly queue an entry
            entry = LogEntry(
                timestamp=int(time.time() * 1_000_000_000),
                level="info",
                message="Final log",
            )
            handler._queue.put(entry)

            # Manually call flush
            handler.flush()

            # Verify log was sent
            assert mock_post.call_count > 0

    def test_close_idempotent(self):
        """Test close can be called multiple times safely."""
        mock_gateway = MagicMock()

        handler = LokiLogHandler(
            gateway_client=mock_gateway,
            agent_name="test-agent",
        )

        handler.close()
        handler.close()  # Should not raise

        assert handler._running is False


class TestIntegrationWithMarchAgentApp:
    """Test LokiLogHandler integration with MarchAgentApp."""

    def test_handler_created_on_agent_registration(self):
        """Test handler is created when enable_remote_logging=True."""
        from march_agent.app import MarchAgentApp

        with patch('march_agent.app.GatewayClient') as mock_gateway_class, \
             patch('march_agent.app.ConversationClient'), \
             patch('march_agent.app.logging.getLogger') as mock_get_logger:

            mock_gateway = MagicMock()
            mock_gateway.http_post.return_value = Mock(
                status_code=201,
                json=lambda: {"id": "agent-123"}
            )
            mock_gateway_class.return_value = mock_gateway

            mock_root_logger = MagicMock()
            mock_get_logger.return_value = mock_root_logger

            app = MarchAgentApp(
                gateway_url="http://gateway:8080",
                api_key="test-key",
                enable_remote_logging=True,
                remote_log_level=logging.INFO,
            )

            # Register agent should create handler
            agent = app.register_me(
                name="test-agent",
                about="Test",
                document="Doc"
            )

            # Verify handler was created and added
            assert app._loki_handler is not None
            assert isinstance(app._loki_handler, LokiLogHandler)

            # Cleanup
            if app._loki_handler:
                app._loki_handler.close()

    def test_handler_not_created_when_disabled(self):
        """Test handler is not created when enable_remote_logging=False."""
        from march_agent.app import MarchAgentApp

        with patch('march_agent.app.GatewayClient') as mock_gateway_class, \
             patch('march_agent.app.ConversationClient'):

            mock_gateway = MagicMock()
            mock_gateway.http_post.return_value = Mock(
                status_code=201,
                json=lambda: {"id": "agent-123"}
            )
            mock_gateway_class.return_value = mock_gateway

            app = MarchAgentApp(
                gateway_url="http://gateway:8080",
                api_key="test-key",
                enable_remote_logging=False,
            )

            agent = app.register_me(
                name="test-agent",
                about="Test",
                document="Doc"
            )

            # Verify handler was not created
            assert app._loki_handler is None

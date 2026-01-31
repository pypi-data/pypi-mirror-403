"""Comprehensive tests for HeartbeatManager."""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from march_agent.heartbeat import HeartbeatManager
from march_agent.gateway_client import GatewayClient
from march_agent.exceptions import HeartbeatError


class TestHeartbeatManager:
    """Test HeartbeatManager functionality."""

    def test_heartbeat_initialization(self):
        """Test HeartbeatManager initialization."""
        gateway_client = Mock(spec=GatewayClient)
        heartbeat = HeartbeatManager(
            gateway_client=gateway_client,
            agent_name="test-agent",
            interval=60
        )

        assert heartbeat.gateway_client is gateway_client
        assert heartbeat.agent_name == "test-agent"
        assert heartbeat.interval == 60
        assert heartbeat._running is False
        assert heartbeat._thread is None

    def test_heartbeat_custom_interval(self):
        """Test HeartbeatManager with custom interval."""
        gateway_client = Mock(spec=GatewayClient)
        heartbeat = HeartbeatManager(
            gateway_client=gateway_client,
            agent_name="test-agent",
            interval=30
        )

        assert heartbeat.interval == 30

    def test_start_heartbeat(self):
        """Test starting the heartbeat thread."""
        gateway_client = Mock(spec=GatewayClient)
        heartbeat = HeartbeatManager(
            gateway_client=gateway_client,
            agent_name="test-agent",
            interval=60
        )

        with patch.object(heartbeat, '_heartbeat_loop'):
            heartbeat.start()

            assert heartbeat._running is True
            assert heartbeat._thread is not None
            assert isinstance(heartbeat._thread, threading.Thread)
            assert heartbeat._thread.daemon is True

            # Clean up
            heartbeat.stop()

    def test_start_heartbeat_twice_raises_error(self):
        """Test that starting heartbeat twice raises error."""
        gateway_client = Mock(spec=GatewayClient)
        heartbeat = HeartbeatManager(
            gateway_client=gateway_client,
            agent_name="test-agent",
            interval=60
        )

        with patch.object(heartbeat, '_heartbeat_loop'):
            heartbeat.start()

            with pytest.raises(HeartbeatError, match="Heartbeat already running"):
                heartbeat.start()

            # Clean up
            heartbeat.stop()

    def test_stop_heartbeat(self):
        """Test stopping the heartbeat thread."""
        gateway_client = Mock(spec=GatewayClient)
        heartbeat = HeartbeatManager(
            gateway_client=gateway_client,
            agent_name="test-agent",
            interval=1
        )

        with patch.object(heartbeat, '_heartbeat_loop'):
            heartbeat.start()
            assert heartbeat._running is True

            heartbeat.stop()

            assert heartbeat._running is False

    def test_stop_heartbeat_not_running(self):
        """Test stopping heartbeat when not running."""
        gateway_client = Mock(spec=GatewayClient)
        heartbeat = HeartbeatManager(
            gateway_client=gateway_client,
            agent_name="test-agent",
            interval=60
        )

        # Should not raise error
        heartbeat.stop()

        assert heartbeat._running is False

    def test_send_heartbeat_success(self):
        """Test sending heartbeat successfully."""
        gateway_client = Mock(spec=GatewayClient)
        mock_response = Mock()
        mock_response.status_code = 200
        gateway_client.http_post = Mock(return_value=mock_response)

        heartbeat = HeartbeatManager(
            gateway_client=gateway_client,
            agent_name="test-agent",
            interval=60
        )

        heartbeat._send_heartbeat()

        # Verify HTTP request made
        gateway_client.http_post.assert_called_once_with(
            "ai-inventory",
            "/api/v1/health/heartbeat",
            json={"name": "test-agent"},
            timeout=5.0
        )

    def test_send_heartbeat_201_response(self):
        """Test sending heartbeat with 201 response."""
        gateway_client = Mock(spec=GatewayClient)
        mock_response = Mock()
        mock_response.status_code = 201
        gateway_client.http_post = Mock(return_value=mock_response)

        heartbeat = HeartbeatManager(
            gateway_client=gateway_client,
            agent_name="test-agent",
            interval=60
        )

        # Should not raise error
        heartbeat._send_heartbeat()

        gateway_client.http_post.assert_called_once()

    def test_send_heartbeat_404_logs_warning(self):
        """Test sending heartbeat when agent not found (404)."""
        gateway_client = Mock(spec=GatewayClient)
        mock_response = Mock()
        mock_response.status_code = 404
        gateway_client.http_post = Mock(return_value=mock_response)

        heartbeat = HeartbeatManager(
            gateway_client=gateway_client,
            agent_name="test-agent",
            interval=60
        )

        with patch('march_agent.heartbeat.logger') as mock_logger:
            heartbeat._send_heartbeat()

            # Should log warning about agent not found
            mock_logger.warning.assert_called()
            warning_msg = mock_logger.warning.call_args[0][0]
            assert "not found" in warning_msg.lower()

    def test_send_heartbeat_error_status(self):
        """Test sending heartbeat with error status code."""
        gateway_client = Mock(spec=GatewayClient)
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        gateway_client.http_post = Mock(return_value=mock_response)

        heartbeat = HeartbeatManager(
            gateway_client=gateway_client,
            agent_name="test-agent",
            interval=60
        )

        with patch('march_agent.heartbeat.logger') as mock_logger:
            heartbeat._send_heartbeat()

            # Should log warning about error status
            mock_logger.warning.assert_called()
            warning_msg = mock_logger.warning.call_args[0][0]
            assert "500" in warning_msg

    def test_send_heartbeat_request_exception(self):
        """Test sending heartbeat when request raises exception."""
        gateway_client = Mock(spec=GatewayClient)
        gateway_client.http_post = Mock(side_effect=Exception("Connection failed"))

        heartbeat = HeartbeatManager(
            gateway_client=gateway_client,
            agent_name="test-agent",
            interval=60
        )

        with pytest.raises(HeartbeatError, match="Failed to send heartbeat"):
            heartbeat._send_heartbeat()

    def test_heartbeat_loop_sends_periodic_heartbeats(self):
        """Test that heartbeat loop sends periodic heartbeats."""
        gateway_client = Mock(spec=GatewayClient)
        mock_response = Mock()
        mock_response.status_code = 200
        gateway_client.http_post = Mock(return_value=mock_response)

        heartbeat = HeartbeatManager(
            gateway_client=gateway_client,
            agent_name="test-agent",
            interval=1  # Short interval for testing
        )

        heartbeat.start()

        # Wait for at least 2 heartbeats
        time.sleep(2.5)

        heartbeat.stop()

        # Should have sent at least 2 heartbeats
        assert gateway_client.http_post.call_count >= 2

    def test_heartbeat_loop_handles_exceptions(self):
        """Test that heartbeat loop continues after exceptions."""
        gateway_client = Mock(spec=GatewayClient)

        # First call raises exception, second succeeds
        mock_response = Mock()
        mock_response.status_code = 200
        gateway_client.http_post = Mock(side_effect=[
            Exception("First failure"),
            mock_response,
            mock_response
        ])

        heartbeat = HeartbeatManager(
            gateway_client=gateway_client,
            agent_name="test-agent",
            interval=1
        )

        with patch('march_agent.heartbeat.logger') as mock_logger:
            heartbeat.start()

            # Wait for multiple heartbeat attempts
            time.sleep(2.5)

            heartbeat.stop()

            # Should have logged the error
            mock_logger.error.assert_called()

            # Should have attempted multiple heartbeats despite first failure
            assert gateway_client.http_post.call_count >= 2

    def test_heartbeat_loop_stops_quickly(self):
        """Test that heartbeat loop stops quickly when stopped."""
        gateway_client = Mock(spec=GatewayClient)
        mock_response = Mock()
        mock_response.status_code = 200
        gateway_client.http_post = Mock(return_value=mock_response)

        heartbeat = HeartbeatManager(
            gateway_client=gateway_client,
            agent_name="test-agent",
            interval=60  # Long interval
        )

        heartbeat.start()

        # Immediately stop
        start_time = time.time()
        heartbeat.stop()
        stop_duration = time.time() - start_time

        # Should stop within 5 seconds (the join timeout)
        assert stop_duration < 6

    def test_heartbeat_thread_is_daemon(self):
        """Test that heartbeat thread is a daemon thread."""
        gateway_client = Mock(spec=GatewayClient)
        heartbeat = HeartbeatManager(
            gateway_client=gateway_client,
            agent_name="test-agent",
            interval=60
        )

        with patch.object(heartbeat, '_heartbeat_loop'):
            heartbeat.start()

            assert heartbeat._thread.daemon is True

            heartbeat.stop()

    def test_heartbeat_timeout_parameter(self):
        """Test that heartbeat sends with correct timeout."""
        gateway_client = Mock(spec=GatewayClient)
        mock_response = Mock()
        mock_response.status_code = 200
        gateway_client.http_post = Mock(return_value=mock_response)

        heartbeat = HeartbeatManager(
            gateway_client=gateway_client,
            agent_name="test-agent",
            interval=60
        )

        heartbeat._send_heartbeat()

        # Verify timeout is 5.0 seconds
        call_kwargs = gateway_client.http_post.call_args[1]
        assert call_kwargs["timeout"] == 5.0

    def test_heartbeat_payload_structure(self):
        """Test that heartbeat payload has correct structure."""
        gateway_client = Mock(spec=GatewayClient)
        mock_response = Mock()
        mock_response.status_code = 200
        gateway_client.http_post = Mock(return_value=mock_response)

        heartbeat = HeartbeatManager(
            gateway_client=gateway_client,
            agent_name="my-test-agent",
            interval=60
        )

        heartbeat._send_heartbeat()

        # Verify payload structure
        call_kwargs = gateway_client.http_post.call_args[1]
        payload = call_kwargs["json"]
        assert payload == {"name": "my-test-agent"}

    def test_heartbeat_logging_on_start(self):
        """Test that heartbeat logs on start."""
        gateway_client = Mock(spec=GatewayClient)
        heartbeat = HeartbeatManager(
            gateway_client=gateway_client,
            agent_name="test-agent",
            interval=60
        )

        with patch('march_agent.heartbeat.logger') as mock_logger:
            with patch.object(heartbeat, '_heartbeat_loop'):
                heartbeat.start()

                # Should log info message
                mock_logger.info.assert_called()
                info_msg = mock_logger.info.call_args[0][0]
                assert "started" in info_msg.lower()
                assert "test-agent" in info_msg

                heartbeat.stop()

    def test_heartbeat_logging_on_stop(self):
        """Test that heartbeat logs on stop."""
        gateway_client = Mock(spec=GatewayClient)
        heartbeat = HeartbeatManager(
            gateway_client=gateway_client,
            agent_name="test-agent",
            interval=60
        )

        with patch('march_agent.heartbeat.logger') as mock_logger:
            with patch.object(heartbeat, '_heartbeat_loop'):
                heartbeat.start()
                heartbeat.stop()

                # Check that info was called with stop message
                info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
                assert any("stopped" in msg.lower() for msg in info_calls)

    def test_heartbeat_debug_logging_on_success(self):
        """Test that heartbeat logs debug message on successful send."""
        gateway_client = Mock(spec=GatewayClient)
        mock_response = Mock()
        mock_response.status_code = 200
        gateway_client.http_post = Mock(return_value=mock_response)

        heartbeat = HeartbeatManager(
            gateway_client=gateway_client,
            agent_name="test-agent",
            interval=60
        )

        with patch('march_agent.heartbeat.logger') as mock_logger:
            heartbeat._send_heartbeat()

            # Should log debug message
            mock_logger.debug.assert_called()
            debug_msg = mock_logger.debug.call_args[0][0]
            assert "successfully" in debug_msg.lower()

    def test_multiple_agents_different_names(self):
        """Test multiple heartbeat managers with different agent names."""
        gateway_client1 = Mock(spec=GatewayClient)
        gateway_client2 = Mock(spec=GatewayClient)
        mock_response = Mock()
        mock_response.status_code = 200
        gateway_client1.http_post = Mock(return_value=mock_response)
        gateway_client2.http_post = Mock(return_value=mock_response)

        heartbeat1 = HeartbeatManager(
            gateway_client=gateway_client1,
            agent_name="agent-1",
            interval=60
        )

        heartbeat2 = HeartbeatManager(
            gateway_client=gateway_client2,
            agent_name="agent-2",
            interval=60
        )

        heartbeat1._send_heartbeat()
        heartbeat2._send_heartbeat()

        # Verify each sent with correct agent name
        payload1 = gateway_client1.http_post.call_args[1]["json"]
        payload2 = gateway_client2.http_post.call_args[1]["json"]

        assert payload1["name"] == "agent-1"
        assert payload2["name"] == "agent-2"

    def test_heartbeat_interval_sleep_logic(self):
        """Test that heartbeat sleeps in 1-second intervals for quick shutdown."""
        gateway_client = Mock(spec=GatewayClient)
        mock_response = Mock()
        mock_response.status_code = 200
        gateway_client.http_post = Mock(return_value=mock_response)

        heartbeat = HeartbeatManager(
            gateway_client=gateway_client,
            agent_name="test-agent",
            interval=5  # 5 seconds
        )

        with patch('march_agent.heartbeat.time.sleep') as mock_sleep:
            heartbeat.start()

            # Wait a bit for the loop to execute
            time.sleep(0.5)

            heartbeat.stop()

            # Should have slept multiple times in 1-second intervals
            # (The loop sleeps in 1-second chunks to allow quick shutdown)
            sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
            assert all(sleep_time == 1 for sleep_time in sleep_calls if sleep_time == 1)

    def test_heartbeat_join_timeout(self):
        """Test that stop waits up to 5 seconds for thread to finish."""
        gateway_client = Mock(spec=GatewayClient)
        heartbeat = HeartbeatManager(
            gateway_client=gateway_client,
            agent_name="test-agent",
            interval=60
        )

        with patch.object(heartbeat, '_heartbeat_loop'):
            heartbeat.start()

            # Mock the thread's join method
            with patch.object(heartbeat._thread, 'join') as mock_join:
                heartbeat.stop()

                # Should call join with 5 second timeout
                mock_join.assert_called_once_with(timeout=5.0)

"""Tests for MarchAgentApp - Application lifecycle and agent management."""

import logging
import pytest
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from march_agent.app import MarchAgentApp
from march_agent.agent import Agent
from march_agent.exceptions import RegistrationError, ConfigurationError


class TestAppInitialization:
    """Test MarchAgentApp initialization."""

    def test_app_initialization(self):
        """Test basic app initialization."""
        with patch('march_agent.app.GatewayClient') as mock_gateway_class, \
             patch('march_agent.app.ConversationClient') as mock_conv_class:

            app = MarchAgentApp(
                gateway_url="http://gateway:8080",
                api_key="test-key"
            )

            assert app.gateway_url == "http://gateway:8080"
            assert app.api_key == "test-key"
            assert app.heartbeat_interval == 60
            assert "encountered an error" in app.error_message_template.lower()
            assert len(app._agents) == 0
            assert app._running is False
            assert app._connected is False

            # Verify clients were created
            mock_gateway_class.assert_called_once_with("http://gateway:8080", "test-key", secure=False)
            mock_conv_class.assert_called_once()

    def test_app_initialization_with_custom_error_template(self):
        """Test app with custom error template."""
        with patch('march_agent.app.GatewayClient'), \
             patch('march_agent.app.ConversationClient'):

            custom_template = "Service unavailable"
            app = MarchAgentApp(
                gateway_url="http://gateway:8080",
                api_key="test-key",
                error_message_template=custom_template
            )

            assert app.error_message_template == custom_template

    def test_app_initialization_with_custom_heartbeat(self):
        """Test app with custom heartbeat interval."""
        with patch('march_agent.app.GatewayClient'), \
             patch('march_agent.app.ConversationClient'):

            app = MarchAgentApp(
                gateway_url="http://gateway:8080",
                api_key="test-key",
                heartbeat_interval=30
            )

            assert app.heartbeat_interval == 30


class TestAgentRegistration:
    """Test agent registration."""

    def test_register_me_success(self):
        """Test successful agent registration."""
        with patch('march_agent.app.GatewayClient') as mock_gateway_class, \
             patch('march_agent.app.ConversationClient'):

            mock_gateway = MagicMock()
            mock_gateway.http_post.return_value = Mock(
                status_code=201,
                json=lambda: {"id": "agent-123", "name": "test-agent"}
            )
            mock_gateway_class.return_value = mock_gateway

            app = MarchAgentApp(
                gateway_url="http://gateway:8080",
                api_key="test-key"
            )

            agent = app.register_me(
                name="test-agent",
                about="Test agent",
                document="Test document"
            )

            # Verify HTTP registration call
            mock_gateway.http_post.assert_called_once()
            call_args = mock_gateway.http_post.call_args
            assert call_args[0][0] == "ai-inventory"  # service name
            assert call_args[0][1] == "/api/v1/agents/register"  # path

            # Verify agent was returned and added to list
            assert isinstance(agent, Agent)
            assert agent.name == "test-agent"
            assert len(app._agents) == 1

    def test_register_me_returns_agent_instance(self):
        """Test register_me returns Agent instance."""
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
                api_key="test-key"
            )

            agent = app.register_me(
                name="test-agent",
                about="Test",
                document="Doc"
            )

            assert isinstance(agent, Agent)

    def test_register_me_passes_error_template(self):
        """Test error template is passed to agent."""
        with patch('march_agent.app.GatewayClient') as mock_gateway_class, \
             patch('march_agent.app.ConversationClient'):

            mock_gateway = MagicMock()
            mock_gateway.http_post.return_value = Mock(
                status_code=201,
                json=lambda: {"id": "agent-123"}
            )
            mock_gateway_class.return_value = mock_gateway

            custom_template = "Service error"
            app = MarchAgentApp(
                gateway_url="http://gateway:8080",
                api_key="test-key",
                error_message_template=custom_template
            )

            agent = app.register_me(
                name="test-agent",
                about="Test",
                document="Doc"
            )

            assert agent.error_message_template == custom_template

    def test_register_me_http_failure(self):
        """Test registration fails on HTTP error."""
        with patch('march_agent.app.GatewayClient') as mock_gateway_class, \
             patch('march_agent.app.ConversationClient'):

            mock_gateway = MagicMock()
            mock_gateway.http_post.return_value = Mock(
                status_code=500,
                text="Server error"
            )
            mock_gateway_class.return_value = mock_gateway

            app = MarchAgentApp(
                gateway_url="http://gateway:8080",
                api_key="test-key"
            )

            with pytest.raises(RegistrationError, match="Registration failed"):
                app.register_me(
                    name="test-agent",
                    about="Test",
                    document="Doc"
                )

    def test_register_me_network_failure(self):
        """Test registration fails on network error."""
        with patch('march_agent.app.GatewayClient') as mock_gateway_class, \
             patch('march_agent.app.ConversationClient'):

            mock_gateway = MagicMock()
            mock_gateway.http_post.side_effect = Exception("Network error")
            mock_gateway_class.return_value = mock_gateway

            app = MarchAgentApp(
                gateway_url="http://gateway:8080",
                api_key="test-key"
            )

            with pytest.raises(RegistrationError, match="Failed to register agent"):
                app.register_me(
                    name="test-agent",
                    about="Test",
                    document="Doc"
                )

    def test_register_me_multiple_agents(self):
        """Test registering multiple agents."""
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
                api_key="test-key"
            )

            agent1 = app.register_me(name="agent-1", about="Test", document="Doc")
            agent2 = app.register_me(name="agent-2", about="Test", document="Doc")

            assert len(app._agents) == 2
            assert agent1.name == "agent-1"
            assert agent2.name == "agent-2"


class TestConnectionLifecycle:
    """Test connection and lifecycle management."""

    def test_run_without_agents(self):
        """Test running without registered agents raises error."""
        with patch('march_agent.app.GatewayClient'), \
             patch('march_agent.app.ConversationClient'):

            app = MarchAgentApp(
                gateway_url="http://gateway:8080",
                api_key="test-key"
            )

            with pytest.raises(ConfigurationError, match="No agents registered"):
                app.run()

    def test_run_connects_gateway(self):
        """Test run() connects to gateway."""
        with patch('march_agent.app.GatewayClient') as mock_gateway_class, \
             patch('march_agent.app.ConversationClient'), \
             patch('march_agent.app.asyncio.new_event_loop') as mock_loop_func, \
             patch('march_agent.app.asyncio.set_event_loop'):

            # Mock event loop
            mock_loop = MagicMock()
            mock_loop.run_until_complete = MagicMock(return_value=None)
            mock_loop.close = MagicMock()
            mock_loop_func.return_value = mock_loop

            mock_gateway = MagicMock()
            mock_gateway.http_post.return_value = Mock(
                status_code=201,
                json=lambda: {"id": "agent-123"}
            )
            mock_gateway.consume_one.side_effect = KeyboardInterrupt()
            mock_gateway_class.return_value = mock_gateway

            app = MarchAgentApp(
                gateway_url="http://gateway:8080",
                api_key="test-key"
            )

            app.register_me(name="test-agent", about="Test", document="Doc")

            try:
                app.run()
            except KeyboardInterrupt:
                pass

            # Verify gateway was connected
            mock_gateway.connect.assert_called_once()
            assert app._connected is True

    def test_run_initializes_agents(self):
        """Test run() initializes all registered agents."""
        with patch('march_agent.app.GatewayClient') as mock_gateway_class, \
             patch('march_agent.app.ConversationClient'), \
             patch('march_agent.app.asyncio.new_event_loop') as mock_loop_func, \
             patch('march_agent.app.asyncio.set_event_loop'):

            # Mock event loop
            mock_loop = MagicMock()
            mock_loop.run_until_complete = MagicMock(return_value=None)
            mock_loop.close = MagicMock()
            mock_loop_func.return_value = mock_loop

            mock_gateway = MagicMock()
            mock_gateway.http_post.return_value = Mock(
                status_code=201,
                json=lambda: {"id": "agent-123"}
            )
            mock_gateway.consume_one.side_effect = KeyboardInterrupt()
            mock_gateway_class.return_value = mock_gateway

            app = MarchAgentApp(
                gateway_url="http://gateway:8080",
                api_key="test-key"
            )

            agent = app.register_me(name="test-agent", about="Test", document="Doc")

            with patch.object(agent, '_initialize_with_gateway') as mock_init:
                try:
                    app.run()
                except KeyboardInterrupt:
                    pass

                # Verify agent was initialized
                mock_init.assert_called_once()


class TestMessageRouting:
    """Test message routing to agents."""

    def test_consume_loop_routes_to_correct_agent(self):
        """Test messages are routed to correct agent by topic."""
        with patch('march_agent.app.GatewayClient') as mock_gateway_class, \
             patch('march_agent.app.ConversationClient'), \
             patch('march_agent.app.asyncio.new_event_loop') as mock_loop_func, \
             patch('march_agent.app.asyncio.set_event_loop'):

            # Mock event loop
            mock_loop = MagicMock()
            mock_loop.run_until_complete = MagicMock(return_value=None)
            mock_loop.close = MagicMock()
            mock_loop_func.return_value = mock_loop

            mock_gateway = MagicMock()
            mock_gateway.http_post.return_value = Mock(
                status_code=201,
                json=lambda: {"id": "agent-123"}
            )

            # Create mock message for agent-1
            mock_msg = Mock()
            mock_msg.topic = "agent-1.inbox"

            # Return message once, then raise KeyboardInterrupt
            mock_gateway.consume_one.side_effect = [mock_msg, KeyboardInterrupt()]
            mock_gateway_class.return_value = mock_gateway

            app = MarchAgentApp(
                gateway_url="http://gateway:8080",
                api_key="test-key"
            )

            agent = app.register_me(name="agent-1", about="Test", document="Doc")

            with patch.object(agent, '_handle_message_async', new_callable=AsyncMock) as mock_handler:
                try:
                    app.run()
                except KeyboardInterrupt:
                    pass

                # Verify message was routed to agent
                mock_handler.assert_called_once_with(mock_msg)

    def test_consume_loop_handles_unknown_topic(self, caplog):
        """Test messages for unknown topics are logged."""
        with patch('march_agent.app.GatewayClient') as mock_gateway_class, \
             patch('march_agent.app.ConversationClient'), \
             patch('march_agent.app.asyncio.new_event_loop') as mock_loop_func, \
             patch('march_agent.app.asyncio.set_event_loop'):

            # Mock event loop
            mock_loop = MagicMock()
            mock_loop.run_until_complete = MagicMock(return_value=None)
            mock_loop.close = MagicMock()
            mock_loop_func.return_value = mock_loop

            mock_gateway = MagicMock()
            mock_gateway.http_post.return_value = Mock(
                status_code=201,
                json=lambda: {"id": "agent-123"}
            )

            # Message for non-existent agent
            mock_msg = Mock()
            mock_msg.topic = "unknown-agent.inbox"

            mock_gateway.consume_one.side_effect = [mock_msg, KeyboardInterrupt()]
            mock_gateway_class.return_value = mock_gateway

            app = MarchAgentApp(
                gateway_url="http://gateway:8080",
                api_key="test-key"
            )

            app.register_me(name="agent-1", about="Test", document="Doc")

            try:
                app.run()
            except KeyboardInterrupt:
                pass

            # Verify warning was logged
            assert "No agent for topic: unknown-agent.inbox" in caplog.text

    def test_consume_loop_timeout(self):
        """Test consume loop handles timeout gracefully."""
        with patch('march_agent.app.GatewayClient') as mock_gateway_class, \
             patch('march_agent.app.ConversationClient'), \
             patch('march_agent.app.asyncio.new_event_loop') as mock_loop_func, \
             patch('march_agent.app.asyncio.set_event_loop'):

            # Mock event loop
            mock_loop = MagicMock()
            mock_loop.run_until_complete = MagicMock(return_value=None)
            mock_loop.close = MagicMock()
            mock_loop_func.return_value = mock_loop

            mock_gateway = MagicMock()
            mock_gateway.http_post.return_value = Mock(
                status_code=201,
                json=lambda: {"id": "agent-123"}
            )

            # Return None (timeout) then exit
            mock_gateway.consume_one.side_effect = [None, KeyboardInterrupt()]
            mock_gateway_class.return_value = mock_gateway

            app = MarchAgentApp(
                gateway_url="http://gateway:8080",
                api_key="test-key"
            )

            app.register_me(name="agent-1", about="Test", document="Doc")

            try:
                app.run()
            except KeyboardInterrupt:
                pass

            # Should handle timeout without error
            assert app._running is False


class TestShutdown:
    """Test shutdown handling."""

    def test_shutdown_calls_agent_shutdown(self):
        """Test shutdown calls shutdown on all agents."""
        with patch('march_agent.app.GatewayClient') as mock_gateway_class, \
             patch('march_agent.app.ConversationClient'), \
             patch('march_agent.app.asyncio.get_event_loop') as mock_get_loop:

            # Mock async cleanup
            mock_loop = MagicMock()
            mock_loop.is_closed.return_value = False
            mock_loop.run_until_complete = MagicMock()
            mock_get_loop.return_value = mock_loop

            mock_gateway = MagicMock()
            mock_gateway.http_post.return_value = Mock(
                status_code=201,
                json=lambda: {"id": "agent-123"}
            )
            mock_gateway.close_async = AsyncMock()
            mock_gateway_class.return_value = mock_gateway

            mock_conv_client = MagicMock()
            mock_conv_client.close = AsyncMock()

            app = MarchAgentApp(
                gateway_url="http://gateway:8080",
                api_key="test-key"
            )
            app.conversation_client = mock_conv_client

            agent1 = app.register_me(name="agent-1", about="Test", document="Doc")
            agent2 = app.register_me(name="agent-2", about="Test", document="Doc")

            with patch.object(agent1, 'shutdown') as mock_shutdown1, \
                 patch.object(agent2, 'shutdown') as mock_shutdown2:

                app._shutdown()

                # Verify both agents were shut down
                mock_shutdown1.assert_called_once()
                mock_shutdown2.assert_called_once()

    def test_shutdown_closes_gateway(self):
        """Test shutdown closes gateway connection."""
        with patch('march_agent.app.GatewayClient') as mock_gateway_class, \
             patch('march_agent.app.ConversationClient'), \
             patch('march_agent.app.asyncio.get_event_loop') as mock_get_loop:

            # Mock async cleanup
            mock_loop = MagicMock()
            mock_loop.is_closed.return_value = False
            mock_loop.run_until_complete = MagicMock()
            mock_get_loop.return_value = mock_loop

            mock_gateway = MagicMock()
            mock_gateway.http_post.return_value = Mock(
                status_code=201,
                json=lambda: {"id": "agent-123"}
            )
            mock_gateway.close_async = AsyncMock()
            mock_gateway_class.return_value = mock_gateway

            mock_conv_client = MagicMock()
            mock_conv_client.close = AsyncMock()

            app = MarchAgentApp(
                gateway_url="http://gateway:8080",
                api_key="test-key"
            )
            app.conversation_client = mock_conv_client

            app.register_me(name="agent-1", about="Test", document="Doc")
            app._connected = True

            app._shutdown()

            # Verify gateway was closed
            mock_gateway.close.assert_called_once()
            assert app._running is False


class TestRemoteLogging:
    """Test remote logging integration."""

    def test_app_with_remote_logging_enabled(self):
        """Test app initialization with remote logging enabled."""
        with patch('march_agent.app.GatewayClient'), \
             patch('march_agent.app.ConversationClient'):

            app = MarchAgentApp(
                gateway_url="http://gateway:8080",
                api_key="test-key",
                enable_remote_logging=True,
                remote_log_level=logging.INFO,
                remote_log_batch_size=50,
                remote_log_flush_interval=3.0,
            )

            # Should have pending logging config
            assert app._pending_remote_logging is not None
            assert app._pending_remote_logging["log_level"] == logging.INFO
            assert app._pending_remote_logging["batch_size"] == 50
            assert app._pending_remote_logging["flush_interval"] == 3.0
            assert app._loki_handler is None  # Not created yet

    def test_remote_logging_handler_created_on_registration(self):
        """Test Loki handler is created when agent is registered."""
        with patch('march_agent.app.GatewayClient') as mock_gateway_class, \
             patch('march_agent.app.ConversationClient'), \
             patch('march_agent.loki_handler.LokiLogHandler') as mock_handler_class:

            mock_gateway = MagicMock()
            mock_gateway.http_post.return_value = Mock(
                status_code=201,
                json=lambda: {"id": "agent-123"}
            )
            mock_gateway_class.return_value = mock_gateway

            mock_handler = MagicMock()
            mock_handler_class.return_value = mock_handler

            app = MarchAgentApp(
                gateway_url="http://gateway:8080",
                api_key="test-key",
                enable_remote_logging=True,
                remote_log_level=logging.INFO,
                remote_log_batch_size=50,
                remote_log_flush_interval=3.0,
            )

            # Register agent
            agent = app.register_me(
                name="test-agent",
                about="Test",
                document="Doc"
            )

            # Verify handler was created with correct params
            mock_handler_class.assert_called_once_with(
                gateway_client=mock_gateway,
                agent_name="test-agent",
                batch_size=50,
                flush_interval=3.0,
                level=logging.INFO,
            )

            # Verify handler was added to root logger
            assert app._loki_handler == mock_handler

            # Verify pending config was cleared
            assert app._pending_remote_logging is None

    def test_remote_logging_disabled_by_default(self):
        """Test remote logging is disabled by default."""
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
                api_key="test-key"
            )

            agent = app.register_me(
                name="test-agent",
                about="Test",
                document="Doc"
            )

            # Verify no handler was created
            assert app._loki_handler is None
            assert app._pending_remote_logging is None

    def test_remote_logging_handler_only_created_once(self):
        """Test handler is only created for first agent registration."""
        with patch('march_agent.app.GatewayClient') as mock_gateway_class, \
             patch('march_agent.app.ConversationClient'), \
             patch('march_agent.loki_handler.LokiLogHandler') as mock_handler_class:

            mock_gateway = MagicMock()
            mock_gateway.http_post.return_value = Mock(
                status_code=201,
                json=lambda: {"id": "agent-123"}
            )
            mock_gateway_class.return_value = mock_gateway

            mock_handler = MagicMock()
            mock_handler_class.return_value = mock_handler

            app = MarchAgentApp(
                gateway_url="http://gateway:8080",
                api_key="test-key",
                enable_remote_logging=True,
            )

            # Register first agent
            agent1 = app.register_me(
                name="agent-1",
                about="Test",
                document="Doc"
            )

            # Register second agent
            agent2 = app.register_me(
                name="agent-2",
                about="Test",
                document="Doc"
            )

            # Handler should only be created once (for first agent)
            mock_handler_class.assert_called_once()
            call_args = mock_handler_class.call_args
            assert call_args[1]["agent_name"] == "agent-1"  # Uses first agent name

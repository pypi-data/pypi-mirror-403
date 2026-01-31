"""Tests for Agent class - Core functionality and fault tolerance."""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch, call
from march_agent.agent import Agent, SenderFilter
from march_agent.message import Message
from march_agent.gateway_client import KafkaMessage
from march_agent.exceptions import ConfigurationError


class TestAgentInitialization:
    """Test Agent initialization."""

    def test_agent_initialization(self, mock_gateway_client, sample_agent_data):
        """Test basic agent initialization."""
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
        )

        assert agent.name == "test-agent"
        assert agent.gateway_client == mock_gateway_client
        assert agent.agent_data == sample_agent_data
        assert agent.heartbeat_interval == 60
        assert agent.conversation_client is None
        assert agent.send_error_responses is True
        assert agent._running is False
        assert agent._initialized is False

    def test_agent_initialization_with_custom_error_template(
        self, mock_gateway_client, sample_agent_data
    ):
        """Test agent with custom error template."""
        custom_template = "Custom error message"
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
            error_message_template=custom_template,
        )

        assert agent.error_message_template == custom_template

    def test_agent_initialization_default_error_template(
        self, mock_gateway_client, sample_agent_data
    ):
        """Test agent has default error template."""
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
        )

        assert "encountered an error" in agent.error_message_template.lower()


class TestHandlerRegistration:
    """Test handler registration and sender filtering."""

    def test_on_message_decorator_no_filter(self, mock_gateway_client, sample_agent_data):
        """Test registering a catch-all handler."""
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
        )

        @agent.on_message
        def handler(message: Message, sender: str):
            pass

        assert len(agent._message_handlers) == 1
        sender_filter, registered_handler = agent._message_handlers[0]
        assert registered_handler == handler
        assert sender_filter.match_all is True

    def test_on_message_decorator_with_include_filter(
        self, mock_gateway_client, sample_agent_data
    ):
        """Test registering handler with sender whitelist."""
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
        )

        @agent.on_message(senders=["user", "agent-1"])
        def handler(message: Message, sender: str):
            pass

        sender_filter, _ = agent._message_handlers[0]
        assert "user" in sender_filter.include
        assert "agent-1" in sender_filter.include
        assert sender_filter.match_all is False

    def test_on_message_decorator_with_exclude_filter(
        self, mock_gateway_client, sample_agent_data
    ):
        """Test registering handler with sender blacklist."""
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
        )

        @agent.on_message(senders=["~bot"])
        def handler(message: Message, sender: str):
            pass

        sender_filter, _ = agent._message_handlers[0]
        assert "bot" in sender_filter.exclude

    def test_on_message_decorator_multiple_handlers(
        self, mock_gateway_client, sample_agent_data
    ):
        """Test registering multiple handlers - first match wins."""
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
        )

        @agent.on_message(senders=["user"])
        def handler1(message: Message, sender: str):
            pass

        @agent.on_message(senders=["agent-1"])
        def handler2(message: Message, sender: str):
            pass

        assert len(agent._message_handlers) == 2


class TestSenderFilter:
    """Test SenderFilter matching logic."""

    def test_sender_filter_match_all(self):
        """Test filter with no restrictions matches everything."""
        filter = SenderFilter(senders=None)
        assert filter.matches("user")
        assert filter.matches("agent-1")
        assert filter.matches("anyone")

    def test_sender_filter_include(self):
        """Test filter with include list."""
        filter = SenderFilter(senders=["user", "agent-1"])
        assert filter.matches("user")
        assert filter.matches("agent-1")
        assert not filter.matches("agent-2")

    def test_sender_filter_exclude(self):
        """Test filter with exclude list (~ prefix)."""
        filter = SenderFilter(senders=["~bot"])
        assert filter.matches("user")
        assert filter.matches("agent-1")
        assert not filter.matches("bot")

    def test_sender_filter_mixed(self):
        """Test filter with both include and exclude."""
        filter = SenderFilter(senders=["user", "agent-1", "~bot"])
        assert filter.matches("user")
        assert filter.matches("agent-1")
        assert not filter.matches("bot")
        assert not filter.matches("agent-2")

    def test_find_matching_handler_found(self, mock_gateway_client, sample_agent_data):
        """Test finding a matching handler."""
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
        )

        @agent.on_message(senders=["user"])
        def handler(message: Message, sender: str):
            pass

        found_handler = agent._find_matching_handler("user")
        assert found_handler == handler

    def test_find_matching_handler_not_found(
        self, mock_gateway_client, sample_agent_data
    ):
        """Test when no handler matches."""
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
        )

        @agent.on_message(senders=["user"])
        def handler(message: Message, sender: str):
            pass

        found_handler = agent._find_matching_handler("agent-1")
        assert found_handler is None


class TestMessageProcessing:
    """Test message processing and handler execution."""

    @pytest.mark.asyncio
    async def test_on_kafka_message_async_handler_success(
        self, mock_gateway_client, sample_agent_data, sample_kafka_message
    ):
        """Test successful async message processing."""
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
        )

        handler_called = False
        received_content = None

        @agent.on_message
        async def handler(message: Message, sender: str):
            nonlocal handler_called, received_content
            handler_called = True
            received_content = message.content

        agent._on_kafka_message(sample_kafka_message)
        await asyncio.sleep(0.1)  # Let async task complete

        assert handler_called
        assert received_content == "Test message content"

    @pytest.mark.asyncio
    async def test_on_kafka_message_sync_handler_success(
        self, mock_gateway_client, sample_agent_data, sample_kafka_message
    ):
        """Test successful sync message processing (backward compatibility)."""
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
        )

        handler_called = False
        received_content = None

        @agent.on_message
        def handler(message: Message, sender: str):
            nonlocal handler_called, received_content
            handler_called = True
            received_content = message.content

        agent._on_kafka_message(sample_kafka_message)
        await asyncio.sleep(0.1)  # Let task complete

        assert handler_called
        assert received_content == "Test message content"

    @pytest.mark.asyncio
    async def test_on_kafka_message_no_handler_matched(
        self, mock_gateway_client, sample_agent_data, sample_kafka_message, caplog
    ):
        """Test message with no matching handler logs warning."""
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
        )

        @agent.on_message(senders=["agent-1"])
        async def handler(message: Message, sender: str):
            pass

        agent._on_kafka_message(sample_kafka_message)
        await asyncio.sleep(0.1)

        assert "No handler matched for sender: user" in caplog.text

    @pytest.mark.asyncio
    async def test_on_kafka_message_handler_exception(
        self, mock_gateway_client, sample_agent_data, sample_kafka_message
    ):
        """Test handler exception triggers error response."""
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
        )

        @agent.on_message
        async def handler(message: Message, sender: str):
            raise ValueError("Test error")

        # Mock the streamer to track error response
        with patch.object(agent, 'streamer') as mock_streamer:
            mock_stream = MagicMock()
            mock_streamer.return_value.__aenter__ = AsyncMock(return_value=mock_stream)
            mock_streamer.return_value.__aexit__ = AsyncMock(return_value=False)

            agent._on_kafka_message(sample_kafka_message)
            await asyncio.sleep(0.1)

            # Verify error response was sent
            mock_streamer.assert_called_once()
            mock_stream.stream.assert_called_once_with(agent.error_message_template)

    @pytest.mark.asyncio
    async def test_on_kafka_message_message_creation_failure(
        self, mock_gateway_client, sample_agent_data, caplog
    ):
        """Test message creation failure doesn't trigger error response."""
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
        )

        @agent.on_message
        async def handler(message: Message, sender: str):
            pass

        # Create a valid Kafka message
        kafka_msg = KafkaMessage(
            topic="test-agent.inbox",
            partition=0,
            offset=100,
            key="conv-123",
            headers={"from_": "user"},
            body={"content": "test"},
            timestamp=1234567890
        )

        # Patch Message.from_kafka_message to raise an exception
        with patch.object(agent, 'streamer') as mock_streamer, \
             patch('march_agent.agent.Message.from_kafka_message', side_effect=Exception("Message creation failed")):
            agent._on_kafka_message(kafka_msg)
            await asyncio.sleep(0.1)

            # Error response should NOT be called (no message context)
            mock_streamer.assert_not_called()

            # Error should be logged
            assert "Error processing Kafka message before handler execution" in caplog.text


class TestErrorResponse:
    """Test error response functionality (fault tolerance)."""

    @pytest.mark.asyncio
    async def test_send_error_response_async_success(
        self, mock_gateway_client, sample_agent_data, sample_message
    ):
        """Test async error response is sent successfully."""
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
        )

        error = ValueError("Test error")

        with patch.object(agent, 'streamer') as mock_streamer:
            mock_stream = MagicMock()
            mock_streamer.return_value.__aenter__ = AsyncMock(return_value=mock_stream)
            mock_streamer.return_value.__aexit__ = AsyncMock(return_value=False)

            await agent._send_error_response_async(sample_message, error, "test_handler")

            # Verify streamer was created with correct params
            mock_streamer.assert_called_once_with(
                original_message=sample_message,
                send_to="user"
            )

            # Verify error message was streamed
            mock_stream.stream.assert_called_once_with(agent.error_message_template)

    @pytest.mark.asyncio
    async def test_send_error_response_async_with_handler_name(
        self, mock_gateway_client, sample_agent_data, sample_message, caplog
    ):
        """Test error response includes handler name in logs."""
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
        )

        error = ValueError("Test error")

        with patch.object(agent, 'streamer') as mock_streamer:
            mock_stream = MagicMock()
            mock_streamer.return_value.__aenter__ = AsyncMock(return_value=mock_stream)
            mock_streamer.return_value.__aexit__ = AsyncMock(return_value=False)

            await agent._send_error_response_async(sample_message, error, "my_handler")

            assert "in handler 'my_handler'" in caplog.text

    @pytest.mark.asyncio
    async def test_send_error_response_async_disabled(
        self, mock_gateway_client, sample_agent_data, sample_message
    ):
        """Test error response can be disabled."""
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
        )
        agent.send_error_responses = False

        error = ValueError("Test error")

        with patch.object(agent, 'streamer') as mock_streamer:
            await agent._send_error_response_async(sample_message, error)

            # Should not create streamer when disabled
            mock_streamer.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_error_response_async_streamer_failure(
        self, mock_gateway_client, sample_agent_data, sample_message, caplog
    ):
        """Test fail-safe when streamer itself fails."""
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
        )

        error = ValueError("Original error")

        with patch.object(agent, 'streamer') as mock_streamer:
            # Make streamer raise an exception
            mock_streamer.side_effect = Exception("Streamer failed")

            await agent._send_error_response_async(sample_message, error)

            # Should log the failure but not crash
            assert "Failed to send error response" in caplog.text
            assert "Streamer failed" in caplog.text

    @pytest.mark.asyncio
    async def test_send_error_response_async_custom_template(
        self, mock_gateway_client, sample_agent_data, sample_message
    ):
        """Test custom error template is used."""
        custom_template = "Our service is down. Please try again later."
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
            error_message_template=custom_template,
        )

        error = ValueError("Test error")

        with patch.object(agent, 'streamer') as mock_streamer:
            mock_stream = MagicMock()
            mock_streamer.return_value.__aenter__ = AsyncMock(return_value=mock_stream)
            mock_streamer.return_value.__aexit__ = AsyncMock(return_value=False)

            await agent._send_error_response_async(sample_message, error)

            # Verify custom template was used
            mock_stream.stream.assert_called_once_with(custom_template)


class TestStreamerCreation:
    """Test streamer creation."""

    def test_streamer_creation(self, mock_gateway_client, sample_agent_data, sample_message):
        """Test streamer instance is created correctly."""
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
        )

        streamer = agent.streamer(original_message=sample_message)

        assert streamer._agent_name == "test-agent"
        assert streamer._original_message == sample_message
        assert streamer._gateway_client == mock_gateway_client
        assert streamer._send_to == "user"
        assert streamer._awaiting is False

    def test_streamer_with_awaiting(
        self, mock_gateway_client, sample_agent_data, sample_message
    ):
        """Test streamer with awaiting parameter."""
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
        )

        streamer = agent.streamer(original_message=sample_message, awaiting=True)

        assert streamer._awaiting is True

    def test_streamer_with_send_to(
        self, mock_gateway_client, sample_agent_data, sample_message
    ):
        """Test streamer with custom send_to."""
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
        )

        streamer = agent.streamer(original_message=sample_message, send_to="agent-2")

        assert streamer._send_to == "agent-2"


class TestLifecycle:
    """Test agent lifecycle methods."""

    def test_initialize_with_gateway(self, mock_gateway_client, sample_agent_data):
        """Test gateway initialization registers handler and starts heartbeat."""
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
        )

        with patch('march_agent.agent.HeartbeatManager') as mock_heartbeat_class:
            mock_heartbeat = MagicMock()
            mock_heartbeat_class.return_value = mock_heartbeat

            agent._initialize_with_gateway()

            # Verify handler was registered with gateway
            mock_gateway_client.register_handler.assert_called_once_with(
                "test-agent.inbox", agent._on_kafka_message
            )

            # Verify heartbeat was started
            mock_heartbeat_class.assert_called_once()
            mock_heartbeat.start.assert_called_once()

            assert agent._initialized is True

    def test_initialize_with_gateway_idempotent(
        self, mock_gateway_client, sample_agent_data
    ):
        """Test initialization only runs once."""
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
        )

        with patch('march_agent.agent.HeartbeatManager') as mock_heartbeat_class:
            agent._initialize_with_gateway()
            agent._initialize_with_gateway()  # Call again

            # Should only be called once
            assert mock_heartbeat_class.call_count == 1

    def test_start_consuming_without_handlers(
        self, mock_gateway_client, sample_agent_data
    ):
        """Test starting without handlers raises error."""
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
        )

        with pytest.raises(ConfigurationError, match="No message handlers registered"):
            agent.start_consuming()

    def test_start_consuming_without_initialization(
        self, mock_gateway_client, sample_agent_data
    ):
        """Test starting without initialization raises error."""
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
        )

        @agent.on_message
        def handler(message: Message, sender: str):
            pass

        with pytest.raises(ConfigurationError, match="Agent not initialized"):
            agent.start_consuming()

    def test_shutdown(self, mock_gateway_client, sample_agent_data):
        """Test shutdown stops heartbeat and sets running flag."""
        agent = Agent(
            name="test-agent",
            gateway_client=mock_gateway_client,
            agent_data=sample_agent_data,
        )

        # Set up heartbeat manager
        mock_heartbeat = MagicMock()
        agent.heartbeat_manager = mock_heartbeat
        agent._running = True

        agent.shutdown()

        # Verify shutdown actions
        assert agent._running is False
        mock_heartbeat.stop.assert_called_once()

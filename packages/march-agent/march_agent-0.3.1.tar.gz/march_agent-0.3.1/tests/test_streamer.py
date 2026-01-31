"""Tests for Streamer class - Response streaming functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from march_agent.streamer import Streamer


class TestStreamerInitialization:
    """Test Streamer initialization."""

    def test_streamer_initialization(self, mock_gateway_client, sample_message):
        """Test basic streamer initialization."""
        streamer = Streamer(
            agent_name="test-agent",
            original_message=sample_message,
            gateway_client=mock_gateway_client
        )

        assert streamer._agent_name == "test-agent"
        assert streamer._original_message == sample_message
        assert streamer._gateway_client == mock_gateway_client
        assert streamer._send_to == "user"
        assert streamer._awaiting is False
        assert streamer._finished is False

    def test_streamer_defaults(self, mock_gateway_client, sample_message):
        """Test default parameter values."""
        streamer = Streamer(
            agent_name="test-agent",
            original_message=sample_message,
            gateway_client=mock_gateway_client
        )

        assert streamer._awaiting is False
        assert streamer._send_to == "user"


class TestStreaming:
    """Test streaming content."""

    def test_stream_sends_content(self, mock_gateway_client, sample_message):
        """Test stream() sends content via gateway."""
        streamer = Streamer(
            agent_name="test-agent",
            original_message=sample_message,
            gateway_client=mock_gateway_client
        )

        streamer.stream("Hello world")

        # Verify produce was called
        mock_gateway_client.produce.assert_called_once()
        call_kwargs = mock_gateway_client.produce.call_args[1]

        assert call_kwargs["topic"] == "router.inbox"
        assert call_kwargs["body"]["content"] == "Hello world"
        assert call_kwargs["body"]["done"] is False

    def test_stream_sets_done_false(self, mock_gateway_client, sample_message):
        """Test stream() sets done=False."""
        streamer = Streamer(
            agent_name="test-agent",
            original_message=sample_message,
            gateway_client=mock_gateway_client
        )

        streamer.stream("Content")

        call_kwargs = mock_gateway_client.produce.call_args[1]
        assert call_kwargs["body"]["done"] is False

    def test_stream_uses_conversation_id(
        self, mock_gateway_client, sample_message
    ):
        """Test stream() uses conversation ID from original message."""
        streamer = Streamer(
            agent_name="test-agent",
            original_message=sample_message,
            gateway_client=mock_gateway_client
        )

        streamer.stream("Content")

        call_kwargs = mock_gateway_client.produce.call_args[1]
        assert call_kwargs["key"] == sample_message.conversation_id
        assert (
            call_kwargs["headers"]["conversationId"]
            == sample_message.conversation_id
        )

    def test_stream_sets_from_header(self, mock_gateway_client, sample_message):
        """Test stream() sets from_ header to agent name."""
        streamer = Streamer(
            agent_name="my-agent",
            original_message=sample_message,
            gateway_client=mock_gateway_client
        )

        streamer.stream("Content")

        call_kwargs = mock_gateway_client.produce.call_args[1]
        assert call_kwargs["headers"]["from_"] == "my-agent"

    def test_stream_sets_next_route(self, mock_gateway_client, sample_message):
        """Test stream() sets nextRoute header."""
        streamer = Streamer(
            agent_name="test-agent",
            original_message=sample_message,
            gateway_client=mock_gateway_client,
            send_to="agent-2"
        )

        streamer.stream("Content")

        call_kwargs = mock_gateway_client.produce.call_args[1]
        assert call_kwargs["headers"]["nextRoute"] == "agent-2"

    def test_write_alias(self, mock_gateway_client, sample_message):
        """Test write() is an alias for stream()."""
        streamer = Streamer(
            agent_name="test-agent",
            original_message=sample_message,
            gateway_client=mock_gateway_client
        )

        streamer.write("Content via write")

        # Should call produce just like stream()
        mock_gateway_client.produce.assert_called_once()
        call_kwargs = mock_gateway_client.produce.call_args[1]
        assert call_kwargs["body"]["content"] == "Content via write"


class TestFinish:
    """Test finish() method."""

    @pytest.mark.asyncio
    async def test_finish_sends_done_true(
        self, mock_gateway_client, sample_message
    ):
        """Test finish() sends done=True."""
        streamer = Streamer(
            agent_name="test-agent",
            original_message=sample_message,
            gateway_client=mock_gateway_client
        )

        await streamer.finish()

        call_kwargs = mock_gateway_client.produce.call_args[1]
        assert call_kwargs["body"]["done"] is True
        assert call_kwargs["body"]["content"] == ""

    @pytest.mark.asyncio
    async def test_finish_idempotent(self, mock_gateway_client, sample_message):
        """Test finish() can be called multiple times safely."""
        streamer = Streamer(
            agent_name="test-agent",
            original_message=sample_message,
            gateway_client=mock_gateway_client
        )

        await streamer.finish()
        await streamer.finish()  # Call again

        # Should only produce once
        assert mock_gateway_client.produce.call_count == 1

    @pytest.mark.asyncio
    async def test_finish_with_awaiting_false(
        self, mock_gateway_client, sample_message, mock_conversation_client
    ):
        """Test finish() with awaiting=False doesn't update conversation."""
        streamer = Streamer(
            agent_name="test-agent",
            original_message=sample_message,
            gateway_client=mock_gateway_client,
            conversation_client=mock_conversation_client,
            awaiting=False
        )

        await streamer.finish()

        # Should not update conversation
        mock_conversation_client.update_conversation.assert_not_called()

    @pytest.mark.asyncio
    async def test_finish_with_awaiting_true(
        self, mock_gateway_client, sample_message, mock_conversation_client
    ):
        """Test finish() with awaiting=True updates conversation."""
        streamer = Streamer(
            agent_name="test-agent",
            original_message=sample_message,
            gateway_client=mock_gateway_client,
            conversation_client=mock_conversation_client,
            awaiting=True
        )

        await streamer.finish()

        # Should update conversation with awaiting_route
        mock_conversation_client.update_conversation.assert_called_once()


class TestContextManager:
    """Test context manager functionality."""

    @pytest.mark.asyncio
    async def test_context_manager_enter_returns_self(
        self, mock_gateway_client, sample_message
    ):
        """Test __aenter__ returns self."""
        streamer = Streamer(
            agent_name="test-agent",
            original_message=sample_message,
            gateway_client=mock_gateway_client
        )

        async with streamer as s:
            assert s is streamer

    @pytest.mark.asyncio
    async def test_context_manager_exit_calls_finish(
        self, mock_gateway_client, sample_message
    ):
        """Test __aexit__ automatically calls finish()."""
        streamer = Streamer(
            agent_name="test-agent",
            original_message=sample_message,
            gateway_client=mock_gateway_client
        )

        async with streamer as s:
            s.stream("Content")

        # finish() should have been called automatically
        # Check that done=True was sent
        calls = mock_gateway_client.produce.call_args_list
        last_call = calls[-1]
        assert last_call[1]["body"]["done"] is True

    @pytest.mark.asyncio
    async def test_context_manager_uses_awaiting_param(
        self, mock_gateway_client, sample_message, mock_conversation_client
    ):
        """Test context manager uses awaiting parameter."""
        streamer = Streamer(
            agent_name="test-agent",
            original_message=sample_message,
            gateway_client=mock_gateway_client,
            conversation_client=mock_conversation_client,
            awaiting=True
        )

        async with streamer as s:
            s.stream("Content")

        # Should update conversation because awaiting=True
        mock_conversation_client.update_conversation.assert_called_once()


class TestFluentAPI:
    """Test fluent API methods."""

    def test_set_response_schema(self, mock_gateway_client, sample_message):
        """Test set_response_schema() returns self and stores schema."""
        streamer = Streamer(
            agent_name="test-agent",
            original_message=sample_message,
            gateway_client=mock_gateway_client
        )

        schema = {
            "type": "object",
            "properties": {"answer": {"type": "string"}}
        }
        result = streamer.set_response_schema(schema)

        # Should return self for chaining
        assert result is streamer
        # Should store schema
        assert streamer._response_schema == schema

    def test_set_message_metadata(self, mock_gateway_client, sample_message):
        """Test set_message_metadata() returns self and stores metadata."""
        streamer = Streamer(
            agent_name="test-agent",
            original_message=sample_message,
            gateway_client=mock_gateway_client
        )

        metadata = {"priority": "high", "tags": ["urgent"]}
        result = streamer.set_message_metadata(metadata)

        # Should return self for chaining
        assert result is streamer
        # Should store metadata
        assert streamer._message_metadata == metadata

    def test_fluent_chaining(self, mock_gateway_client, sample_message):
        """Test fluent API can be chained."""
        streamer = Streamer(
            agent_name="test-agent",
            original_message=sample_message,
            gateway_client=mock_gateway_client
        )

        schema = {"type": "object"}
        metadata = {"key": "value"}

        # Chain calls
        result = (
            streamer.set_response_schema(schema)
            .set_message_metadata(metadata)
        )

        assert result is streamer
        assert streamer._response_schema == schema
        assert streamer._message_metadata == metadata


class TestMetadata:
    """Test metadata operations."""

    @pytest.mark.asyncio
    async def test_set_pending_response_schema_success(
        self, mock_gateway_client, sample_message, mock_conversation_client
    ):
        """Test schema is saved to conversation."""
        streamer = Streamer(
            agent_name="test-agent",
            original_message=sample_message,
            gateway_client=mock_gateway_client,
            conversation_client=mock_conversation_client
        )

        schema = {"type": "object"}
        streamer.set_response_schema(schema)
        await streamer.finish()

        # Verify conversation update was called
        mock_conversation_client.update_conversation.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_pending_response_schema_failure(
        self, mock_gateway_client, sample_message, mock_conversation_client, caplog
    ):
        """Test schema update failure is logged but doesn't crash."""
        mock_conversation_client.update_conversation.side_effect = Exception(
            "Update failed"
        )

        streamer = Streamer(
            agent_name="test-agent",
            original_message=sample_message,
            gateway_client=mock_gateway_client,
            conversation_client=mock_conversation_client
        )

        schema = {"type": "object"}
        streamer.set_response_schema(schema)
        await streamer.finish()

        # Should log error but not crash
        assert "Failed to set pending_response_schema" in caplog.text

    @pytest.mark.asyncio
    async def test_set_awaiting_route_success(
        self, mock_gateway_client, sample_message, mock_conversation_client
    ):
        """Test awaiting_route is set on conversation."""
        streamer = Streamer(
            agent_name="test-agent",
            original_message=sample_message,
            gateway_client=mock_gateway_client,
            conversation_client=mock_conversation_client,
            awaiting=True
        )

        await streamer.finish()

        # Verify conversation was updated
        mock_conversation_client.update_conversation.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_awaiting_route_failure(
        self, mock_gateway_client, sample_message, mock_conversation_client, caplog
    ):
        """Test awaiting route update failure is logged but doesn't crash."""
        mock_conversation_client.update_conversation.side_effect = Exception(
            "Update failed"
        )

        streamer = Streamer(
            agent_name="test-agent",
            original_message=sample_message,
            gateway_client=mock_gateway_client,
            conversation_client=mock_conversation_client,
            awaiting=True
        )

        await streamer.finish()

        # Should log error but not crash
        assert "Failed to set awaiting_route" in caplog.text

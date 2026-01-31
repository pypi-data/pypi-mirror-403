"""Comprehensive tests for Conversation class."""

import pytest
from unittest.mock import Mock, AsyncMock
from march_agent.conversation import Conversation
from march_agent.conversation_client import ConversationClient
from march_agent.conversation_message import ConversationMessage


class TestConversation:
    """Test Conversation wrapper class."""

    @pytest.mark.asyncio
    async def test_conversation_initialization(self):
        """Test Conversation initialization."""
        client = Mock(spec=ConversationClient)
        conversation = Conversation(
            conversation_id="conv-123",
            client=client
        )

        assert conversation.id == "conv-123"
        assert conversation._client is client
        assert conversation._agent_name is None

    @pytest.mark.asyncio
    async def test_conversation_initialization_with_agent_name(self):
        """Test Conversation initialization with agent name."""
        client = Mock(spec=ConversationClient)
        conversation = Conversation(
            conversation_id="conv-123",
            client=client,
            agent_name="my-agent"
        )

        assert conversation._agent_name == "my-agent"

    @pytest.mark.asyncio
    async def test_get_history_basic(self):
        """Test getting conversation history."""
        client = Mock(spec=ConversationClient)
        client.get_messages = AsyncMock(return_value=[
            {
                "id": "msg-1",
                "content": "Hello",
                "role": "user",
                "from_": "user",
                "to_": "agent",
                "sequence_number": 1
            },
            {
                "id": "msg-2",
                "content": "Hi there!",
                "role": "assistant",
                "from_": "agent",
                "to_": "user",
                "sequence_number": 2
            }
        ])

        conversation = Conversation(conversation_id="conv-123", client=client)
        messages = await conversation.get_history()

        assert len(messages) == 2
        assert all(isinstance(msg, ConversationMessage) for msg in messages)
        assert messages[0].content == "Hello"
        assert messages[1].content == "Hi there!"

        # Verify client called with correct params
        client.get_messages.assert_called_once_with(
            conversation_id="conv-123",
            role=None,
            limit=100,
            offset=0
        )

    @pytest.mark.asyncio
    async def test_get_history_with_role_filter(self):
        """Test getting history filtered by role."""
        client = Mock(spec=ConversationClient)
        client.get_messages = AsyncMock(return_value=[
            {
                "id": "msg-1",
                "content": "Hello",
                "role": "user",
                "from_": "user",
                "to_": "agent",
                "sequence_number": 1
            }
        ])

        conversation = Conversation(conversation_id="conv-123", client=client)
        messages = await conversation.get_history(role="user")

        assert len(messages) == 1
        assert messages[0].role == "user"

        # Verify role parameter passed
        client.get_messages.assert_called_once_with(
            conversation_id="conv-123",
            role="user",
            limit=100,
            offset=0
        )

    @pytest.mark.asyncio
    async def test_get_history_with_limit(self):
        """Test getting history with custom limit."""
        client = Mock(spec=ConversationClient)
        client.get_messages = AsyncMock(return_value=[])

        conversation = Conversation(conversation_id="conv-123", client=client)
        await conversation.get_history(limit=50)

        client.get_messages.assert_called_once_with(
            conversation_id="conv-123",
            role=None,
            limit=50,
            offset=0
        )

    @pytest.mark.asyncio
    async def test_get_history_with_offset(self):
        """Test getting history with pagination offset."""
        client = Mock(spec=ConversationClient)
        client.get_messages = AsyncMock(return_value=[])

        conversation = Conversation(conversation_id="conv-123", client=client)
        await conversation.get_history(offset=20)

        client.get_messages.assert_called_once_with(
            conversation_id="conv-123",
            role=None,
            limit=100,
            offset=20
        )

    @pytest.mark.asyncio
    async def test_get_history_with_all_parameters(self):
        """Test getting history with all parameters."""
        client = Mock(spec=ConversationClient)
        client.get_messages = AsyncMock(return_value=[])

        conversation = Conversation(conversation_id="conv-123", client=client)
        await conversation.get_history(role="assistant", limit=25, offset=10)

        client.get_messages.assert_called_once_with(
            conversation_id="conv-123",
            role="assistant",
            limit=25,
            offset=10
        )

    @pytest.mark.asyncio
    async def test_get_metadata(self):
        """Test getting conversation metadata."""
        client = Mock(spec=ConversationClient)
        client.get_conversation = AsyncMock(return_value={
            "id": "conv-123",
            "status": "active",
            "user_id": "user-1",
            "created_at": "2024-01-15T10:00:00Z"
        })

        conversation = Conversation(conversation_id="conv-123", client=client)
        metadata = await conversation.get_metadata()

        assert metadata["id"] == "conv-123"
        assert metadata["status"] == "active"
        assert metadata["user_id"] == "user-1"

        client.get_conversation.assert_called_once_with("conv-123")

    @pytest.mark.asyncio
    async def test_get_agent_history_with_explicit_agent_name(self):
        """Test getting agent-specific history with explicit agent name."""
        client = Mock(spec=ConversationClient)

        # Mock responses for sent and received messages
        sent_messages = [
            {
                "id": "msg-2",
                "content": "Response",
                "role": "assistant",
                "from_": "my-agent",
                "to_": "user",
                "sequence_number": 2
            }
        ]

        received_messages = [
            {
                "id": "msg-1",
                "content": "Question",
                "role": "user",
                "from_": "user",
                "to_": "my-agent",
                "sequence_number": 1
            }
        ]

        client.get_messages = AsyncMock(side_effect=[sent_messages, received_messages])

        conversation = Conversation(conversation_id="conv-123", client=client)
        messages = await conversation.get_agent_history(agent_name="my-agent")

        assert len(messages) == 2
        # Should be sorted by sequence_number
        assert messages[0].content == "Question"
        assert messages[1].content == "Response"

        # Verify two calls were made
        assert client.get_messages.call_count == 2

        # First call: messages sent by agent
        first_call = client.get_messages.call_args_list[0]
        assert first_call[1]["from_"] == "my-agent"
        assert "to_" not in first_call[1]

        # Second call: messages received by agent
        second_call = client.get_messages.call_args_list[1]
        assert second_call[1]["to_"] == "my-agent"
        assert "from_" not in second_call[1]

    @pytest.mark.asyncio
    async def test_get_agent_history_with_default_agent_name(self):
        """Test getting agent history using default agent name from init."""
        client = Mock(spec=ConversationClient)
        client.get_messages = AsyncMock(return_value=[])

        conversation = Conversation(
            conversation_id="conv-123",
            client=client,
            agent_name="default-agent"
        )

        await conversation.get_agent_history()

        # Should use default agent name
        first_call = client.get_messages.call_args_list[0]
        assert first_call[1]["from_"] == "default-agent"

    @pytest.mark.asyncio
    async def test_get_agent_history_no_agent_name_raises_error(self):
        """Test that get_agent_history raises error when no agent name provided."""
        client = Mock(spec=ConversationClient)

        conversation = Conversation(conversation_id="conv-123", client=client)

        with pytest.raises(ValueError, match="agent_name must be provided"):
            await conversation.get_agent_history()

    @pytest.mark.asyncio
    async def test_get_agent_history_with_role_filter(self):
        """Test getting agent history with role filter."""
        client = Mock(spec=ConversationClient)
        client.get_messages = AsyncMock(return_value=[])

        conversation = Conversation(
            conversation_id="conv-123",
            client=client,
            agent_name="my-agent"
        )

        await conversation.get_agent_history(role="assistant")

        # Both calls should include role filter
        first_call = client.get_messages.call_args_list[0]
        assert first_call[1]["role"] == "assistant"

        second_call = client.get_messages.call_args_list[1]
        assert second_call[1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_get_agent_history_with_limit_and_offset(self):
        """Test getting agent history with limit and offset."""
        client = Mock(spec=ConversationClient)
        client.get_messages = AsyncMock(return_value=[])

        conversation = Conversation(
            conversation_id="conv-123",
            client=client,
            agent_name="my-agent"
        )

        await conversation.get_agent_history(limit=50, offset=10)

        # Both calls should include limit and offset
        first_call = client.get_messages.call_args_list[0]
        assert first_call[1]["limit"] == 50
        assert first_call[1]["offset"] == 10

        second_call = client.get_messages.call_args_list[1]
        assert second_call[1]["limit"] == 50
        assert second_call[1]["offset"] == 10

    @pytest.mark.asyncio
    async def test_get_agent_history_deduplication(self):
        """Test that get_agent_history deduplicates messages where from_==to_."""
        client = Mock(spec=ConversationClient)

        # Simulate case where agent sends message to itself
        duplicate_msg = {
            "id": "msg-self",
            "content": "Self message",
            "role": "assistant",
            "from_": "my-agent",
            "to_": "my-agent",
            "sequence_number": 1
        }

        sent_messages = [duplicate_msg]
        received_messages = [duplicate_msg]  # Same message appears in both queries

        client.get_messages = AsyncMock(side_effect=[sent_messages, received_messages])

        conversation = Conversation(
            conversation_id="conv-123",
            client=client,
            agent_name="my-agent"
        )

        messages = await conversation.get_agent_history()

        # Should only have one message, not two
        assert len(messages) == 1
        assert messages[0].id == "msg-self"

    @pytest.mark.asyncio
    async def test_get_agent_history_sorting_by_sequence_number(self):
        """Test that messages are sorted by sequence_number."""
        client = Mock(spec=ConversationClient)

        sent_messages = [
            {
                "id": "msg-3",
                "content": "Third",
                "role": "assistant",
                "from_": "my-agent",
                "to_": "user",
                "sequence_number": 3
            }
        ]

        received_messages = [
            {
                "id": "msg-1",
                "content": "First",
                "role": "user",
                "from_": "user",
                "to_": "my-agent",
                "sequence_number": 1
            },
            {
                "id": "msg-2",
                "content": "Second",
                "role": "user",
                "from_": "user",
                "to_": "my-agent",
                "sequence_number": 2
            }
        ]

        client.get_messages = AsyncMock(side_effect=[sent_messages, received_messages])

        conversation = Conversation(
            conversation_id="conv-123",
            client=client,
            agent_name="my-agent"
        )

        messages = await conversation.get_agent_history()

        # Should be sorted: 1, 2, 3
        assert len(messages) == 3
        assert messages[0].content == "First"
        assert messages[1].content == "Second"
        assert messages[2].content == "Third"

    @pytest.mark.asyncio
    async def test_get_agent_history_empty_results(self):
        """Test get_agent_history with no messages."""
        client = Mock(spec=ConversationClient)
        client.get_messages = AsyncMock(return_value=[])

        conversation = Conversation(
            conversation_id="conv-123",
            client=client,
            agent_name="my-agent"
        )

        messages = await conversation.get_agent_history()

        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_get_agent_history_concurrent_execution(self):
        """Test that get_agent_history executes queries concurrently."""
        client = Mock(spec=ConversationClient)

        # Track call order
        call_order = []

        async def track_call(*args, **kwargs):
            call_order.append(kwargs.get("from_") or kwargs.get("to_"))
            return []

        client.get_messages = AsyncMock(side_effect=track_call)

        conversation = Conversation(
            conversation_id="conv-123",
            client=client,
            agent_name="my-agent"
        )

        await conversation.get_agent_history()

        # Both calls should have been made (asyncio.gather ensures concurrency)
        assert len(call_order) == 2
        assert "my-agent" in call_order

    @pytest.mark.asyncio
    async def test_get_agent_history_overrides_default_agent_name(self):
        """Test that explicit agent_name parameter overrides default."""
        client = Mock(spec=ConversationClient)
        client.get_messages = AsyncMock(return_value=[])

        conversation = Conversation(
            conversation_id="conv-123",
            client=client,
            agent_name="default-agent"
        )

        await conversation.get_agent_history(agent_name="override-agent")

        # Should use override, not default
        first_call = client.get_messages.call_args_list[0]
        assert first_call[1]["from_"] == "override-agent"

    @pytest.mark.asyncio
    async def test_get_agent_history_all_parameters(self):
        """Test get_agent_history with all parameters."""
        client = Mock(spec=ConversationClient)
        client.get_messages = AsyncMock(return_value=[])

        conversation = Conversation(conversation_id="conv-123", client=client)

        await conversation.get_agent_history(
            agent_name="test-agent",
            role="assistant",
            limit=30,
            offset=5
        )

        # Verify all parameters passed to both queries
        first_call = client.get_messages.call_args_list[0]
        assert first_call[1]["conversation_id"] == "conv-123"
        assert first_call[1]["role"] == "assistant"
        assert first_call[1]["from_"] == "test-agent"
        assert first_call[1]["limit"] == 30
        assert first_call[1]["offset"] == 5

        second_call = client.get_messages.call_args_list[1]
        assert second_call[1]["conversation_id"] == "conv-123"
        assert second_call[1]["role"] == "assistant"
        assert second_call[1]["to_"] == "test-agent"
        assert second_call[1]["limit"] == 30
        assert second_call[1]["offset"] == 5

    @pytest.mark.asyncio
    async def test_conversation_preserves_id(self):
        """Test that conversation ID is preserved across operations."""
        client = Mock(spec=ConversationClient)
        client.get_messages = AsyncMock(return_value=[])
        client.get_conversation = AsyncMock(return_value={"id": "conv-123"})

        conversation = Conversation(conversation_id="conv-123", client=client)

        await conversation.get_history()
        await conversation.get_metadata()

        # Verify conversation ID used consistently
        assert client.get_messages.call_args[1]["conversation_id"] == "conv-123"
        assert client.get_conversation.call_args[0][0] == "conv-123"

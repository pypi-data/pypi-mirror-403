"""Unit tests for PydanticAIMessageStore extension."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys

# Mock pydantic_ai before importing the extension
mock_pydantic_ai = MagicMock()
mock_pydantic_ai.messages = MagicMock()


# Create mock TypeAdapter that behaves like Pydantic's TypeAdapter
class MockTypeAdapter:
    @staticmethod
    def validate_python(data):
        """Return data as-is for testing."""
        return data

    @staticmethod
    def dump_python(data, mode=None):
        """Return data as-is for testing."""
        return data


mock_pydantic_ai.messages.ModelMessagesTypeAdapter = MockTypeAdapter
mock_pydantic_ai.messages.ModelMessage = MagicMock

sys.modules['pydantic_ai'] = mock_pydantic_ai
sys.modules['pydantic_ai.messages'] = mock_pydantic_ai.messages

from march_agent.extensions.pydantic_ai import PydanticAIMessageStore
from march_agent.agent_state_client import AgentStateClient


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def mock_app():
    """Create mock MarchAgentApp."""
    app = MagicMock()
    app.gateway_client = MagicMock()
    app.gateway_client.conversation_store_url = "http://gateway/s/conversation-store"
    return app


@pytest.fixture
def mock_agent_state_client():
    """Create mock AgentStateClient."""
    client = MagicMock(spec=AgentStateClient)
    client.get = AsyncMock(return_value=None)
    client.put = AsyncMock(return_value={"conversation_id": "test", "created": True})
    client.delete = AsyncMock(return_value={"deleted": 1})
    client.close = AsyncMock()
    return client


@pytest.fixture
def message_store(mock_app, mock_agent_state_client):
    """Create PydanticAIMessageStore with mocked client."""
    with patch.object(PydanticAIMessageStore, '__init__', lambda self, app: None):
        store = PydanticAIMessageStore.__new__(PydanticAIMessageStore)
        store.client = mock_agent_state_client
        store._app = mock_app
        return store


# ==============================================================================
# Initialization Tests
# ==============================================================================


def test_init_creates_client(mock_app):
    """Test that __init__ creates AgentStateClient with correct URL."""
    with patch('march_agent.extensions.pydantic_ai.AgentStateClient') as MockClient:
        store = PydanticAIMessageStore(app=mock_app)

        MockClient.assert_called_once_with("http://gateway/s/conversation-store")
        assert store._app is mock_app


def test_namespace_constant():
    """Test that NAMESPACE is set correctly."""
    assert PydanticAIMessageStore.NAMESPACE == "pydantic_ai"


# ==============================================================================
# load() Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_load_returns_empty_list_when_no_history(message_store, mock_agent_state_client):
    """Test load() returns empty list when no history exists."""
    mock_agent_state_client.get.return_value = None

    result = await message_store.load("conv-123")

    assert result == []
    mock_agent_state_client.get.assert_called_once_with("conv-123", "pydantic_ai")


@pytest.mark.asyncio
async def test_load_returns_empty_list_when_empty_state(message_store, mock_agent_state_client):
    """Test load() returns empty list when state has no messages."""
    mock_agent_state_client.get.return_value = {
        "conversation_id": "conv-123",
        "namespace": "pydantic_ai",
        "state": {},
    }

    result = await message_store.load("conv-123")

    assert result == []


@pytest.mark.asyncio
async def test_load_returns_messages(message_store, mock_agent_state_client):
    """Test load() returns messages when they exist."""
    mock_messages = [
        {"kind": "request", "parts": [{"part_kind": "user-prompt", "content": "Hello"}]},
        {"kind": "response", "parts": [{"part_kind": "text", "content": "Hi!"}]},
    ]
    mock_agent_state_client.get.return_value = {
        "conversation_id": "conv-123",
        "namespace": "pydantic_ai",
        "state": {"messages": mock_messages},
    }

    result = await message_store.load("conv-123")

    assert result == mock_messages
    mock_agent_state_client.get.assert_called_once_with("conv-123", "pydantic_ai")


@pytest.mark.asyncio
async def test_load_deserializes_messages(message_store, mock_agent_state_client):
    """Test load() uses ModelMessagesTypeAdapter to deserialize."""
    mock_messages = [
        {"kind": "request", "parts": [{"part_kind": "user-prompt", "content": "Test"}]},
    ]
    mock_agent_state_client.get.return_value = {
        "state": {"messages": mock_messages},
    }

    with patch.object(MockTypeAdapter, 'validate_python', return_value=mock_messages) as mock_validate:
        result = await message_store.load("conv-123")

        mock_validate.assert_called_once_with(mock_messages)
        assert result == mock_messages


@pytest.mark.asyncio
async def test_load_handles_deserialization_error(message_store, mock_agent_state_client):
    """Test load() returns empty list on deserialization error."""
    mock_agent_state_client.get.return_value = {
        "state": {"messages": [{"invalid": "data"}]},
    }

    with patch.object(MockTypeAdapter, 'validate_python', side_effect=Exception("Parse error")):
        result = await message_store.load("conv-123")

        assert result == []


# ==============================================================================
# save() Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_save_stores_messages(message_store, mock_agent_state_client):
    """Test save() stores messages correctly."""
    messages = [
        {"kind": "request", "parts": [{"part_kind": "user-prompt", "content": "Hello"}]},
        {"kind": "response", "parts": [{"part_kind": "text", "content": "Hi!"}]},
    ]

    await message_store.save("conv-123", messages)

    mock_agent_state_client.put.assert_called_once()
    call_args = mock_agent_state_client.put.call_args
    assert call_args[0][0] == "conv-123"
    assert call_args[0][1] == "pydantic_ai"
    assert call_args[0][2] == {"messages": messages}


@pytest.mark.asyncio
async def test_save_serializes_messages(message_store, mock_agent_state_client):
    """Test save() uses ModelMessagesTypeAdapter to serialize."""
    messages = [{"kind": "request", "parts": []}]
    serialized = [{"kind": "request", "parts": [], "serialized": True}]

    with patch.object(MockTypeAdapter, 'dump_python', return_value=serialized) as mock_dump:
        await message_store.save("conv-123", messages)

        mock_dump.assert_called_once_with(messages, mode="json")

        # Verify serialized data was sent
        call_args = mock_agent_state_client.put.call_args
        assert call_args[0][2] == {"messages": serialized}


@pytest.mark.asyncio
async def test_save_raises_on_serialization_error(message_store, mock_agent_state_client):
    """Test save() raises exception on serialization error."""
    messages = [{"invalid": "message"}]

    with patch.object(MockTypeAdapter, 'dump_python', side_effect=Exception("Serialize error")):
        with pytest.raises(Exception) as exc_info:
            await message_store.save("conv-123", messages)

        assert "Serialize error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_save_empty_messages(message_store, mock_agent_state_client):
    """Test save() handles empty message list."""
    await message_store.save("conv-123", [])

    mock_agent_state_client.put.assert_called_once()
    call_args = mock_agent_state_client.put.call_args
    assert call_args[0][2] == {"messages": []}


# ==============================================================================
# clear() Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_clear_deletes_state(message_store, mock_agent_state_client):
    """Test clear() deletes the agent state."""
    await message_store.clear("conv-123")

    mock_agent_state_client.delete.assert_called_once_with("conv-123", "pydantic_ai")


@pytest.mark.asyncio
async def test_clear_uses_correct_namespace(message_store, mock_agent_state_client):
    """Test clear() uses the pydantic_ai namespace."""
    await message_store.clear("any-conv")

    call_args = mock_agent_state_client.delete.call_args
    assert call_args[0][1] == "pydantic_ai"


# ==============================================================================
# close() Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_close_closes_client(message_store, mock_agent_state_client):
    """Test close() closes the underlying client."""
    await message_store.close()

    mock_agent_state_client.close.assert_called_once()


# ==============================================================================
# Integration Flow Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_message_history_flow(message_store, mock_agent_state_client):
    """Test a complete message history flow: load -> save -> load."""
    # Initial load - empty
    mock_agent_state_client.get.return_value = None

    history = await message_store.load("conv-flow")
    assert history == []

    # First message exchange
    first_exchange = [
        {"kind": "request", "parts": [{"content": "Hello"}]},
        {"kind": "response", "parts": [{"content": "Hi!"}]},
    ]

    await message_store.save("conv-flow", first_exchange)

    # Simulate loaded state
    mock_agent_state_client.get.return_value = {
        "state": {"messages": first_exchange},
    }

    # Load again
    history = await message_store.load("conv-flow")
    assert len(history) == 2

    # Second message exchange - append
    second_exchange = history + [
        {"kind": "request", "parts": [{"content": "How are you?"}]},
        {"kind": "response", "parts": [{"content": "I'm good!"}]},
    ]

    await message_store.save("conv-flow", second_exchange)

    # Verify save was called with all messages
    final_call = mock_agent_state_client.put.call_args
    assert len(final_call[0][2]["messages"]) == 4


@pytest.mark.asyncio
async def test_multiple_conversations_independent(message_store, mock_agent_state_client):
    """Test that different conversations are independent."""
    # Save to conv-1
    await message_store.save("conv-1", [{"kind": "request", "parts": [{"content": "Conv 1"}]}])

    # Save to conv-2
    await message_store.save("conv-2", [{"kind": "request", "parts": [{"content": "Conv 2"}]}])

    # Verify both were saved with correct conversation IDs
    calls = mock_agent_state_client.put.call_args_list
    assert len(calls) == 2
    assert calls[0][0][0] == "conv-1"
    assert calls[1][0][0] == "conv-2"

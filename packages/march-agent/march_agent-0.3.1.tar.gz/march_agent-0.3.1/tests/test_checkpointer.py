"""Unit tests for HTTPCheckpointSaver (LangGraph-compatible checkpointer)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from march_agent.extensions.langgraph import HTTPCheckpointSaver
from march_agent.exceptions import APIException


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def mock_app():
    """Create mock MarchAgentApp."""
    app = MagicMock()
    app.gateway_client = MagicMock()
    app.gateway_client.conversation_store_url = "http://gateway:8080/s/conversation-store"
    return app


@pytest.fixture
def mock_checkpoint_client():
    """Mock CheckpointClient for testing."""
    client = MagicMock()
    client.put = AsyncMock(return_value={
        "config": {
            "configurable": {
                "thread_id": "thread-1",
                "checkpoint_ns": "",
                "checkpoint_id": "cp-1",
            }
        }
    })
    client.get_tuple = AsyncMock(return_value=None)
    client.list = AsyncMock(return_value=[])
    client.delete_thread = AsyncMock(return_value={"thread_id": "thread-1", "deleted": 0})
    client.close = AsyncMock()
    return client


@pytest.fixture
def checkpointer_with_mock_client(mock_app, mock_checkpoint_client):
    """Create HTTPCheckpointSaver with mocked CheckpointClient."""
    saver = HTTPCheckpointSaver(app=mock_app)
    saver.client = mock_checkpoint_client
    return saver


# ==============================================================================
# Initialization Tests
# ==============================================================================


def test_init_with_app(mock_app):
    """Test initialization with MarchAgentApp."""
    saver = HTTPCheckpointSaver(app=mock_app)

    assert saver.client.base_url == "http://gateway:8080/s/conversation-store"


# ==============================================================================
# aget_tuple() Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_aget_tuple_calls_client(checkpointer_with_mock_client, mock_checkpoint_client):
    """Test aget_tuple() calls client correctly."""
    config = {
        "configurable": {
            "thread_id": "thread-1",
            "checkpoint_ns": "",
            "checkpoint_id": "cp-1",
        }
    }

    await checkpointer_with_mock_client.aget_tuple(config)

    mock_checkpoint_client.get_tuple.assert_called_once_with(
        thread_id="thread-1",
        checkpoint_ns="",
        checkpoint_id="cp-1",
    )


@pytest.mark.asyncio
async def test_aget_tuple_returns_none_when_not_found(checkpointer_with_mock_client, mock_checkpoint_client):
    """Test aget_tuple() returns None when checkpoint not found."""
    mock_checkpoint_client.get_tuple.return_value = None
    config = {"configurable": {"thread_id": "thread-1"}}

    result = await checkpointer_with_mock_client.aget_tuple(config)

    assert result is None


@pytest.mark.asyncio
async def test_aget_tuple_missing_thread_id_raises(checkpointer_with_mock_client):
    """Test aget_tuple() raises ValueError when thread_id missing."""
    config = {"configurable": {}}

    with pytest.raises(ValueError) as exc_info:
        await checkpointer_with_mock_client.aget_tuple(config)

    assert "thread_id" in str(exc_info.value)


@pytest.mark.asyncio
async def test_aget_tuple_converts_response(checkpointer_with_mock_client, mock_checkpoint_client):
    """Test aget_tuple() converts response to CheckpointTuple format."""
    mock_checkpoint_client.get_tuple.return_value = {
        "config": {
            "configurable": {
                "thread_id": "thread-1",
                "checkpoint_ns": "",
                "checkpoint_id": "cp-1",
            }
        },
        "checkpoint": {
            "v": 1,
            "id": "cp-1",
            "ts": "2024-01-01T00:00:00+00:00",
            "channel_values": {"messages": []},
            "channel_versions": {},
            "versions_seen": {},
            "pending_sends": [],
        },
        "metadata": {
            "source": "input",
            "step": -1,
            "writes": None,
            "parents": {},
        },
        "parent_config": None,
        "pending_writes": None,
    }

    config = {"configurable": {"thread_id": "thread-1"}}
    result = await checkpointer_with_mock_client.aget_tuple(config)

    assert result is not None


# ==============================================================================
# aput() Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_aput_calls_client(checkpointer_with_mock_client, mock_checkpoint_client):
    """Test aput() calls client correctly."""
    config = {
        "configurable": {
            "thread_id": "thread-1",
            "checkpoint_ns": "",
            "checkpoint_id": "cp-1",
        }
    }
    checkpoint = {
        "v": 1,
        "id": "cp-1",
        "ts": "2024-01-01T00:00:00+00:00",
        "channel_values": {},
        "channel_versions": {},
        "versions_seen": {},
        "pending_sends": [],
    }
    metadata = {"source": "input", "step": -1, "writes": None, "parents": {}}
    new_versions = {}

    result = await checkpointer_with_mock_client.aput(config, checkpoint, metadata, new_versions)

    mock_checkpoint_client.put.assert_called_once()
    call_args = mock_checkpoint_client.put.call_args
    assert call_args[1]["config"]["configurable"]["thread_id"] == "thread-1"
    assert result["configurable"]["thread_id"] == "thread-1"


@pytest.mark.asyncio
async def test_aput_uses_checkpoint_id_from_data(checkpointer_with_mock_client, mock_checkpoint_client):
    """Test aput() uses checkpoint.id when config doesn't have checkpoint_id."""
    mock_checkpoint_client.put.return_value = {
        "config": {
            "configurable": {
                "thread_id": "thread-1",
                "checkpoint_ns": "",
                "checkpoint_id": "id-from-data",
            }
        }
    }

    config = {"configurable": {"thread_id": "thread-1"}}  # No checkpoint_id
    checkpoint = {"v": 1, "id": "id-from-data", "ts": "2024-01-01"}
    metadata = {"source": "input", "step": -1}

    result = await checkpointer_with_mock_client.aput(config, checkpoint, metadata, {})

    assert result["configurable"]["checkpoint_id"] == "id-from-data"


# ==============================================================================
# alist() Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_alist_yields_tuples(checkpointer_with_mock_client, mock_checkpoint_client):
    """Test alist() yields CheckpointTuples from client response."""
    mock_checkpoint_client.list.return_value = [
        {
            "config": {"configurable": {"thread_id": "thread-1", "checkpoint_id": "cp-1"}},
            "checkpoint": {"v": 1, "id": "cp-1", "ts": "2024", "channel_values": {}},
            "metadata": {"source": "input", "step": -1},
        },
        {
            "config": {"configurable": {"thread_id": "thread-1", "checkpoint_id": "cp-2"}},
            "checkpoint": {"v": 1, "id": "cp-2", "ts": "2024", "channel_values": {}},
            "metadata": {"source": "loop", "step": 0},
        },
    ]

    config = {"configurable": {"thread_id": "thread-1"}}
    results = []
    async for item in checkpointer_with_mock_client.alist(config):
        results.append(item)

    assert len(results) == 2


@pytest.mark.asyncio
async def test_alist_empty(checkpointer_with_mock_client, mock_checkpoint_client):
    """Test alist() handles empty results."""
    mock_checkpoint_client.list.return_value = []

    config = {"configurable": {"thread_id": "nonexistent"}}
    results = []
    async for item in checkpointer_with_mock_client.alist(config):
        results.append(item)

    assert results == []


@pytest.mark.asyncio
async def test_alist_passes_parameters(checkpointer_with_mock_client, mock_checkpoint_client):
    """Test alist() passes filter parameters to client."""
    mock_checkpoint_client.list.return_value = []

    config = {"configurable": {"thread_id": "thread-1", "checkpoint_ns": "ns-1"}}
    before_config = {"configurable": {"checkpoint_id": "cp-5"}}

    async for _ in checkpointer_with_mock_client.alist(config, before=before_config, limit=10):
        pass

    mock_checkpoint_client.list.assert_called_once_with(
        thread_id="thread-1",
        checkpoint_ns="ns-1",
        before="cp-5",
        limit=10,
    )


# ==============================================================================
# adelete_thread() Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_adelete_thread_calls_client(checkpointer_with_mock_client, mock_checkpoint_client):
    """Test adelete_thread() calls client correctly."""
    await checkpointer_with_mock_client.adelete_thread("thread-1")

    mock_checkpoint_client.delete_thread.assert_called_once_with("thread-1")


# ==============================================================================
# Sync Method Wrapper Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_sync_get_tuple_wrapper(checkpointer_with_mock_client, mock_checkpoint_client):
    """Test synchronous get_tuple() wrapper works."""
    # This test verifies the sync wrapper exists and can be called
    # In actual async context, we use aget_tuple instead
    mock_checkpoint_client.get_tuple.return_value = None

    # get_tuple should work (it's a sync wrapper around aget_tuple)
    # We can't easily test this in an async test, but we verify the method exists
    assert hasattr(checkpointer_with_mock_client, 'get_tuple')
    assert callable(checkpointer_with_mock_client.get_tuple)


@pytest.mark.asyncio
async def test_sync_put_wrapper_exists(checkpointer_with_mock_client):
    """Test synchronous put() wrapper exists."""
    assert hasattr(checkpointer_with_mock_client, 'put')
    assert callable(checkpointer_with_mock_client.put)


@pytest.mark.asyncio
async def test_sync_list_wrapper_exists(checkpointer_with_mock_client):
    """Test synchronous list() wrapper exists."""
    assert hasattr(checkpointer_with_mock_client, 'list')
    assert callable(checkpointer_with_mock_client.list)


# ==============================================================================
# Data Conversion Helper Tests
# ==============================================================================


def test_checkpoint_to_api_conversion(mock_app):
    """Test _checkpoint_to_api converts checkpoint correctly."""
    saver = HTTPCheckpointSaver(app=mock_app)

    checkpoint_dict = {
        "v": 1,
        "id": "cp-1",
        "ts": "2024-01-01T00:00:00+00:00",
        "channel_values": {"messages": ["hello"]},
        "channel_versions": {"messages": 1},
        "versions_seen": {"node1": {"messages": 1}},
        "pending_sends": [],
    }

    result = saver._checkpoint_to_api(checkpoint_dict)

    assert result["v"] == 1
    assert result["id"] == "cp-1"
    assert result["channel_values"] == {"messages": ["hello"]}
    assert result["channel_versions"] == {"messages": 1}
    assert result["versions_seen"] == {"node1": {"messages": 1}}


def test_checkpoint_to_api_handles_missing_fields(mock_app):
    """Test _checkpoint_to_api handles missing optional fields."""
    saver = HTTPCheckpointSaver(app=mock_app)

    checkpoint_dict = {"v": 1, "id": "cp-1", "ts": "2024"}

    result = saver._checkpoint_to_api(checkpoint_dict)

    assert result["v"] == 1
    assert result["id"] == "cp-1"
    assert result["channel_values"] == {}
    assert result["pending_sends"] == []


def test_metadata_to_api_conversion(mock_app):
    """Test _metadata_to_api converts metadata correctly."""
    saver = HTTPCheckpointSaver(app=mock_app)

    metadata_dict = {
        "source": "loop",
        "step": 5,
        "writes": {"key": "value"},
        "parents": {"": "parent-cp"},
    }

    result = saver._metadata_to_api(metadata_dict)

    assert result["source"] == "loop"
    assert result["step"] == 5
    assert result["writes"] == {"key": "value"}
    assert result["parents"] == {"": "parent-cp"}


def test_metadata_to_api_handles_defaults(mock_app):
    """Test _metadata_to_api handles missing fields with defaults."""
    saver = HTTPCheckpointSaver(app=mock_app)

    metadata_dict = {}

    result = saver._metadata_to_api(metadata_dict)

    assert result["source"] == "input"
    assert result["step"] == -1
    assert result["writes"] is None
    assert result["parents"] == {}


def test_response_to_tuple_conversion(mock_app):
    """Test _response_to_tuple converts API response correctly."""
    saver = HTTPCheckpointSaver(app=mock_app)

    response = {
        "config": {
            "configurable": {
                "thread_id": "thread-1",
                "checkpoint_ns": "",
                "checkpoint_id": "cp-1",
            }
        },
        "checkpoint": {
            "v": 1,
            "id": "cp-1",
            "ts": "2024-01-01T00:00:00+00:00",
            "channel_values": {},
            "channel_versions": {},
            "versions_seen": {},
            "pending_sends": [],
        },
        "metadata": {
            "source": "input",
            "step": -1,
            "writes": None,
            "parents": {},
        },
        "parent_config": None,
        "pending_writes": None,
    }

    result = saver._response_to_tuple(response)

    # Result should be a tuple or CheckpointTuple-like structure
    assert result is not None


def test_response_to_tuple_none_returns_none(mock_app):
    """Test _response_to_tuple returns None for empty response."""
    saver = HTTPCheckpointSaver(app=mock_app)

    result = saver._response_to_tuple(None)

    assert result is None


def test_response_to_tuple_empty_dict_returns_none(mock_app):
    """Test _response_to_tuple returns None for empty dict."""
    saver = HTTPCheckpointSaver(app=mock_app)

    result = saver._response_to_tuple({})

    assert result is None


# ==============================================================================
# Config Helper Tests
# ==============================================================================


def test_get_thread_id():
    """Test _get_thread_id extracts thread_id correctly."""
    config = {"configurable": {"thread_id": "my-thread"}}

    result = HTTPCheckpointSaver._get_thread_id(config)

    assert result == "my-thread"


def test_get_thread_id_missing_raises():
    """Test _get_thread_id raises when thread_id missing."""
    config = {"configurable": {}}

    with pytest.raises(ValueError) as exc_info:
        HTTPCheckpointSaver._get_thread_id(config)

    assert "thread_id" in str(exc_info.value)


def test_get_checkpoint_ns_default():
    """Test _get_checkpoint_ns returns empty string by default."""
    config = {"configurable": {"thread_id": "test"}}

    result = HTTPCheckpointSaver._get_checkpoint_ns(config)

    assert result == ""


def test_get_checkpoint_ns_with_value():
    """Test _get_checkpoint_ns returns provided value."""
    config = {"configurable": {"thread_id": "test", "checkpoint_ns": "my-ns"}}

    result = HTTPCheckpointSaver._get_checkpoint_ns(config)

    assert result == "my-ns"


def test_get_checkpoint_id_none():
    """Test _get_checkpoint_id returns None when not provided."""
    config = {"configurable": {"thread_id": "test"}}

    result = HTTPCheckpointSaver._get_checkpoint_id(config)

    assert result is None


def test_get_checkpoint_id_with_value():
    """Test _get_checkpoint_id returns provided value."""
    config = {"configurable": {"thread_id": "test", "checkpoint_id": "cp-123"}}

    result = HTTPCheckpointSaver._get_checkpoint_id(config)

    assert result == "cp-123"


# ==============================================================================
# Close Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_close(checkpointer_with_mock_client, mock_checkpoint_client):
    """Test close() closes the client session."""
    await checkpointer_with_mock_client.close()

    mock_checkpoint_client.close.assert_called_once()

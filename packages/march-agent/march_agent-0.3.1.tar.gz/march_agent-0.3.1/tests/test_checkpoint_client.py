"""Unit tests for CheckpointClient HTTP client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from march_agent.checkpoint_client import CheckpointClient
from march_agent.exceptions import APIException


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def checkpoint_client():
    """Create CheckpointClient instance."""
    return CheckpointClient(base_url="http://test-gateway/s/conversation-store")


@pytest.fixture
def mock_response():
    """Create a mock aiohttp response."""
    response = MagicMock()
    response.status = 200
    response.json = AsyncMock(return_value={"config": {"configurable": {"thread_id": "test"}}})
    response.text = AsyncMock(return_value="OK")
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=None)
    return response


# ==============================================================================
# Initialization Tests
# ==============================================================================


def test_init_strips_trailing_slash():
    """Test that base_url trailing slash is stripped."""
    client = CheckpointClient(base_url="http://example.com/api/")
    assert client.base_url == "http://example.com/api"


def test_init_no_trailing_slash():
    """Test that base_url without trailing slash is preserved."""
    client = CheckpointClient(base_url="http://example.com/api")
    assert client.base_url == "http://example.com/api"


# ==============================================================================
# Session Management Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_get_session_creates_session(checkpoint_client):
    """Test that _get_session creates a new session."""
    session = await checkpoint_client._get_session()

    try:
        assert session is not None
        assert isinstance(session, aiohttp.ClientSession)
    finally:
        await checkpoint_client.close()


@pytest.mark.asyncio
async def test_get_session_reuses_session(checkpoint_client):
    """Test that _get_session reuses existing session."""
    session1 = await checkpoint_client._get_session()
    session2 = await checkpoint_client._get_session()

    try:
        assert session1 is session2
    finally:
        await checkpoint_client.close()


@pytest.mark.asyncio
async def test_close_session(checkpoint_client):
    """Test that close() properly closes the session."""
    # Create session
    await checkpoint_client._get_session()

    # Close it
    await checkpoint_client.close()

    # Verify closed
    assert checkpoint_client._session is None or checkpoint_client._session.closed


# ==============================================================================
# put() Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_put_success(checkpoint_client, mock_response):
    """Test put() sends correct request and returns response."""
    config = {"configurable": {"thread_id": "thread-1", "checkpoint_ns": "", "checkpoint_id": "cp-1"}}
    checkpoint_data = {"v": 1, "id": "cp-1", "ts": "2024-01-01", "channel_values": {}}
    metadata = {"source": "input", "step": -1, "writes": None, "parents": {}}

    with patch.object(checkpoint_client, '_get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_session.put = MagicMock(return_value=mock_response)
        mock_get_session.return_value = mock_session

        result = await checkpoint_client.put(config, checkpoint_data, metadata)

        # Verify request was made correctly
        mock_session.put.assert_called_once()
        call_args = mock_session.put.call_args
        assert call_args[0][0] == "http://test-gateway/s/conversation-store/checkpoints/"
        assert "config" in call_args[1]["json"]
        assert "checkpoint" in call_args[1]["json"]
        assert "metadata" in call_args[1]["json"]

        # Verify response
        assert result == {"config": {"configurable": {"thread_id": "test"}}}


@pytest.mark.asyncio
async def test_put_http_error(checkpoint_client):
    """Test put() raises APIException on HTTP error."""
    mock_response = MagicMock()
    mock_response.status = 422
    mock_response.text = AsyncMock(return_value="Validation error")
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    with patch.object(checkpoint_client, '_get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_session.put = MagicMock(return_value=mock_response)
        mock_get_session.return_value = mock_session

        with pytest.raises(APIException) as exc_info:
            await checkpoint_client.put(
                {"configurable": {}},
                {"v": 1, "id": "cp-1", "ts": "2024"},
                {"source": "input", "step": -1},
            )

        assert "422" in str(exc_info.value)


@pytest.mark.asyncio
async def test_put_client_error(checkpoint_client):
    """Test put() raises APIException on client error."""
    with patch.object(checkpoint_client, '_get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_session.put = MagicMock(side_effect=aiohttp.ClientError("Connection failed"))
        mock_get_session.return_value = mock_session

        with pytest.raises(APIException) as exc_info:
            await checkpoint_client.put(
                {"configurable": {}},
                {"v": 1, "id": "cp-1", "ts": "2024"},
                {"source": "input", "step": -1},
            )

        assert "Connection failed" in str(exc_info.value)


# ==============================================================================
# get_tuple() Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_get_tuple_found(checkpoint_client):
    """Test get_tuple() returns checkpoint when found."""
    expected_response = {
        "config": {"configurable": {"thread_id": "thread-1", "checkpoint_id": "cp-1"}},
        "checkpoint": {"v": 1, "channel_values": {"messages": []}},
        "metadata": {"source": "input", "step": -1},
    }

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=expected_response)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    with patch.object(checkpoint_client, '_get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_get_session.return_value = mock_session

        result = await checkpoint_client.get_tuple("thread-1", "", "cp-1")

        # Verify request
        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        assert "thread-1" in call_args[0][0]
        assert call_args[1]["params"]["checkpoint_id"] == "cp-1"

        # Verify response
        assert result == expected_response


@pytest.mark.asyncio
async def test_get_tuple_not_found_returns_none(checkpoint_client):
    """Test get_tuple() returns None when checkpoint not found."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=None)  # API returns null for not found
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    with patch.object(checkpoint_client, '_get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_get_session.return_value = mock_session

        result = await checkpoint_client.get_tuple("nonexistent", "", "cp-1")

        assert result is None


@pytest.mark.asyncio
async def test_get_tuple_404_returns_none(checkpoint_client):
    """Test get_tuple() returns None on 404."""
    mock_response = MagicMock()
    mock_response.status = 404
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    with patch.object(checkpoint_client, '_get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_get_session.return_value = mock_session

        result = await checkpoint_client.get_tuple("thread-1", "", "cp-1")

        assert result is None


@pytest.mark.asyncio
async def test_get_tuple_without_checkpoint_id(checkpoint_client):
    """Test get_tuple() request without checkpoint_id gets latest."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"config": {}})
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    with patch.object(checkpoint_client, '_get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_get_session.return_value = mock_session

        await checkpoint_client.get_tuple("thread-1", "ns-1")

        # Verify checkpoint_id not in params
        call_args = mock_session.get.call_args
        assert "checkpoint_id" not in call_args[1]["params"]
        assert call_args[1]["params"]["checkpoint_ns"] == "ns-1"


# ==============================================================================
# list() Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_list_success(checkpoint_client):
    """Test list() returns list of checkpoints."""
    expected_response = [
        {"config": {"configurable": {"thread_id": "thread-1"}}, "checkpoint": {}},
        {"config": {"configurable": {"thread_id": "thread-1"}}, "checkpoint": {}},
    ]

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=expected_response)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    with patch.object(checkpoint_client, '_get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_get_session.return_value = mock_session

        result = await checkpoint_client.list(thread_id="thread-1")

        assert result == expected_response
        assert len(result) == 2


@pytest.mark.asyncio
async def test_list_with_params(checkpoint_client):
    """Test list() passes query parameters correctly."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=[])
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    with patch.object(checkpoint_client, '_get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_get_session.return_value = mock_session

        await checkpoint_client.list(
            thread_id="thread-1",
            checkpoint_ns="ns-1",
            before="cp-3",
            limit=10,
        )

        # Verify params
        call_args = mock_session.get.call_args
        params = call_args[1]["params"]
        assert params["thread_id"] == "thread-1"
        assert params["checkpoint_ns"] == "ns-1"
        assert params["before"] == "cp-3"
        assert params["limit"] == 10


@pytest.mark.asyncio
async def test_list_empty(checkpoint_client):
    """Test list() returns empty list when no checkpoints."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=[])
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    with patch.object(checkpoint_client, '_get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_get_session.return_value = mock_session

        result = await checkpoint_client.list()

        assert result == []


# ==============================================================================
# delete_thread() Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_delete_thread_success(checkpoint_client):
    """Test delete_thread() sends correct request."""
    expected_response = {"thread_id": "thread-1", "deleted": 3}

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=expected_response)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    with patch.object(checkpoint_client, '_get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_session.delete = MagicMock(return_value=mock_response)
        mock_get_session.return_value = mock_session

        result = await checkpoint_client.delete_thread("thread-1")

        # Verify request
        mock_session.delete.assert_called_once()
        call_args = mock_session.delete.call_args
        assert "thread-1" in call_args[0][0]

        # Verify response
        assert result == expected_response
        assert result["deleted"] == 3


@pytest.mark.asyncio
async def test_delete_thread_http_error(checkpoint_client):
    """Test delete_thread() raises APIException on HTTP error."""
    mock_response = MagicMock()
    mock_response.status = 500
    mock_response.text = AsyncMock(return_value="Internal server error")
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    with patch.object(checkpoint_client, '_get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_session.delete = MagicMock(return_value=mock_response)
        mock_get_session.return_value = mock_session

        with pytest.raises(APIException) as exc_info:
            await checkpoint_client.delete_thread("thread-1")

        assert "500" in str(exc_info.value)

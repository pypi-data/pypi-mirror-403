"""Unit tests for AgentStateClient HTTP client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from march_agent.agent_state_client import AgentStateClient
from march_agent.exceptions import APIException


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def agent_state_client():
    """Create AgentStateClient instance."""
    return AgentStateClient(base_url="http://test-gateway/s/conversation-store")


@pytest.fixture
def mock_response():
    """Create a mock aiohttp response."""
    response = MagicMock()
    response.status = 200
    response.json = AsyncMock(return_value={
        "conversation_id": "conv-1",
        "namespace": "pydantic_ai",
        "state": {"messages": []},
    })
    response.text = AsyncMock(return_value="OK")
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=None)
    return response


# ==============================================================================
# Initialization Tests
# ==============================================================================


def test_init_strips_trailing_slash():
    """Test that base_url trailing slash is stripped."""
    client = AgentStateClient(base_url="http://example.com/api/")
    assert client.base_url == "http://example.com/api"


def test_init_no_trailing_slash():
    """Test that base_url without trailing slash is preserved."""
    client = AgentStateClient(base_url="http://example.com/api")
    assert client.base_url == "http://example.com/api"


# ==============================================================================
# Session Management Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_get_session_creates_session(agent_state_client):
    """Test that _get_session creates a new session."""
    session = await agent_state_client._get_session()

    try:
        assert session is not None
        assert isinstance(session, aiohttp.ClientSession)
    finally:
        await agent_state_client.close()


@pytest.mark.asyncio
async def test_get_session_reuses_session(agent_state_client):
    """Test that _get_session reuses existing session."""
    session1 = await agent_state_client._get_session()
    session2 = await agent_state_client._get_session()

    try:
        assert session1 is session2
    finally:
        await agent_state_client.close()


@pytest.mark.asyncio
async def test_close_session(agent_state_client):
    """Test that close() properly closes the session."""
    # Create session
    await agent_state_client._get_session()

    # Close it
    await agent_state_client.close()

    # Verify closed
    assert agent_state_client._session is None or agent_state_client._session.closed


# ==============================================================================
# put() Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_put_success(agent_state_client, mock_response):
    """Test put() sends correct request and returns response."""
    mock_response.json = AsyncMock(return_value={
        "conversation_id": "conv-1",
        "namespace": "pydantic_ai",
        "created": True,
    })

    with patch.object(agent_state_client, '_get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_session.put = MagicMock(return_value=mock_response)
        mock_get_session.return_value = mock_session

        result = await agent_state_client.put(
            "conv-1",
            "pydantic_ai",
            {"messages": [{"role": "user", "content": "test"}]},
        )

        # Verify request was made correctly
        mock_session.put.assert_called_once()
        call_args = mock_session.put.call_args
        assert call_args[0][0] == "http://test-gateway/s/conversation-store/agent-state/conv-1"
        assert "namespace" in call_args[1]["json"]
        assert "state" in call_args[1]["json"]
        assert call_args[1]["json"]["namespace"] == "pydantic_ai"

        # Verify response
        assert result["conversation_id"] == "conv-1"
        assert result["created"] is True


@pytest.mark.asyncio
async def test_put_http_error(agent_state_client):
    """Test put() raises APIException on HTTP error."""
    mock_response = MagicMock()
    mock_response.status = 422
    mock_response.text = AsyncMock(return_value="Validation error")
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    with patch.object(agent_state_client, '_get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_session.put = MagicMock(return_value=mock_response)
        mock_get_session.return_value = mock_session

        with pytest.raises(APIException) as exc_info:
            await agent_state_client.put(
                "conv-1",
                "pydantic_ai",
                {"messages": []},
            )

        assert "422" in str(exc_info.value)


@pytest.mark.asyncio
async def test_put_client_error(agent_state_client):
    """Test put() raises APIException on client error."""
    with patch.object(agent_state_client, '_get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_session.put = MagicMock(side_effect=aiohttp.ClientError("Connection failed"))
        mock_get_session.return_value = mock_session

        with pytest.raises(APIException) as exc_info:
            await agent_state_client.put(
                "conv-1",
                "pydantic_ai",
                {"messages": []},
            )

        assert "Connection failed" in str(exc_info.value)


# ==============================================================================
# get() Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_get_found(agent_state_client):
    """Test get() returns agent state when found."""
    expected_response = {
        "conversation_id": "conv-1",
        "namespace": "pydantic_ai",
        "state": {"messages": [{"role": "user", "content": "test"}]},
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=expected_response)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    with patch.object(agent_state_client, '_get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_get_session.return_value = mock_session

        result = await agent_state_client.get("conv-1", "pydantic_ai")

        # Verify request
        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        assert "conv-1" in call_args[0][0]
        assert call_args[1]["params"]["namespace"] == "pydantic_ai"

        # Verify response
        assert result == expected_response


@pytest.mark.asyncio
async def test_get_not_found_returns_none(agent_state_client):
    """Test get() returns None when agent state not found."""
    mock_response = MagicMock()
    mock_response.status = 404
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    with patch.object(agent_state_client, '_get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_get_session.return_value = mock_session

        result = await agent_state_client.get("nonexistent", "pydantic_ai")

        assert result is None


@pytest.mark.asyncio
async def test_get_http_error(agent_state_client):
    """Test get() raises APIException on HTTP error (non-404)."""
    mock_response = MagicMock()
    mock_response.status = 500
    mock_response.text = AsyncMock(return_value="Internal server error")
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    with patch.object(agent_state_client, '_get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_get_session.return_value = mock_session

        with pytest.raises(APIException) as exc_info:
            await agent_state_client.get("conv-1", "pydantic_ai")

        assert "500" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_client_error(agent_state_client):
    """Test get() raises APIException on client error."""
    with patch.object(agent_state_client, '_get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=aiohttp.ClientError("Connection refused"))
        mock_get_session.return_value = mock_session

        with pytest.raises(APIException) as exc_info:
            await agent_state_client.get("conv-1", "pydantic_ai")

        assert "Connection refused" in str(exc_info.value)


# ==============================================================================
# delete() Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_delete_with_namespace(agent_state_client):
    """Test delete() with namespace sends correct request."""
    expected_response = {
        "conversation_id": "conv-1",
        "namespace": "pydantic_ai",
        "deleted": 1,
    }

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=expected_response)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    with patch.object(agent_state_client, '_get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_session.delete = MagicMock(return_value=mock_response)
        mock_get_session.return_value = mock_session

        result = await agent_state_client.delete("conv-1", "pydantic_ai")

        # Verify request
        mock_session.delete.assert_called_once()
        call_args = mock_session.delete.call_args
        assert "conv-1" in call_args[0][0]
        assert call_args[1]["params"]["namespace"] == "pydantic_ai"

        # Verify response
        assert result == expected_response
        assert result["deleted"] == 1


@pytest.mark.asyncio
async def test_delete_without_namespace(agent_state_client):
    """Test delete() without namespace deletes all."""
    expected_response = {
        "conversation_id": "conv-1",
        "namespace": None,
        "deleted": 3,
    }

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=expected_response)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    with patch.object(agent_state_client, '_get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_session.delete = MagicMock(return_value=mock_response)
        mock_get_session.return_value = mock_session

        result = await agent_state_client.delete("conv-1")

        # Verify request - no namespace param
        mock_session.delete.assert_called_once()
        call_args = mock_session.delete.call_args
        assert call_args[1]["params"] == {}

        # Verify response
        assert result["deleted"] == 3


@pytest.mark.asyncio
async def test_delete_http_error(agent_state_client):
    """Test delete() raises APIException on HTTP error."""
    mock_response = MagicMock()
    mock_response.status = 500
    mock_response.text = AsyncMock(return_value="Internal server error")
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    with patch.object(agent_state_client, '_get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_session.delete = MagicMock(return_value=mock_response)
        mock_get_session.return_value = mock_session

        with pytest.raises(APIException) as exc_info:
            await agent_state_client.delete("conv-1", "pydantic_ai")

        assert "500" in str(exc_info.value)


@pytest.mark.asyncio
async def test_delete_client_error(agent_state_client):
    """Test delete() raises APIException on client error."""
    with patch.object(agent_state_client, '_get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_session.delete = MagicMock(side_effect=aiohttp.ClientError("Timeout"))
        mock_get_session.return_value = mock_session

        with pytest.raises(APIException) as exc_info:
            await agent_state_client.delete("conv-1")

        assert "Timeout" in str(exc_info.value)

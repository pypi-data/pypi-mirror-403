"""Comprehensive tests for Memory class and MemoryClient."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from march_agent.memory import Memory
from march_agent.memory_client import MemoryClient, MemorySearchResult, MemoryMessage, UserSummary
from march_agent.exceptions import APIException
import aiohttp


# Helper classes for async context manager mocking
class MockResponse:
    def __init__(self, status=200, json_data=None, text_data=""):
        self.status = status
        self._json_data = json_data or {}
        self.text_data = text_data

    async def json(self):
        return self._json_data

    async def text(self):
        return self.text_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class MockSession:
    def __init__(self, response):
        self.response = response

    def get(self, url):
        return self.response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class TestMemoryClient:
    """Test MemoryClient low-level HTTP client."""

    @pytest.mark.asyncio
    async def test_memory_client_initialization(self):
        """Test MemoryClient initialization."""
        client = MemoryClient(base_url="http://memory:8080/api")
        assert client.base_url == "http://memory:8080/api"
        assert client._session is None
        await client.close()

    @pytest.mark.asyncio
    async def test_memory_client_base_url_normalization(self):
        """Test that trailing slashes are removed from base_url."""
        client = MemoryClient(base_url="http://memory:8080/api/")
        assert client.base_url == "http://memory:8080/api"
        await client.close()

    @pytest.mark.asyncio
    async def test_get_session_creates_session(self):
        """Test that _get_session creates aiohttp session."""
        client = MemoryClient(base_url="http://memory:8080")
        session = await client._get_session()
        assert isinstance(session, aiohttp.ClientSession)
        assert not session.closed
        await client.close()

    @pytest.mark.asyncio
    async def test_get_session_reuses_existing_session(self):
        """Test that _get_session reuses existing session."""
        client = MemoryClient(base_url="http://memory:8080")
        session1 = await client._get_session()
        session2 = await client._get_session()
        assert session1 is session2
        await client.close()

    @pytest.mark.asyncio
    async def test_close_session(self):
        """Test closing the client session."""
        client = MemoryClient(base_url="http://memory:8080")
        session = await client._get_session()
        await client.close()
        assert session.closed

    @pytest.mark.asyncio
    async def test_close_without_session(self):
        """Test closing when no session exists."""
        client = MemoryClient(base_url="http://memory:8080")
        await client.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_search_basic(self):
        """Test basic memory search."""
        client = MemoryClient(base_url="http://memory:8080")

        mock_response_data = {
            "results": [
                {
                    "message": {
                        "id": "msg-1",
                        "role": "user",
                        "content": "I love pizza",
                        "user_id": "user-123"
                    },
                    "score": 0.95,
                    "context": []
                }
            ]
        }

        mock_response = MockResponse(status=200, json_data=mock_response_data)
        mock_session = MockSession(mock_response)

        with patch.object(client, '_get_session', return_value=mock_session):
            results = await client.search(query="pizza", user_id="user-123")

            assert len(results) == 1
            assert isinstance(results[0], MemorySearchResult)
            assert results[0].message.content == "I love pizza"
            assert results[0].score == 0.95

        await client.close()

    @pytest.mark.asyncio
    async def test_search_with_all_parameters(self):
        """Test search with all parameters."""
        client = MemoryClient(base_url="http://memory:8080")

        mock_response_data = {"results": []}

        with patch.object(client, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock()
            mock_get_session.return_value = mock_session

            results = await client.search(
                query="test",
                user_id="user-1",
                conversation_id="conv-1",
                tenant_id="tenant-1",
                limit=20,
                min_similarity=80,
                context_messages=5
            )

            # Verify URL construction with all params
            call_args = mock_session.get.call_args
            url = call_args[0][0]
            assert "q=test" in url
            assert "user_id=user-1" in url
            assert "conversation_id=conv-1" in url
            assert "tenant_id=tenant-1" in url
            assert "limit=20" in url
            assert "min_similarity=80" in url
            assert "context_messages=5" in url

        await client.close()

    @pytest.mark.asyncio
    async def test_search_with_context_messages(self):
        """Test search returns context messages."""
        client = MemoryClient(base_url="http://memory:8080")

        mock_response_data = {
            "results": [
                {
                    "message": {
                        "id": "msg-2",
                        "role": "assistant",
                        "content": "I can help with that",
                        "user_id": "user-123"
                    },
                    "score": 0.88,
                    "context": [
                        {
                            "id": "msg-1",
                            "role": "user",
                            "content": "Previous message",
                            "user_id": "user-123"
                        }
                    ]
                }
            ]
        }

        with patch.object(client, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock()
            mock_get_session.return_value = mock_session

            results = await client.search(query="help", context_messages=1)

            assert len(results) == 1
            assert len(results[0].context) == 1
            assert results[0].context[0].content == "Previous message"

        await client.close()

    @pytest.mark.asyncio
    async def test_search_error_response(self):
        """Test search handles error responses."""
        client = MemoryClient(base_url="http://memory:8080")

        with patch.object(client, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Internal Server Error")
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock()
            mock_get_session.return_value = mock_session

            with pytest.raises(APIException, match="Memory search failed: 500"):
                await client.search(query="test")

        await client.close()

    @pytest.mark.asyncio
    async def test_search_network_error(self):
        """Test search handles network errors."""
        client = MemoryClient(base_url="http://memory:8080")

        with patch.object(client, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(side_effect=aiohttp.ClientError("Connection failed"))
            mock_get_session.return_value = mock_session

            with pytest.raises(APIException, match="Memory search failed"):
                await client.search(query="test")

        await client.close()

    @pytest.mark.asyncio
    async def test_get_user_summary_success(self):
        """Test getting user summary."""
        client = MemoryClient(base_url="http://memory:8080")

        mock_response_data = {
            "has_summary": True,
            "summary": {
                "text": "User likes pizza and coding",
                "last_updated": "2024-01-15T10:00:00Z",
                "message_count": 50,
                "version": 2
            }
        }

        with patch.object(client, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock()
            mock_get_session.return_value = mock_session

            summary = await client.get_user_summary(user_id="user-123")

            assert isinstance(summary, UserSummary)
            assert summary.text == "User likes pizza and coding"
            assert summary.message_count == 50
            assert summary.version == 2

        await client.close()

    @pytest.mark.asyncio
    async def test_get_user_summary_not_found(self):
        """Test getting summary when user not found."""
        client = MemoryClient(base_url="http://memory:8080")

        with patch.object(client, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock()
            mock_get_session.return_value = mock_session

            summary = await client.get_user_summary(user_id="unknown")

            assert summary is None

        await client.close()

    @pytest.mark.asyncio
    async def test_get_user_summary_no_summary(self):
        """Test getting summary when has_summary is False."""
        client = MemoryClient(base_url="http://memory:8080")

        mock_response_data = {
            "has_summary": False,
            "summary": None
        }

        with patch.object(client, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock()
            mock_get_session.return_value = mock_session

            summary = await client.get_user_summary(user_id="user-123")

            assert summary is None

        await client.close()

    @pytest.mark.asyncio
    async def test_get_user_summary_error_response(self):
        """Test summary handles error responses."""
        client = MemoryClient(base_url="http://memory:8080")

        with patch.object(client, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Server error")
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock()
            mock_get_session.return_value = mock_session

            with pytest.raises(APIException, match="Summary fetch failed: 500"):
                await client.get_user_summary(user_id="user-123")

        await client.close()


class TestMemoryMessage:
    """Test MemoryMessage dataclass."""

    def test_memory_message_from_dict_complete(self):
        """Test creating MemoryMessage from complete dict."""
        data = {
            "id": "msg-1",
            "role": "user",
            "content": "Hello",
            "tenant_id": "tenant-1",
            "user_id": "user-1",
            "conversation_id": "conv-1",
            "metadata": {"key": "value"},
            "timestamp": "2024-01-15T10:00:00Z",
            "sequence_number": 42
        }

        msg = MemoryMessage.from_dict(data)

        assert msg.id == "msg-1"
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.tenant_id == "tenant-1"
        assert msg.user_id == "user-1"
        assert msg.conversation_id == "conv-1"
        assert msg.metadata == {"key": "value"}
        assert msg.timestamp == "2024-01-15T10:00:00Z"
        assert msg.sequence_number == 42

    def test_memory_message_from_dict_minimal(self):
        """Test creating MemoryMessage with minimal fields."""
        data = {
            "id": "msg-1",
            "role": "assistant",
            "content": "Response"
        }

        msg = MemoryMessage.from_dict(data)

        assert msg.id == "msg-1"
        assert msg.role == "assistant"
        assert msg.content == "Response"
        assert msg.tenant_id is None
        assert msg.user_id is None
        assert msg.conversation_id is None
        assert msg.metadata is None
        assert msg.timestamp is None
        assert msg.sequence_number is None

    def test_memory_message_from_dict_empty(self):
        """Test creating MemoryMessage from empty dict."""
        data = {}

        msg = MemoryMessage.from_dict(data)

        assert msg.id == ""
        assert msg.role == ""
        assert msg.content == ""


class TestMemory:
    """Test Memory wrapper class."""

    @pytest.mark.asyncio
    async def test_memory_initialization(self):
        """Test Memory initialization."""
        client = MemoryClient(base_url="http://memory:8080")
        memory = Memory(user_id="user-1", conversation_id="conv-1", client=client)

        assert memory.user_id == "user-1"
        assert memory.conversation_id == "conv-1"
        assert memory._client is client

        await client.close()

    @pytest.mark.asyncio
    async def test_query_about_user_basic(self):
        """Test querying user memory."""
        client = MemoryClient(base_url="http://memory:8080")
        memory = Memory(user_id="user-123", conversation_id="conv-1", client=client)

        mock_result = MemorySearchResult(
            message=MemoryMessage(
                id="msg-1",
                role="user",
                content="I love pizza",
                user_id="user-123"
            ),
            score=0.95,
            context=[]
        )

        with patch.object(client, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [mock_result]

            results = await memory.query_about_user(query="pizza")

            assert len(results) == 1
            assert results[0].message.content == "I love pizza"

            # Verify correct parameters passed
            mock_search.assert_called_once_with(
                query="pizza",
                user_id="user-123",
                limit=10,
                min_similarity=70,
                context_messages=0
            )

        await client.close()

    @pytest.mark.asyncio
    async def test_query_about_user_with_custom_parameters(self):
        """Test querying user memory with custom parameters."""
        client = MemoryClient(base_url="http://memory:8080")
        memory = Memory(user_id="user-123", conversation_id="conv-1", client=client)

        with patch.object(client, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []

            await memory.query_about_user(
                query="preferences",
                limit=20,
                threshold=85,
                context_messages=3
            )

            # Verify parameters including user_id scope
            mock_search.assert_called_once_with(
                query="preferences",
                user_id="user-123",
                limit=20,
                min_similarity=85,
                context_messages=3
            )

        await client.close()

    @pytest.mark.asyncio
    async def test_query_about_conversation_basic(self):
        """Test querying conversation memory."""
        client = MemoryClient(base_url="http://memory:8080")
        memory = Memory(user_id="user-123", conversation_id="conv-456", client=client)

        mock_result = MemorySearchResult(
            message=MemoryMessage(
                id="msg-1",
                role="assistant",
                content="We discussed the project timeline",
                conversation_id="conv-456"
            ),
            score=0.92,
            context=[]
        )

        with patch.object(client, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [mock_result]

            results = await memory.query_about_conversation(query="timeline")

            assert len(results) == 1
            assert results[0].message.content == "We discussed the project timeline"

            # Verify conversation_id is used instead of user_id
            mock_search.assert_called_once_with(
                query="timeline",
                conversation_id="conv-456",
                limit=10,
                min_similarity=70,
                context_messages=0
            )

        await client.close()

    @pytest.mark.asyncio
    async def test_query_about_conversation_with_custom_parameters(self):
        """Test querying conversation memory with custom parameters."""
        client = MemoryClient(base_url="http://memory:8080")
        memory = Memory(user_id="user-123", conversation_id="conv-456", client=client)

        with patch.object(client, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []

            await memory.query_about_conversation(
                query="decisions",
                limit=15,
                threshold=80,
                context_messages=2
            )

            # Verify parameters
            mock_search.assert_called_once_with(
                query="decisions",
                conversation_id="conv-456",
                limit=15,
                min_similarity=80,
                context_messages=2
            )

        await client.close()

    @pytest.mark.asyncio
    async def test_get_user_summary(self):
        """Test getting user summary through Memory."""
        client = MemoryClient(base_url="http://memory:8080")
        memory = Memory(user_id="user-123", conversation_id="conv-1", client=client)

        mock_summary = UserSummary(
            text="User prefers Python and TypeScript",
            last_updated="2024-01-15T10:00:00Z",
            message_count=100,
            version=3
        )

        with patch.object(client, 'get_user_summary', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_summary

            summary = await memory.get_user_summary()

            assert summary is not None
            assert summary.text == "User prefers Python and TypeScript"
            assert summary.message_count == 100

            # Verify correct user_id passed
            mock_get.assert_called_once_with("user-123")

        await client.close()

    @pytest.mark.asyncio
    async def test_get_user_summary_none(self):
        """Test getting user summary when none exists."""
        client = MemoryClient(base_url="http://memory:8080")
        memory = Memory(user_id="user-123", conversation_id="conv-1", client=client)

        with patch.object(client, 'get_user_summary', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            summary = await memory.get_user_summary()

            assert summary is None

        await client.close()

    @pytest.mark.asyncio
    async def test_memory_preserves_user_and_conversation_ids(self):
        """Test that Memory correctly scopes queries to user/conversation."""
        client = MemoryClient(base_url="http://memory:8080")
        memory = Memory(user_id="user-A", conversation_id="conv-B", client=client)

        with patch.object(client, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []

            # Query user scope
            await memory.query_about_user(query="test1")
            assert mock_search.call_args[1]["user_id"] == "user-A"
            assert "conversation_id" not in mock_search.call_args[1]

            # Query conversation scope
            await memory.query_about_conversation(query="test2")
            assert mock_search.call_args[1]["conversation_id"] == "conv-B"
            assert "user_id" not in mock_search.call_args[1]

        await client.close()

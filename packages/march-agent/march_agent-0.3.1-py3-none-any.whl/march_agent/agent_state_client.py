"""HTTP client for agent state storage API."""

import logging
from typing import Dict, Any, Optional
import aiohttp

from .exceptions import APIException

logger = logging.getLogger(__name__)


class AgentStateClient:
    """Async HTTP client for agent-state API.

    This client communicates with the conversation-store's agent-state endpoints
    to store and retrieve framework-specific state data.

    Example:
        ```python
        client = AgentStateClient("http://gateway/s/conversation-store")

        # Store state
        await client.put("conv-123", "pydantic_ai", {"messages": [...]})

        # Get state
        state = await client.get("conv-123", "pydantic_ai")

        # Delete state
        await client.delete("conv-123", "pydantic_ai")
        ```
    """

    def __init__(self, base_url: str):
        """Initialize agent state client.

        Args:
            base_url: Base URL for the agent-state API
                      (e.g., http://gateway/s/conversation-store)
        """
        self.base_url = base_url.rstrip("/")
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30.0)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def put(
        self,
        conversation_id: str,
        namespace: str,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Store or update agent state.

        Args:
            conversation_id: Conversation identifier
            namespace: Framework namespace (e.g., 'pydantic_ai')
            state: State data to store (will be serialized as JSON)

        Returns:
            Response with conversation_id, namespace, and created flag
        """
        url = f"{self.base_url}/agent-state/{conversation_id}"
        payload = {
            "namespace": namespace,
            "state": state,
        }

        session = await self._get_session()
        try:
            async with session.put(url, json=payload) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    raise APIException(
                        f"Failed to store agent state: {response.status} - {error_text}"
                    )
                return await response.json()
        except aiohttp.ClientError as e:
            raise APIException(f"Failed to store agent state: {e}")

    async def get(
        self,
        conversation_id: str,
        namespace: str,
    ) -> Optional[Dict[str, Any]]:
        """Get agent state.

        Args:
            conversation_id: Conversation identifier
            namespace: Framework namespace (e.g., 'pydantic_ai')

        Returns:
            AgentStateResponse dict or None if not found
        """
        url = f"{self.base_url}/agent-state/{conversation_id}"
        params = {"namespace": namespace}

        session = await self._get_session()
        try:
            async with session.get(url, params=params) as response:
                if response.status == 404:
                    return None
                if response.status >= 400:
                    error_text = await response.text()
                    raise APIException(
                        f"Failed to get agent state: {response.status} - {error_text}"
                    )
                return await response.json()
        except aiohttp.ClientError as e:
            raise APIException(f"Failed to get agent state: {e}")

    async def delete(
        self,
        conversation_id: str,
        namespace: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Delete agent state.

        Args:
            conversation_id: Conversation identifier
            namespace: Framework namespace (optional, deletes all if not provided)

        Returns:
            Response with conversation_id, namespace, and deleted count
        """
        url = f"{self.base_url}/agent-state/{conversation_id}"
        params = {}
        if namespace:
            params["namespace"] = namespace

        session = await self._get_session()
        try:
            async with session.delete(url, params=params) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    raise APIException(
                        f"Failed to delete agent state: {response.status} - {error_text}"
                    )
                return await response.json()
        except aiohttp.ClientError as e:
            raise APIException(f"Failed to delete agent state: {e}")

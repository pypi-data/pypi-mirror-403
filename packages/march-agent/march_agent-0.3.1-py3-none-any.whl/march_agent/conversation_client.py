"""Conversation store client for fetching conversation history."""

import logging
from typing import List, Dict, Any, Optional
import aiohttp

from .exceptions import APIException

logger = logging.getLogger(__name__)


class ConversationClient:
    """Client for interacting with conversation-store API (async)."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=10.0)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation metadata."""
        url = f"{self.base_url}/conversations/{conversation_id}"
        session = await self._get_session()
        try:
            async with session.get(url) as response:
                if response.status == 404:
                    raise APIException(f"Conversation {conversation_id} not found")
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            raise APIException(f"Failed to fetch conversation: {e}")

    async def get_messages(
        self,
        conversation_id: str,
        role: Optional[str] = None,
        from_: Optional[str] = None,
        to_: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get messages from a conversation."""
        url = f"{self.base_url}/conversations/{conversation_id}/messages"
        params = {"limit": min(limit, 1000), "offset": offset}
        if role:
            params["role"] = role
        if from_:
            params["from"] = from_
        if to_:
            params["to"] = to_

        session = await self._get_session()
        try:
            async with session.get(url, params=params) as response:
                if response.status == 404:
                    raise APIException(f"Conversation {conversation_id} not found")
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            raise APIException(f"Failed to fetch messages: {e}")

    async def update_conversation(
        self,
        conversation_id: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update conversation fields (PATCH)."""
        url = f"{self.base_url}/conversations/{conversation_id}"
        session = await self._get_session()
        try:
            async with session.patch(url, json=data) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            raise APIException(f"Failed to update conversation: {e}")

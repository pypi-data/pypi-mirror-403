"""HTTP client for checkpoint storage API."""

import logging
from typing import List, Dict, Any, Optional
import aiohttp

from .exceptions import APIException

logger = logging.getLogger(__name__)


class CheckpointClient:
    """Async HTTP client for checkpoint-store API.

    This client communicates with the conversation-store's checkpoint endpoints
    to store and retrieve LangGraph-compatible checkpoints.
    """

    def __init__(self, base_url: str):
        """Initialize checkpoint client.

        Args:
            base_url: Base URL for the checkpoint API (e.g., http://gateway/s/conversation-store)
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
        config: Dict[str, Any],
        checkpoint: Dict[str, Any],
        metadata: Dict[str, Any],
        new_versions: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Store a checkpoint.

        Args:
            config: RunnableConfig with configurable containing thread_id, checkpoint_ns, checkpoint_id
            checkpoint: Checkpoint data (channel_values, channel_versions, etc.)
            metadata: Checkpoint metadata (source, step, parents, writes)
            new_versions: New channel versions (optional)

        Returns:
            Config of the stored checkpoint
        """
        url = f"{self.base_url}/checkpoints/"
        payload = {
            "config": config,
            "checkpoint": checkpoint,
            "metadata": metadata,
            "new_versions": new_versions or {},
        }

        session = await self._get_session()
        try:
            async with session.put(url, json=payload) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    raise APIException(f"Failed to store checkpoint: {response.status} - {error_text}")
                return await response.json()
        except aiohttp.ClientError as e:
            raise APIException(f"Failed to store checkpoint: {e}")

    async def get_tuple(
        self,
        thread_id: str,
        checkpoint_ns: str = "",
        checkpoint_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get a checkpoint tuple.

        Args:
            thread_id: Thread identifier
            checkpoint_ns: Checkpoint namespace (default "")
            checkpoint_id: Specific checkpoint ID (latest if not provided)

        Returns:
            CheckpointTuple dict or None if not found
        """
        url = f"{self.base_url}/checkpoints/{thread_id}"
        params = {"checkpoint_ns": checkpoint_ns}
        if checkpoint_id:
            params["checkpoint_id"] = checkpoint_id

        session = await self._get_session()
        try:
            async with session.get(url, params=params) as response:
                if response.status == 404:
                    return None
                if response.status >= 400:
                    error_text = await response.text()
                    raise APIException(f"Failed to get checkpoint: {response.status} - {error_text}")
                result = await response.json()
                # API returns null for not found
                return result if result else None
        except aiohttp.ClientError as e:
            raise APIException(f"Failed to get checkpoint: {e}")

    async def list(
        self,
        thread_id: Optional[str] = None,
        checkpoint_ns: Optional[str] = None,
        before: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """List checkpoints.

        Args:
            thread_id: Filter by thread ID
            checkpoint_ns: Filter by namespace
            before: Return checkpoints before this checkpoint_id
            limit: Maximum number of checkpoints to return

        Returns:
            List of CheckpointTuple dicts
        """
        url = f"{self.base_url}/checkpoints/"
        params = {}
        if thread_id:
            params["thread_id"] = thread_id
        if checkpoint_ns is not None:
            params["checkpoint_ns"] = checkpoint_ns
        if before:
            params["before"] = before
        if limit:
            params["limit"] = limit

        session = await self._get_session()
        try:
            async with session.get(url, params=params) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    raise APIException(f"Failed to list checkpoints: {response.status} - {error_text}")
                return await response.json()
        except aiohttp.ClientError as e:
            raise APIException(f"Failed to list checkpoints: {e}")

    async def delete_thread(self, thread_id: str) -> Dict[str, Any]:
        """Delete all checkpoints for a thread.

        Args:
            thread_id: Thread identifier

        Returns:
            Dict with thread_id and deleted count
        """
        url = f"{self.base_url}/checkpoints/{thread_id}"

        session = await self._get_session()
        try:
            async with session.delete(url) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    raise APIException(f"Failed to delete checkpoints: {response.status} - {error_text}")
                return await response.json()
        except aiohttp.ClientError as e:
            raise APIException(f"Failed to delete checkpoints: {e}")

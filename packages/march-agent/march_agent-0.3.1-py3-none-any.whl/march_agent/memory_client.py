"""HTTP client for AI Memory service."""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode
import aiohttp

from .exceptions import APIException

logger = logging.getLogger(__name__)


@dataclass
class MemoryMessage:
    """A message from ai-memory storage.

    Exactly matches the ai-memory API MessageStored schema.
    """

    id: str
    role: str  # "user", "assistant", "system"
    content: str
    tenant_id: Optional[str] = None  # Agent scope/namespace
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    sequence_number: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryMessage":
        """Create from ai-memory API response."""
        return cls(
            id=data.get("id", ""),
            role=data.get("role", ""),
            content=data.get("content", ""),
            tenant_id=data.get("tenant_id"),
            user_id=data.get("user_id"),
            conversation_id=data.get("conversation_id"),
            metadata=data.get("metadata"),
            timestamp=data.get("timestamp"),
            sequence_number=data.get("sequence_number"),
        )


@dataclass
class MemorySearchResult:
    """A memory search result with similarity score."""

    message: MemoryMessage
    score: float
    context: List[MemoryMessage] = field(default_factory=list)


@dataclass
class UserSummary:
    """User conversation summary."""

    text: str
    last_updated: str
    message_count: int
    version: int


class MemoryClient:
    """Low-level async HTTP client for AI Memory service."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30.0)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        limit: int = 10,
        min_similarity: int = 70,
        context_messages: int = 0,
    ) -> List[MemorySearchResult]:
        """Search long-term memory with semantic search."""
        params = {
            "q": query,
            "limit": limit,
            "min_similarity": min_similarity,
            "context_messages": context_messages,
        }
        if user_id:
            params["user_id"] = user_id
        if conversation_id:
            params["conversation_id"] = conversation_id
        if tenant_id:
            params["tenant_id"] = tenant_id

        url = f"{self.base_url}/conversation/search?{urlencode(params)}"
        session = await self._get_session()
        try:
            async with session.get(url) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    raise APIException(
                        f"Memory search failed: {response.status} - {error_text}"
                    )
                data = await response.json()

            results = []
            for item in data.get("results", []):
                msg = MemoryMessage.from_dict(item["message"])
                context = [MemoryMessage.from_dict(c) for c in item.get("context", [])]
                results.append(
                    MemorySearchResult(message=msg, score=item["score"], context=context)
                )
            return results
        except aiohttp.ClientError as e:
            raise APIException(f"Memory search failed: {e}")

    async def get_user_summary(self, user_id: str) -> Optional[UserSummary]:
        """Get user's conversation summary."""
        url = f"{self.base_url}/conversation/user/{user_id}/summary"
        session = await self._get_session()
        try:
            async with session.get(url) as response:
                if response.status == 404:
                    return None
                if response.status >= 400:
                    error_text = await response.text()
                    raise APIException(
                        f"Summary fetch failed: {response.status} - {error_text}"
                    )
                data = await response.json()

            if not data.get("has_summary") or not data.get("summary"):
                return None

            s = data["summary"]
            return UserSummary(
                text=s["text"],
                last_updated=s["last_updated"],
                message_count=s["message_count"],
                version=s.get("version", 1),
            )
        except aiohttp.ClientError as e:
            raise APIException(f"Summary fetch failed: {e}")

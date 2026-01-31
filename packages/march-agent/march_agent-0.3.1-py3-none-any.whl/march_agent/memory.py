"""Memory context for accessing AI memory from message handler."""

from typing import List, Optional

from .memory_client import MemoryClient, MemorySearchResult, UserSummary


class Memory:
    """User-facing memory context, attached to Message.

    Provides easy access to memory functions scoped to the current user/conversation.
    """

    def __init__(self, user_id: str, conversation_id: str, client: MemoryClient):
        self.user_id = user_id
        self.conversation_id = conversation_id
        self._client = client

    async def query_about_user(
        self,
        query: str,
        limit: int = 10,
        threshold: int = 70,
        context_messages: int = 0,
    ) -> List[MemorySearchResult]:
        """Query user's long-term memory with semantic search.

        Args:
            query: Semantic search query
            limit: Maximum results (1-100)
            threshold: Similarity threshold 0-100
            context_messages: Surrounding messages to include (0-20)

        Returns:
            List of MemorySearchResult
        """
        return await self._client.search(
            query=query,
            user_id=self.user_id,
            limit=limit,
            min_similarity=threshold,
            context_messages=context_messages,
        )

    async def query_about_conversation(
        self,
        query: str,
        limit: int = 10,
        threshold: int = 70,
        context_messages: int = 0,
    ) -> List[MemorySearchResult]:
        """Query conversation's long-term memory with semantic search.

        Args:
            query: Semantic search query
            limit: Maximum results (1-100)
            threshold: Similarity threshold 0-100
            context_messages: Surrounding messages to include (0-20)

        Returns:
            List of MemorySearchResult
        """
        return await self._client.search(
            query=query,
            conversation_id=self.conversation_id,
            limit=limit,
            min_similarity=threshold,
            context_messages=context_messages,
        )

    async def get_user_summary(self) -> Optional[UserSummary]:
        """Get user's summary (aggregated across all conversations)."""
        return await self._client.get_user_summary(self.user_id)

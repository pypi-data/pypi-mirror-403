"""Conversation context for accessing message history."""

import asyncio
from typing import List, Dict, Any, Optional

from .conversation_client import ConversationClient
from .conversation_message import ConversationMessage


class Conversation:
    """Lazy-loaded conversation context (async)."""

    def __init__(
        self,
        conversation_id: str,
        client: ConversationClient,
        agent_name: Optional[str] = None,
    ):
        self.id = conversation_id
        self._client = client
        self._agent_name = agent_name

    async def get_history(
        self,
        role: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ConversationMessage]:
        """Fetch conversation message history.

        Args:
            role: Optional filter by role ('user', 'assistant', 'system')
            limit: Maximum messages to fetch
            offset: Pagination offset

        Returns:
            List of ConversationMessage objects
        """
        messages = await self._client.get_messages(
            conversation_id=self.id, role=role, limit=limit, offset=offset
        )
        return ConversationMessage.from_list(messages)

    async def get_metadata(self) -> Dict[str, Any]:
        """Fetch conversation metadata."""
        return await self._client.get_conversation(self.id)

    async def get_agent_history(
        self,
        agent_name: Optional[str] = None,
        role: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ConversationMessage]:
        """Fetch messages where agent was sender or recipient.

        Makes two API calls concurrently to get both sent and received messages,
        then merges and sorts by sequence number.

        Args:
            agent_name: The agent name to filter by. Defaults to the current agent
                if not specified (requires agent_name to be set during Conversation init).
            role: Optional role filter ('user', 'assistant', 'system')
            limit: Maximum messages to fetch per query
            offset: Pagination offset

        Returns:
            List of ConversationMessage where from_==agent_name OR to_==agent_name

        Raises:
            ValueError: If agent_name is not provided and no default is set.
        """
        # Use provided agent_name or fall back to the default from init
        agent_name = agent_name or self._agent_name
        if not agent_name:
            raise ValueError(
                "agent_name must be provided either as argument or set during Conversation initialization"
            )
        # Run both queries concurrently
        sent_task = self._client.get_messages(
            conversation_id=self.id,
            role=role,
            from_=agent_name,
            limit=limit,
            offset=offset,
        )

        received_task = self._client.get_messages(
            conversation_id=self.id,
            role=role,
            to_=agent_name,
            limit=limit,
            offset=offset,
        )

        sent, received = await asyncio.gather(sent_task, received_task)

        # Merge and dedupe (in case from_==to_)
        all_msgs = {msg["id"]: msg for msg in sent + received}

        # Sort by sequence_number and convert to typed messages
        sorted_msgs = sorted(all_msgs.values(), key=lambda m: m.get("sequence_number", 0))
        return ConversationMessage.from_list(sorted_msgs)

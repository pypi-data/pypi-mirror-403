"""Pydantic AI extension for march_agent.

This module provides integration with Pydantic AI, enabling persistent
message history storage via the agent-state API.

Usage:
    from march_agent import MarchAgentApp
    from march_agent.extensions.pydantic_ai import PydanticAIMessageStore
    from pydantic_ai import Agent

    app = MarchAgentApp(gateway_url="agent-gateway:8080", api_key="key")
    store = PydanticAIMessageStore(app=app)

    my_agent = Agent('openai:gpt-4o', system_prompt="...")

    @medical_agent.on_message
    async def handle(message, sender):
        # Load message history
        history = await store.load(message.conversation_id)

        # Run agent with streaming
        async with medical_agent.streamer(message) as s:
            async with my_agent.run_stream(message.content, message_history=history) as result:
                async for chunk in result.stream_text():
                    s.stream(chunk)

            # Save updated history
            await store.save(message.conversation_id, result.all_messages())
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List, Any, Optional

if TYPE_CHECKING:
    from ..app import MarchAgentApp

logger = logging.getLogger(__name__)

# Try to import Pydantic AI types, but make them optional
try:
    from pydantic_ai.messages import (
        ModelMessage,
        ModelMessagesTypeAdapter,
    )

    PYDANTIC_AI_AVAILABLE = True
except ImportError:
    PYDANTIC_AI_AVAILABLE = False
    ModelMessage = Any
    ModelMessagesTypeAdapter = None

from ..agent_state_client import AgentStateClient


class PydanticAIMessageStore:
    """Persistent message store for Pydantic AI.

    Stores and retrieves Pydantic AI native message history using the
    agent-state API. Messages are serialized using Pydantic AI's built-in
    ModelMessagesTypeAdapter for full fidelity.

    Example:
        ```python
        from march_agent import MarchAgentApp
        from march_agent.extensions.pydantic_ai import PydanticAIMessageStore
        from pydantic_ai import Agent

        app = MarchAgentApp(gateway_url="...", api_key="...")
        store = PydanticAIMessageStore(app=app)

        my_agent = Agent('openai:gpt-4o')

        @medical_agent.on_message
        async def handle(message, sender):
            history = await store.load(message.conversation_id)

            async with medical_agent.streamer(message) as s:
                async with my_agent.run_stream(
                    message.content,
                    message_history=history
                ) as result:
                    async for chunk in result.stream_text():
                        s.stream(chunk)

                await store.save(message.conversation_id, result.all_messages())
        ```
    """

    NAMESPACE = "pydantic_ai"

    def __init__(self, app: "MarchAgentApp"):
        """Initialize Pydantic AI message store.

        Args:
            app: MarchAgentApp instance to get the gateway client from.
        """
        if not PYDANTIC_AI_AVAILABLE:
            raise ImportError(
                "pydantic-ai is required for PydanticAIMessageStore. "
                "Install it with: pip install march-agent[pydantic]"
            )

        base_url = app.gateway_client.conversation_store_url
        self.client = AgentStateClient(base_url)
        self._app = app

    async def load(self, conversation_id: str) -> List[ModelMessage]:
        """Load Pydantic AI message history for a conversation.

        Args:
            conversation_id: The conversation ID to load history for.

        Returns:
            List of ModelMessage objects (empty list if no history).
        """
        result = await self.client.get(conversation_id, self.NAMESPACE)

        if not result:
            logger.debug(f"No message history found for conversation {conversation_id}")
            return []

        state = result.get("state", {})
        messages_data = state.get("messages", [])

        if not messages_data:
            return []

        # Deserialize using Pydantic AI's TypeAdapter
        try:
            messages = ModelMessagesTypeAdapter.validate_python(messages_data)
            logger.debug(
                f"Loaded {len(messages)} messages for conversation {conversation_id}"
            )
            return messages
        except Exception as e:
            logger.error(f"Failed to deserialize messages: {e}")
            return []

    async def save(
        self,
        conversation_id: str,
        messages: List[ModelMessage],
    ) -> None:
        """Save Pydantic AI message history for a conversation.

        Args:
            conversation_id: The conversation ID to save history for.
            messages: List of ModelMessage objects to save.
        """
        # Serialize using Pydantic AI's TypeAdapter
        try:
            serialized = ModelMessagesTypeAdapter.dump_python(messages, mode="json")
        except Exception as e:
            logger.error(f"Failed to serialize messages: {e}")
            raise

        await self.client.put(
            conversation_id,
            self.NAMESPACE,
            {"messages": serialized},
        )

        logger.debug(
            f"Saved {len(messages)} messages for conversation {conversation_id}"
        )

    async def clear(self, conversation_id: str) -> None:
        """Clear message history for a conversation.

        Args:
            conversation_id: The conversation ID to clear history for.
        """
        await self.client.delete(conversation_id, self.NAMESPACE)
        logger.debug(f"Cleared message history for conversation {conversation_id}")

    async def close(self) -> None:
        """Close the HTTP client session."""
        await self.client.close()

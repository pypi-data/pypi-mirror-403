"""Streamer class for streaming responses with context manager support."""

import json
import logging
from typing import Optional, Dict, Any, TypeVar, TYPE_CHECKING

from .structural.base import StructuralStreamer

if TYPE_CHECKING:
    from .gateway_client import GatewayClient
    from .message import Message
    from .conversation_client import ConversationClient

T = TypeVar('T', bound=StructuralStreamer)

logger = logging.getLogger(__name__)


class Streamer:
    """Handles streaming responses back to the conversation via the gateway (async)."""

    def __init__(
        self,
        agent_name: str,
        original_message: "Message",
        gateway_client: "GatewayClient",
        conversation_client: Optional["ConversationClient"] = None,
        awaiting: bool = False,
        send_to: str = "user",
    ):
        self._agent_name = agent_name
        self._original_message = original_message
        self._gateway_client = gateway_client
        self._conversation_client = conversation_client
        self._awaiting = awaiting  # Used by context manager
        self._send_to = send_to
        self._finished = False
        self._response_schema: Optional[Dict[str, Any]] = None
        self._message_metadata: Optional[Dict[str, Any]] = None

    def set_response_schema(self, schema: Dict[str, Any]) -> "Streamer":
        """Set response schema (fluent API)."""
        self._response_schema = schema
        return self

    def set_message_metadata(self, metadata: Dict[str, Any]) -> "Streamer":
        """Set message metadata (fluent API)."""
        self._message_metadata = metadata
        return self

    def stream_by(self, structural: T) -> T:
        """Bind a structural streamer to this streamer for event sending.

        Returns the structural object itself with streaming capability enabled.

        Args:
            structural: StructuralStreamer instance (Artifact, Surface, etc.)

        Returns:
            The same structural object, now bound to this streamer

        Example:
            artifact = Artifact()
            s.stream_by(artifact).generating("Creating...")
            s.stream_by(artifact).done(url="...", type="image")
        """
        return structural._bind_streamer(self)

    def stream(
        self, content: str, persist: bool = True, event_type: Optional[str] = None
    ) -> None:
        """Stream a content chunk (not done).

        Args:
            content: The content to stream
            persist: If True, this content will be saved to DB. If False, only streamed.
            event_type: Optional event type for the chunk (e.g., 'thinking', 'tool_call').
        """
        if self._finished:
            raise RuntimeError("Streamer already finished")
        self._send(content, done=False, persist=persist, event_type=event_type)

    def write(self, content: str, persist: bool = True) -> None:
        """Alias for stream() - write a content chunk.

        Args:
            content: The content to write
            persist: If True, this content will be saved to DB. If False, only streamed.
        """
        self.stream(content, persist=persist)

    async def finish(self, awaiting: Optional[bool] = None) -> None:
        """Finish streaming with empty done=True chunk.

        Args:
            awaiting: If True, sets awaiting_route to this agent's name.
                     If None, uses the awaiting value from constructor.
                     If response_schema was set and awaiting is not explicitly False,
                     awaiting is automatically set to True.
        """
        if self._finished:
            return  # Idempotent

        self._send("", done=True, persist=True)
        self._finished = True

        # Determine if we should set awaiting_route
        # Priority: explicit awaiting arg > constructor awaiting > auto-await for schema
        if awaiting is not None:
            should_await = awaiting
        elif self._awaiting:
            should_await = True
        elif self._response_schema is not None:
            # Auto-await when response_schema is set (so next message comes back to this agent)
            should_await = True
        else:
            should_await = False

        # Store pending_response_schema if schema was set
        if self._response_schema and self._conversation_client:
            await self._set_pending_response_schema()

        if should_await and self._conversation_client:
            await self._set_awaiting_route()

    def _send(
        self,
        content: str,
        done: bool,
        persist: bool = True,
        event_type: Optional[str] = None,
    ) -> None:
        """Send message to router via gateway (sync - uses gRPC)."""
        message_body = {"content": content, "done": done, "persist": persist}
        if event_type:
            message_body["eventType"] = event_type
        headers = {
            "conversationId": self._original_message.conversation_id,
            "userId": self._original_message.user_id,
            "from_": self._agent_name,
            "to_": self._send_to,
            "nextRoute": self._send_to,
        }
        if self._response_schema:
            headers["responseSchema"] = json.dumps(self._response_schema)
        if self._message_metadata:
            headers["messageMetadata"] = json.dumps(self._message_metadata)

        # Produce via gateway gRPC (synchronous operation)
        self._gateway_client.produce(
            topic="router.inbox",
            key=self._original_message.conversation_id,
            headers=headers,
            body=message_body,
        )

    async def _set_pending_response_schema(self) -> None:
        """Store response schema on conversation for form validation."""
        try:
            await self._conversation_client.update_conversation(
                self._original_message.conversation_id,
                {"pending_response_schema": self._response_schema},
            )
        except Exception as e:
            logger.error(f"Failed to set pending_response_schema: {e}")

    async def _set_awaiting_route(self) -> None:
        """Set awaiting_route to this agent's name."""
        try:
            await self._conversation_client.update_conversation(
                self._original_message.conversation_id,
                {"awaiting_route": self._agent_name},
            )
        except Exception as e:
            logger.error(f"Failed to set awaiting_route: {e}")

    async def __aenter__(self) -> "Streamer":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if not self._finished:
            # Pass None to let finish() determine awaiting based on schema or constructor value
            await self.finish(awaiting=None)
        return False  # Don't suppress exceptions

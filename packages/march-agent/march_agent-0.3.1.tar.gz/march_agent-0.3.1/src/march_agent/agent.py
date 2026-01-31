"""Core agent class for handling messages."""

import asyncio
import inspect
import logging
from typing import Callable, Optional, Dict, Any, List, Tuple, Set

from .gateway_client import GatewayClient, KafkaMessage
from .heartbeat import HeartbeatManager
from .message import Message
from .conversation_client import ConversationClient
from .memory_client import MemoryClient
from .attachment_client import AttachmentClient
from .streamer import Streamer
from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class SenderFilter:
    """Filter for matching message senders."""

    def __init__(self, senders: Optional[List[str]] = None):
        self.include: Set[str] = set()
        self.exclude: Set[str] = set()
        self.match_all = senders is None or len(senders) == 0

        if senders:
            for s in senders:
                if s.startswith("~"):
                    self.exclude.add(s[1:])
                else:
                    self.include.add(s)

    def matches(self, sender: str) -> bool:
        """Check if sender matches this filter."""
        if self.match_all:
            return True
        if sender in self.exclude:
            return False
        if self.include and sender not in self.include:
            return False
        return True


class Agent:
    """Core agent class that handles messaging via the Agent Gateway."""

    def __init__(
        self,
        name: str,
        gateway_client: GatewayClient,
        agent_data: Dict[str, Any],
        heartbeat_interval: int = 60,
        conversation_client: Optional[ConversationClient] = None,
        memory_client: Optional[MemoryClient] = None,
        attachment_client: Optional[AttachmentClient] = None,
        error_message_template: str = "I encountered an error while processing your message. Please try again or contact support if the issue persists.",
    ):
        self.name = name
        self.gateway_client = gateway_client
        self.agent_data = agent_data
        self.conversation_client = conversation_client
        self.memory_client = memory_client
        self.attachment_client = attachment_client
        self.heartbeat_interval = heartbeat_interval

        # Error handling configuration
        self.error_message_template: str = error_message_template
        self.send_error_responses: bool = True

        self.heartbeat_manager: Optional[HeartbeatManager] = None
        self._message_handlers: List[Tuple[SenderFilter, Callable]] = []
        self._running = False
        self._initialized = False

        logger.info(f"Agent '{name}' created")

    def _initialize_with_gateway(self):
        """Initialize agent after gateway connection is established."""
        if self._initialized:
            return

        # Start heartbeat via gateway proxy
        self.heartbeat_manager = HeartbeatManager(
            gateway_client=self.gateway_client,
            agent_name=self.name,
            interval=self.heartbeat_interval,
        )
        self.heartbeat_manager.start()

        self._initialized = True
        logger.info(f"Agent '{self.name}' initialized with gateway")

    def on_message(self, handler_or_senders=None, *, senders: Optional[List[str]] = None):
        """Register message handler with optional sender filter.

        Supports both:
            @agent.on_message          # catch-all
            @agent.on_message(senders=["user"])  # filtered

        Args:
            senders: List of sender names to match. Prefix with ~ to exclude.
                     Examples: ["user"], ["agent-1", "agent-2"], ["~user"]
        """
        def decorator(handler: Callable[[Message, str], None]):
            sender_filter = SenderFilter(senders)
            self._message_handlers.append((sender_filter, handler))
            logger.info(f"Handler registered for agent '{self.name}' with senders={senders}")
            return handler

        # Called as @on_message (no parens) - handler_or_senders is the function
        if callable(handler_or_senders):
            return decorator(handler_or_senders)

        # Called as @on_message(senders=[...]) - return decorator
        return decorator

    def _get_sender(self, headers: Dict[str, str]) -> str:
        """Determine sender from headers."""
        return headers.get("from_", "user")

    def _find_matching_handler(self, sender: str) -> Optional[Callable]:
        """Find first handler that matches the sender."""
        for sender_filter, handler in self._message_handlers:
            if sender_filter.matches(sender):
                return handler
        return None

    def _send_error_response(
        self,
        message: Message,
        error: Exception,
        handler_name: Optional[str] = None
    ) -> None:
        """Send error response to user when handler fails (sync - deprecated).

        Fail-safe design: wraps everything in try-except to prevent
        cascading failures if error response itself fails.

        Args:
            message: The original message that caused the error
            error: The exception that was caught
            handler_name: Optional name of the handler that failed
        """
        if not self.send_error_responses:
            return

        try:
            # Log detailed error for debugging with structured fields
            handler_info = f" in handler '{handler_name}'" if handler_name else ""
            logger.error(
                f"Handler error{handler_info} for agent '{self.name}': {error}",
                exc_info=True,
                extra={
                    "agent_name": self.name,
                    "conversation_id": message.conversation_id,
                    "error_type": type(error).__name__,
                }
            )

            # Create streamer with original message context
            streamer = self.streamer(
                original_message=message,
                send_to="user"
            )

            # Send error message (stream is sync, but we can't await here)
            streamer.stream(self.error_message_template)
            # Note: Can't use async context manager in sync method

            logger.info(
                f"Error response sent to user for conversation {message.conversation_id}"
            )

        except Exception as send_error:
            # Fail-safe: if sending error response fails, just log it
            logger.error(
                f"Failed to send error response: {send_error}",
                exc_info=True,
                extra={
                    "agent_name": self.name,
                    "conversation_id": message.conversation_id,
                    "original_error": str(error),
                }
            )

    async def _send_error_response_async(
        self,
        message: Message,
        error: Exception,
        handler_name: Optional[str] = None
    ) -> None:
        """Send error response to user when handler fails (async).

        Fail-safe design: wraps everything in try-except to prevent
        cascading failures if error response itself fails.

        Args:
            message: The original message that caused the error
            error: The exception that was caught
            handler_name: Optional name of the handler that failed
        """
        if not self.send_error_responses:
            return

        try:
            # Log detailed error for debugging with structured fields
            handler_info = f" in handler '{handler_name}'" if handler_name else ""
            logger.error(
                f"Handler error{handler_info} for agent '{self.name}': {error}",
                exc_info=True,
                extra={
                    "agent_name": self.name,
                    "conversation_id": message.conversation_id,
                    "error_type": type(error).__name__,
                }
            )

            # Create streamer with original message context
            streamer = self.streamer(
                original_message=message,
                send_to="user"
            )

            # Send error message using async context manager pattern
            async with streamer as s:
                s.stream(self.error_message_template)

            logger.info(
                f"Error response sent to user for conversation {message.conversation_id}"
            )

        except Exception as send_error:
            # Fail-safe: if sending error response fails, just log it
            logger.error(
                f"Failed to send error response: {send_error}",
                exc_info=True,
                extra={
                    "agent_name": self.name,
                    "conversation_id": message.conversation_id,
                    "original_error": str(error),
                }
            )

    async def _handle_message_async(self, kafka_msg: KafkaMessage):
        """Handle incoming Kafka message asynchronously."""
        message = None
        handler = None

        try:
            headers = kafka_msg.headers
            body = kafka_msg.body if isinstance(kafka_msg.body, dict) else {}

            sender = self._get_sender(headers)
            handler = self._find_matching_handler(sender)

            if handler is None:
                logger.warning(f"No handler matched for sender: {sender}")
                return

            # Create message before handler execution
            message = Message.from_kafka_message(
                body, headers,
                conversation_client=self.conversation_client,
                memory_client=self.memory_client,
                attachment_client=self.attachment_client,
                agent_name=self.name,
            )

            # Execute handler based on whether it's async or sync
            if inspect.iscoroutinefunction(handler):
                # Async handler - await it directly
                await handler(message, sender)
            else:
                # Sync handler - run in thread pool for backward compatibility
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, handler, message, sender)

        except Exception as e:
            # Handler execution failed - send error response to user
            # Only send if we successfully created the message
            if message is not None:
                handler_name = handler.__name__ if handler and hasattr(handler, '__name__') else None
                await self._send_error_response_async(message, e, handler_name)
            else:
                # Message creation failed - just log (can't respond without context)
                logger.error(
                    f"Error processing Kafka message before handler execution: {e}",
                    exc_info=True,
                    extra={"agent_name": self.name}
                )

    def start_consuming(self):
        """Mark agent as ready to consume messages.

        Note: Actual consumption is handled by the gateway client's consume loop.
        This method just sets the agent as running and waits for shutdown.
        """
        if not self._message_handlers:
            raise ConfigurationError("No message handlers registered.")

        if not self._initialized:
            raise ConfigurationError("Agent not initialized. Call _initialize_with_gateway first.")

        logger.info(f"Agent '{self.name}' ready to consume messages")
        self._running = True

        # The gateway client handles all message consumption in a single thread.
        # We just keep this thread alive until shutdown.
        import time
        while self._running:
            time.sleep(1.0)

    def streamer(
        self,
        original_message: Message,
        awaiting: bool = False,
        send_to: str = "user",
    ) -> Streamer:
        """Create a new Streamer for streaming responses.

        Args:
            original_message: The message being responded to
            awaiting: If True (and using context manager), sets awaiting_route on finish
            send_to: Target for the response - "user" (default) or another agent name
        """
        return Streamer(
            agent_name=self.name,
            original_message=original_message,
            gateway_client=self.gateway_client,
            conversation_client=self.conversation_client,
            awaiting=awaiting,
            send_to=send_to,
        )

    def shutdown(self):
        """Shutdown agent gracefully."""
        logger.info(f"Shutting down agent '{self.name}'...")
        self._running = False

        if self.heartbeat_manager:
            self.heartbeat_manager.stop()

        logger.info(f"Agent '{self.name}' shutdown complete")

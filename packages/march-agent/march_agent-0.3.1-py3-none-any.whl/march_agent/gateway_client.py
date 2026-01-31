"""
Gateway client for connecting to the Agent Gateway service.
Handles gRPC communication for Kafka and HTTP for other services.
"""

import json
import logging
import queue
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Any, Tuple

import grpc
import requests
import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class KafkaMessage:
    """Represents a message received from Kafka via the gateway."""
    topic: str
    partition: int
    offset: int
    key: str
    headers: Dict[str, str]
    body: Dict[str, Any]
    timestamp: int


class GatewayClient:
    """
    Client for communicating with the Agent Gateway.

    Provides:
    - gRPC bidirectional streaming for Kafka consume/produce
    - HTTP proxy for AI Inventory and Conversation Store
    """

    def __init__(self, gateway_url: str, api_key: str, secure: bool = False):
        """
        Initialize the gateway client.

        Args:
            gateway_url: Gateway endpoint (e.g., "agent-gateway:8080")
            api_key: API key for authentication
            secure: If True, use TLS for gRPC and HTTPS for HTTP requests
        """
        # Both gRPC and HTTP use the same endpoint (multiplexed via cmux)
        self.grpc_url = gateway_url
        self.secure = secure
        scheme = "https" if secure else "http"
        self.http_url = f"{scheme}://{gateway_url}"
        self.api_key = api_key

        self.channel: Optional[grpc.Channel] = None
        self.stub = None
        self.stream = None

        self.connection_id: Optional[str] = None
        self.subscribed_topics: List[str] = []

        self._running = False
        self._send_queue: queue.Queue = queue.Queue()
        self._lock = threading.Lock()

        # Import generated protobuf code lazily
        self._pb = None
        self._pb_grpc = None

        # Topic handlers (for compatibility, routing done by MarchAgentApp)
        self._handlers: Dict[str, Callable] = {}

        # Async HTTP session
        self._http_session: Optional[aiohttp.ClientSession] = None

    def _load_protobuf(self):
        """Lazily load protobuf modules."""
        if self._pb is None:
            from . import gateway_pb2 as pb
            from . import gateway_pb2_grpc as pb_grpc
            self._pb = pb
            self._pb_grpc = pb_grpc

    @property
    def ai_inventory_url(self) -> str:
        """HTTP URL for AI Inventory service via proxy."""
        return f"{self.http_url}/s/ai-inventory"

    @property
    def conversation_store_url(self) -> str:
        """HTTP URL for Conversation Store service via proxy."""
        return f"{self.http_url}/s/conversation-store"

    @property
    def ai_memory_url(self) -> str:
        """HTTP URL for AI Memory service via proxy."""
        return f"{self.http_url}/s/ai-memory"

    @property
    def attachment_url(self) -> str:
        """HTTP URL for Attachment service via proxy."""
        return f"{self.http_url}/s/attachment"

    def register_handler(self, topic: str, handler: Callable) -> None:
        """
        Register a handler for a topic.

        Note: Message routing is handled by MarchAgentApp._consume_loop(),
        this method is kept for compatibility.
        """
        self._handlers[topic] = handler
        logger.debug(f"Registered handler for topic: {topic}")

    def connect(self, agent_names: List[str]) -> List[str]:
        """
        Connect to the gateway and authenticate.

        Args:
            agent_names: List of agent names to subscribe to

        Returns:
            List of subscribed topic names
        """
        self._load_protobuf()
        pb = self._pb
        pb_grpc = self._pb_grpc

        logger.info(f"Connecting to gRPC gateway at {self.grpc_url} (secure={self.secure})")

        # Create gRPC channel with keepalive settings
        options = [
            ('grpc.keepalive_time_ms', 30000),  # Send keepalive ping every 30s
            ('grpc.keepalive_timeout_ms', 10000),  # Wait 10s for ping ack
            ('grpc.keepalive_permit_without_calls', True),  # Allow pings without active calls
            ('grpc.http2.min_time_between_pings_ms', 10000),  # Min time between pings
            ('grpc.http2.max_pings_without_data', 0),  # Unlimited pings without data
        ]

        if self.secure:
            # Use system default SSL credentials for TLS
            credentials = grpc.ssl_channel_credentials()
            self.channel = grpc.secure_channel(self.grpc_url, credentials, options=options)
        else:
            self.channel = grpc.insecure_channel(self.grpc_url, options=options)
        self.stub = pb_grpc.AgentGatewayStub(self.channel)

        # Start bidirectional stream
        # Create a fresh queue to prevent old generator from stealing messages
        self._send_queue = queue.Queue()
        self._running = True

        # Prepare auth message to send first
        auth_request = pb.ClientMessage(
            auth=pb.AuthRequest(
                api_key=self.api_key,
                agent_names=agent_names
            )
        )

        # Create request iterator that sends auth first, then reads from queue
        self._request_iterator = self._generate_requests(auth_request)

        # Start the stream
        self.stream = self.stub.AgentStream(self._request_iterator)

        # Wait for auth response
        try:
            response = next(self.stream)

            if response.HasField("error"):
                error = response.error
                raise AuthenticationError(f"Authentication failed: {error.message}")

            if response.HasField("auth_response"):
                auth_resp = response.auth_response
                self.connection_id = auth_resp.connection_id
                self.subscribed_topics = list(auth_resp.subscribed_topics)

                logger.info(f"Connected to gateway (connection_id: {self.connection_id})")
                logger.info(f"Subscribed to topics: {self.subscribed_topics}")

                return self.subscribed_topics
            else:
                raise GatewayError(f"Unexpected response type")

        except grpc.RpcError as e:
            raise GatewayError(f"gRPC error during auth: {e}")

    def _generate_requests(self, first_message=None):
        """Generator that yields requests. Sends first_message immediately, then from queue."""
        # Capture local reference to this connection's queue.
        # On reconnect, connect() creates a new _send_queue, so this generator
        # will only drain the old (now-orphaned) queue and won't steal from the new one.
        my_queue = self._send_queue

        # Send the first message (auth) immediately
        if first_message:
            logger.debug("Sending auth message")
            yield first_message

        # Then continue with queued messages
        seq = 0
        while self._running and my_queue is self._send_queue:
            try:
                msg = my_queue.get(timeout=0.1)
                seq += 1
                if hasattr(msg, 'produce') and msg.HasField('produce'):
                    body_preview = msg.produce.body[:80].decode('utf-8', errors='replace') if msg.produce.body else ''
                    logger.info(f"[GENERATOR] Yielding produce #{seq}, key={msg.produce.key}, body={body_preview}")
                yield msg
                logger.info(f"[GENERATOR] Yielded #{seq} successfully (gRPC consumed it)")
            except queue.Empty:
                continue

    def subscribe(self, agent_name: str) -> str:
        """
        Subscribe to an additional agent's topic.

        Args:
            agent_name: Name of the agent to subscribe to

        Returns:
            Topic name that was subscribed to
        """
        pb = self._pb

        if not self.stream:
            raise GatewayError("Not connected to gateway")

        msg = pb.ClientMessage(
            subscribe=pb.SubscribeRequest(agent_name=agent_name)
        )
        self._send_queue.put(msg)

        # Wait for response
        try:
            response = next(self.stream)

            if response.HasField("error"):
                raise GatewayError(f"Subscribe failed: {response.error.message}")

            if response.HasField("subscribe_ack"):
                topic = response.subscribe_ack.topic
                self.subscribed_topics.append(topic)
                logger.info(f"Subscribed to topic: {topic}")
                return topic

        except grpc.RpcError as e:
            raise GatewayError(f"Subscribe failed: {e}")

        raise GatewayError("Unexpected response")

    def unsubscribe(self, agent_name: str) -> None:
        """
        Unsubscribe from an agent's topic.

        Args:
            agent_name: Name of the agent to unsubscribe from
        """
        pb = self._pb

        if not self.stream:
            raise GatewayError("Not connected to gateway")

        msg = pb.ClientMessage(
            unsubscribe=pb.UnsubscribeRequest(agent_name=agent_name)
        )
        self._send_queue.put(msg)

        topic = f"{agent_name}.inbox"
        if topic in self.subscribed_topics:
            self.subscribed_topics.remove(topic)
        logger.info(f"Unsubscribed from agent: {agent_name}")

    def produce(
        self,
        topic: str,
        key: str,
        headers: Dict[str, str],
        body: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Produce a message to Kafka via the gateway.

        Args:
            topic: Target topic (usually "router.inbox")
            key: Message key (usually conversation_id)
            headers: Message headers
            body: Message body
            correlation_id: Optional correlation ID for tracking

        Returns:
            Produce acknowledgment with partition and offset
        """
        pb = self._pb

        if not self.stream:
            raise GatewayError("Not connected to gateway")

        # Serialize body to JSON bytes
        body_bytes = json.dumps(body).encode('utf-8')

        msg = pb.ClientMessage(
            produce=pb.ProduceRequest(
                topic=topic,
                key=key,
                headers=headers,
                body=body_bytes,
                correlation_id=correlation_id or ""
            )
        )
        body_preview = body_bytes[:80].decode('utf-8', errors='replace')
        logger.info(f"[PRODUCE] Queuing message, key={key}, queue_size={self._send_queue.qsize()}, body={body_preview}")
        self._send_queue.put(msg)

        # Don't block waiting for ack
        return {"status": "sent", "topic": topic}

    def consume_one(self, timeout: float = 1.0) -> Optional[KafkaMessage]:
        """
        Consume a single message (blocking).

        Args:
            timeout: Maximum time to wait for a message

        Returns:
            KafkaMessage or None if timeout
        """
        if not self.stream:
            raise GatewayError("Not connected to gateway")

        try:
            response = next(self.stream)

            if response.HasField("message"):
                kafka_msg = response.message

                # Parse body from JSON bytes
                try:
                    body = json.loads(kafka_msg.body.decode('utf-8'))
                except json.JSONDecodeError:
                    body = {}

                return KafkaMessage(
                    topic=kafka_msg.topic,
                    partition=kafka_msg.partition,
                    offset=kafka_msg.offset,
                    key=kafka_msg.key,
                    headers=dict(kafka_msg.headers),
                    body=body,
                    timestamp=kafka_msg.timestamp
                )
            elif response.HasField("produce_ack"):
                logger.debug(f"Received produce_ack for topic {response.produce_ack.topic}")
                return None
            elif response.HasField("pong"):
                return None
            elif response.HasField("error"):
                logger.error(f"Gateway error: {response.error.message}")
                return None
            else:
                logger.debug(f"Received other message type")
                return None

        except StopIteration:
            logger.warning("Stream ended")
            raise GatewayError("Stream ended unexpectedly")
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                return None
            logger.error(f"Error in consume_one: {e}")
            raise GatewayError(f"Consume error: {e}")

    def ping(self) -> int:
        """
        Send a ping to the gateway.

        Returns:
            Client timestamp sent
        """
        pb = self._pb

        if not self.stream:
            raise GatewayError("Not connected to gateway")

        timestamp = int(time.time() * 1000)
        msg = pb.ClientMessage(
            ping=pb.PingRequest(timestamp=timestamp)
        )
        self._send_queue.put(msg)
        return timestamp

    async def _get_http_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._http_session is None or self._http_session.closed:
            timeout = aiohttp.ClientTimeout(total=30.0)
            self._http_session = aiohttp.ClientSession(timeout=timeout)
        return self._http_session

    async def close_async(self):
        """Close async HTTP session."""
        if self._http_session and not self._http_session.closed:
            await self._http_session.close()

    def close(self) -> None:
        """Close the gateway connection."""
        self._running = False

        if self.channel:
            try:
                self.channel.close()
            except Exception:
                pass
            self.channel = None

        self.stream = None
        self.stub = None
        self.connection_id = None
        self.subscribed_topics = []
        logger.info("gRPC gateway connection closed")

    # HTTP Proxy Methods (Sync - for registration)

    def http_post(self, service: str, path: str, **kwargs) -> requests.Response:
        """
        Make a sync POST request (used for registration).

        Args:
            service: Service name ("ai-inventory" or "conversation-store")
            path: Request path
            **kwargs: Additional arguments passed to requests.post

        Returns:
            Response object
        """
        url = f"{self.http_url}/s/{service}{path}"
        return requests.post(url, **kwargs)

    # HTTP Proxy Methods (Async - for runtime)

    async def http_get_async(self, service: str, path: str, **kwargs):
        """
        Make an async GET request to a service via the gateway proxy.

        Args:
            service: Service name ("ai-inventory" or "conversation-store")
            path: Request path
            **kwargs: Additional arguments passed to aiohttp

        Returns:
            Response object
        """
        url = f"{self.http_url}/s/{service}{path}"
        session = await self._get_http_session()
        async with session.get(url, **kwargs) as response:
            response.raise_for_status()
            return response

    async def http_post_async(self, service: str, path: str, **kwargs):
        """
        Make an async POST request to a service via the gateway proxy.

        Args:
            service: Service name ("ai-inventory" or "conversation-store")
            path: Request path
            **kwargs: Additional arguments passed to aiohttp

        Returns:
            Response object
        """
        url = f"{self.http_url}/s/{service}{path}"
        session = await self._get_http_session()
        async with session.post(url, **kwargs) as response:
            response.raise_for_status()
            return response

    async def http_patch_async(self, service: str, path: str, **kwargs):
        """
        Make an async PATCH request to a service via the gateway proxy.

        Args:
            service: Service name ("ai-inventory" or "conversation-store")
            path: Request path
            **kwargs: Additional arguments passed to aiohttp

        Returns:
            Response object
        """
        url = f"{self.http_url}/s/{service}{path}"
        session = await self._get_http_session()
        async with session.patch(url, **kwargs) as response:
            response.raise_for_status()
            return response

    async def http_delete_async(self, service: str, path: str, **kwargs):
        """
        Make an async DELETE request to a service via the gateway proxy.

        Args:
            service: Service name ("ai-inventory" or "conversation-store")
            path: Request path
            **kwargs: Additional arguments passed to aiohttp

        Returns:
            Response object
        """
        url = f"{self.http_url}/s/{service}{path}"
        session = await self._get_http_session()
        async with session.delete(url, **kwargs) as response:
            response.raise_for_status()
            return response


class GatewayError(Exception):
    """Base exception for gateway errors."""
    pass


class AuthenticationError(GatewayError):
    """Raised when authentication fails."""
    pass

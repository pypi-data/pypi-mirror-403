"""Main application class for March AI Agent framework (async)."""

import asyncio
import logging
import signal
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any, List, Set

from .agent import Agent
from .gateway_client import GatewayClient
from .conversation_client import ConversationClient
from .memory_client import MemoryClient
from .attachment_client import AttachmentClient
from .exceptions import RegistrationError, ConfigurationError

logger = logging.getLogger(__name__)


class MarchAgentApp:
    """
    Main application class for March AI Agent framework.

    Example:
        from march_agent import MarchAgentApp

        app = MarchAgentApp(
            gateway_url="agent-gateway:8080",
            api_key="agent-key-1"
        )

        # Register agents
        medical_agent = app.register_me(
            name="medical-qa-agent",
            about="Medical Q&A",
            document="Answers medical questions"
        )

        @medical_agent.on_message
        def handle_message(message, sender):
            # Access conversation history
            history = message.conversation.get_history(limit=5)

            # Stream response
            with medical_agent.streamer(message) as s:
                s.stream("Processing...")
                s.stream("Done!")

        app.run()
    """

    def __init__(
        self,
        gateway_url: str,
        api_key: str,
        heartbeat_interval: int = 60,
        max_concurrent_tasks: int = 100,
        error_message_template: str = (
            "I encountered an error while processing your message. "
            "Please try again or contact support if the issue persists."
        ),
        secure: bool = False,
        enable_remote_logging: bool = False,
        remote_log_level: int = logging.INFO,
        remote_log_batch_size: int = 100,
        remote_log_flush_interval: float = 5.0,
    ):
        """
        Initialize March Agent App.

        Args:
            gateway_url: Gateway endpoint (e.g., "agent-gateway:8080")
            api_key: API key for gateway authentication
            heartbeat_interval: Heartbeat interval in seconds
            max_concurrent_tasks: Maximum number of concurrent message handlers (default: 100)
            error_message_template: Template for error messages sent to users
            secure: If True, use TLS for gRPC and HTTPS for HTTP requests
            enable_remote_logging: Send logs to Loki via gateway (default: False)
            remote_log_level: Minimum log level for remote logging (default: INFO)
            remote_log_batch_size: Logs per batch (default: 100)
            remote_log_flush_interval: Seconds between flushes (default: 5.0)
        """
        self.gateway_url = gateway_url
        self.api_key = api_key
        self.heartbeat_interval = heartbeat_interval
        self.max_concurrent_tasks = max_concurrent_tasks
        self.error_message_template = error_message_template
        self.secure = secure

        # Create gateway client
        self.gateway_client = GatewayClient(gateway_url, api_key, secure=secure)

        # Create conversation client using gateway proxy
        self.conversation_client = ConversationClient(
            self.gateway_client.conversation_store_url
        )

        # Create memory client using gateway proxy
        self.memory_client = MemoryClient(
            self.gateway_client.ai_memory_url
        )

        # Create attachment client using gateway proxy
        self.attachment_client = AttachmentClient(
            self.gateway_client.attachment_url
        )

        self._agents: List[Agent] = []
        self._running = False
        self._connected = False
        self._active_tasks: Set[asyncio.Task] = set()
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="consume")
        self._task_start_times: Dict[asyncio.Task, float] = {}
        self._hung_task_threshold = 300.0  # 5 minutes

        # Remote logging setup
        self._loki_handler: Optional[Any] = None
        self._pending_remote_logging: Optional[dict] = None

        if enable_remote_logging:
            self._pending_remote_logging = {
                "log_level": remote_log_level,
                "batch_size": remote_log_batch_size,
                "flush_interval": remote_log_flush_interval,
            }
            logger.info("Remote logging will be enabled after agent registration")

        logger.info(f"MarchAgentApp initialized (gateway: {gateway_url}, max_concurrent: {max_concurrent_tasks})")

    def register_me(
        self,
        name: str,
        about: str,
        document: str,
        representation_name: Optional[str] = None,
        base_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        related_pages: Optional[List[Dict[str, str]]] = None,
        category_name: Optional[str] = None,
        tag_names: Optional[List[str]] = None,
        example_prompts: Optional[List[str]] = None,
        is_experimental: Optional[bool] = None,
        force_update: Optional[bool] = None,
    ) -> Agent:
        """
        Register an agent with the backend.

        Example:
            medical_agent = app.register_me(
                name="medical-qa",
                about="Medical question answering",
                document="Answers medical questions using AI",
                representation_name="Medical Q&A Bot",
                base_url="http://my-agent-frontend:3000",
                related_pages=[
                    {"name": "Dashboard", "endpoint": "/dashboard"},
                    {"name": "Reports", "endpoint": "/reports"},
                ]
            )

            @medical_agent.on_message
            def handle_message(message, sender):
                with medical_agent.streamer(message) as s:
                    s.stream("Processing...")

        Args:
            name: Unique agent name (used for routing)
            about: Short description
            document: Detailed documentation
            representation_name: Display name (optional)
            base_url: Base URL for agent's frontend service (optional)
                      Used for iframe artifact URLs
            metadata: Additional metadata (optional)
            related_pages: List of related pages with 'name' and 'endpoint' keys (optional)
                          Example: [{"name": "Dashboard", "endpoint": "/dashboard"}]
            category_name: Category for the agent in kebab-case (optional, auto-created if needed)
            tag_names: List of tags in kebab-case (optional, auto-created if needed)
            example_prompts: List of example prompts for users (optional)
            is_experimental: Whether the agent is experimental (optional, defaults to false)
            force_update: Bypass content hash check and force update (optional, defaults to false)

        Returns:
            Agent instance
        """
        # Register agent with backend via gateway proxy
        logger.info(f"Registering agent '{name}'...")

        payload = {
            "name": name,
            "about": about,
            "document": document,
            "representationName": representation_name or name,
        }
        if base_url:
            payload["baseUrl"] = base_url
        if metadata:
            payload["metadata"] = metadata
        if related_pages:
            payload["relatedPages"] = related_pages
        if category_name:
            payload["categoryName"] = category_name
        if tag_names:
            payload["tagNames"] = tag_names
        if example_prompts:
            payload["examplePrompts"] = example_prompts
        if is_experimental is not None:
            payload["isExperimental"] = is_experimental
        if force_update is not None:
            payload["forceUpdate"] = force_update

        try:
            response = self.gateway_client.http_post(
                "ai-inventory",
                "/api/v1/agents/register",
                json=payload,
                timeout=30
            )
            if response.status_code == 201:
                agent_data = response.json()
                logger.info(f"Agent '{name}' registered successfully")
            else:
                raise RegistrationError(f"Registration failed: {response.text}")
        except Exception as e:
            raise RegistrationError(f"Failed to register agent '{name}': {e}")

        # Set up remote logging now that we have agent name
        if self._pending_remote_logging and not self._loki_handler:
            from .loki_handler import LokiLogHandler

            config = self._pending_remote_logging
            self._loki_handler = LokiLogHandler(
                gateway_client=self.gateway_client,
                agent_name=name,
                batch_size=config["batch_size"],
                flush_interval=config["flush_interval"],
                level=config["log_level"],
            )

            # Add to root logger to capture all logs
            logging.getLogger().addHandler(self._loki_handler)
            logger.info(f"Remote logging enabled for agent '{name}'")

            # Clear pending config
            self._pending_remote_logging = None

        # Create agent instance
        agent = Agent(
            name=name,
            gateway_client=self.gateway_client,
            agent_data=agent_data,
            heartbeat_interval=self.heartbeat_interval,
            conversation_client=self.conversation_client,
            memory_client=self.memory_client,
            attachment_client=self.attachment_client,
            error_message_template=self.error_message_template,
        )

        self._agents.append(agent)
        logger.info(f"Agent '{name}' ready")

        return agent

    def run(self):
        """Start all registered agents and block until shutdown."""
        if not self._agents:
            raise ConfigurationError(
                "No agents registered. Use app.register_me() to register agents."
            )

        logger.info(f"Starting {len(self._agents)} agent(s)...")
        self._running = True

        # Connect to gateway with all agent names
        agent_names = [agent.name for agent in self._agents]
        try:
            self.gateway_client.connect(agent_names)
            self._connected = True
        except Exception as e:
            raise ConfigurationError(f"Failed to connect to gateway: {e}")

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._shutdown_handler)
        signal.signal(signal.SIGTERM, self._shutdown_handler)

        # Initialize all agents with the connected gateway
        for agent in self._agents:
            agent._initialize_with_gateway()

        # Start all agents in background threads (they just stay alive)
        threads = []
        for agent in self._agents:
            thread = threading.Thread(target=agent.start_consuming, daemon=True)
            thread.start()
            threads.append(thread)

        logger.info("All agents started. Press Ctrl+C to stop.")

        # Run the single consume loop in the main thread
        try:
            self._consume_loop()
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self._shutdown()

    def _consume_loop(self):
        """Main consume loop that dispatches messages to agents concurrently."""
        # Run the async consume loop
        asyncio.run(self._consume_loop_async())

    async def _consume_loop_async(self):
        """Async consume loop with concurrent message processing."""
        # Build topic -> agent mapping
        topic_to_agent = {
            f"{agent.name}.inbox": agent for agent in self._agents
        }

        logger.info(
            f"Starting consume loop for topics: {list(topic_to_agent.keys())} "
            f"(max_concurrent: {self.max_concurrent_tasks})"
        )

        loop = asyncio.get_event_loop()

        try:
            while self._running:
                try:
                    # Run sync consume_one in executor to not block the event loop
                    msg = await loop.run_in_executor(
                        self._executor,
                        lambda: self.gateway_client.consume_one(timeout=0.5)
                    )

                    if msg:
                        agent = topic_to_agent.get(msg.topic)
                        if agent:
                            # Wait if we've hit max concurrency
                            while len(self._active_tasks) >= self.max_concurrent_tasks:
                                if not self._active_tasks:
                                    break

                                # Wait with timeout to detect hung tasks
                                done, self._active_tasks = await asyncio.wait(
                                    self._active_tasks,
                                    return_when=asyncio.FIRST_COMPLETED,
                                    timeout=30.0  # 30 second timeout
                                )

                                # Check for errors in completed tasks
                                for task in done:
                                    self._task_start_times.pop(task, None)
                                    if task.exception():
                                        logger.error(
                                            f"Task failed with exception: {task.exception()}"
                                        )

                                # If timeout with no completions, check for hung tasks
                                if not done:
                                    current_time = time.time()
                                    hung_tasks = [
                                        task for task in self._active_tasks
                                        if current_time - self._task_start_times.get(task, current_time) > self._hung_task_threshold
                                    ]

                                    if hung_tasks:
                                        logger.error(
                                            f"Detected {len(hung_tasks)} hung tasks (>{self._hung_task_threshold}s). "
                                            f"Total active: {len(self._active_tasks)}"
                                        )
                                        # Optional: cancel hung tasks
                                        # for task in hung_tasks:
                                        #     task.cancel()
                                        #     self._task_start_times.pop(task, None)
                                    else:
                                        logger.warning(
                                            f"No tasks completed in 30s. Active tasks: {len(self._active_tasks)} "
                                            f"(may indicate slow handlers or blocking code)"
                                        )

                            # Create task for concurrent processing
                            task = asyncio.create_task(
                                self._handle_message_safe(agent, msg)
                            )
                            self._active_tasks.add(task)
                            self._task_start_times[task] = time.time()
                            # Auto-remove from set when done
                            task.add_done_callback(self._active_tasks.discard)

                            logger.debug(
                                f"Dispatched message to {agent.name}, "
                                f"active tasks: {len(self._active_tasks)}"
                            )
                        else:
                            logger.warning(f"No agent for topic: {msg.topic}")

                except Exception as e:
                    if self._running:
                        logger.error(f"Error in consume loop: {e}")
                        # Try to reconnect if connection lost
                        await asyncio.sleep(1.0)
                        try:
                            self._reconnect()
                        except Exception as re:
                            logger.error(f"Reconnect failed: {re}")
                            await asyncio.sleep(5.0)

        finally:
            # Wait for all active tasks to complete on shutdown
            if self._active_tasks:
                logger.info(
                    f"Waiting for {len(self._active_tasks)} active tasks to complete..."
                )
                await asyncio.gather(*self._active_tasks, return_exceptions=True)
                logger.info("All tasks completed")

    async def _handle_message_safe(self, agent: Agent, msg) -> None:
        """Wrapper that handles errors from message handlers gracefully."""
        try:
            await agent._handle_message_async(msg)
        except Exception as e:
            logger.error(
                f"Error handling message for {agent.name}: {e}",
                exc_info=True
            )

    def _reconnect(self):
        """Attempt to reconnect to the gateway."""
        logger.info("Attempting to reconnect to gateway...")
        agent_names = [agent.name for agent in self._agents]
        self.gateway_client.close()
        self.gateway_client.connect(agent_names)
        logger.info("Reconnected to gateway successfully")

    def _shutdown_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self._running = False

    def _shutdown(self):
        """Shutdown all agents gracefully."""
        logger.info("Shutting down all agents...")
        self._running = False

        # Shutdown the executor
        try:
            self._executor.shutdown(wait=False)
        except Exception as e:
            logger.error(f"Error shutting down executor: {e}")

        # Close async sessions - need to create a new loop since asyncio.run closed its loop
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._close_async_sessions())
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Error closing async sessions: {e}")

        for agent in self._agents:
            try:
                agent.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down agent {agent.name}: {e}")

        # Close Loki handler
        if self._loki_handler:
            try:
                logger.info("Flushing and closing remote logging handler...")
                self._loki_handler.close()
            except Exception as e:
                logger.error(f"Error closing Loki handler: {e}")

        # Close gateway connection
        if self._connected:
            self.gateway_client.close()

        logger.info("All agents shut down successfully")

    async def _close_async_sessions(self):
        """Close all async HTTP sessions."""
        try:
            await self.gateway_client.close_async()
        except Exception as e:
            logger.error(f"Error closing gateway async session: {e}")

        try:
            await self.conversation_client.close()
        except Exception as e:
            logger.error(f"Error closing conversation client: {e}")

        try:
            await self.memory_client.close()
        except Exception as e:
            logger.error(f"Error closing memory client: {e}")

        try:
            await self.attachment_client.close()
        except Exception as e:
            logger.error(f"Error closing attachment client: {e}")

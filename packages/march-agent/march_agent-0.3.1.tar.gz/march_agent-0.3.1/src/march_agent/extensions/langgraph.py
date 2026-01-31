"""LangGraph extension for march_agent.

This module provides LangGraph-compatible components that integrate with
the march_agent framework.

Usage:
    from march_agent.extensions.langgraph import HTTPCheckpointSaver

    app = MarchAgentApp(gateway_url="agent-gateway:8080", api_key="key")
    checkpointer = HTTPCheckpointSaver(app=app)

    graph = StateGraph(...)
    compiled = graph.compile(checkpointer=checkpointer)
"""

from __future__ import annotations

import asyncio
import base64
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Dict,
    Iterator,
    Optional,
    Sequence,
    Set,
    Tuple,
)

if TYPE_CHECKING:
    from ..app import MarchAgentApp

logger = logging.getLogger(__name__)

# Try to import LangGraph types, but make them optional
try:
    from langgraph.checkpoint.base import (
        BaseCheckpointSaver,
        ChannelVersions,
        Checkpoint,
        CheckpointMetadata,
        CheckpointTuple,
    )
    from langchain_core.runnables import RunnableConfig

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    # Define stub types for when langgraph is not installed
    BaseCheckpointSaver = object
    RunnableConfig = Dict[str, Any]
    Checkpoint = Dict[str, Any]
    CheckpointMetadata = Dict[str, Any]
    CheckpointTuple = Tuple[Any, ...]
    ChannelVersions = Dict[str, Any]

from ..checkpoint_client import CheckpointClient
from ..exceptions import APIException


def _generate_checkpoint_id() -> str:
    """Generate a unique checkpoint ID based on timestamp."""
    return datetime.now(timezone.utc).isoformat()


class HTTPCheckpointSaver(BaseCheckpointSaver if LANGGRAPH_AVAILABLE else object):
    """HTTP-based checkpoint saver for LangGraph.

    This checkpointer stores graph state via HTTP calls to the conversation-store
    checkpoint API, enabling distributed checkpoint storage without direct
    database access.

    Example:
        ```python
        from march_agent import MarchAgentApp
        from march_agent.extensions.langgraph import HTTPCheckpointSaver
        from langgraph.graph import StateGraph

        app = MarchAgentApp(gateway_url="agent-gateway:8080", api_key="key")
        checkpointer = HTTPCheckpointSaver(app=app)

        graph = StateGraph(MyState)
        # ... define graph ...
        compiled = graph.compile(checkpointer=checkpointer)

        config = {"configurable": {"thread_id": "my-thread"}}
        result = compiled.invoke({"messages": [...]}, config)
        ```
    """

    def __init__(
        self,
        app: "MarchAgentApp",
        *,
        serde: Optional[Any] = None,
    ):
        """Initialize HTTP checkpoint saver.

        Args:
            app: MarchAgentApp instance to get the gateway client from.
            serde: Optional serializer/deserializer (for LangGraph compatibility)
        """
        if LANGGRAPH_AVAILABLE:
            super().__init__(serde=serde)

        base_url = app.gateway_client.conversation_store_url
        self.client = CheckpointClient(base_url)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="checkpoint")

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create an event loop for sync operations."""
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            if self._loop is None or self._loop.is_closed():
                self._loop = asyncio.new_event_loop()
            return self._loop

    async def close(self):
        """Close the HTTP client session and executor."""
        await self.client.close()
        self._executor.shutdown(wait=True)

    # ==================== Config Helpers ====================

    @staticmethod
    def _get_thread_id(config: RunnableConfig) -> str:
        """Extract thread_id from config."""
        configurable = config.get("configurable", {})
        thread_id = configurable.get("thread_id")
        if not thread_id:
            raise ValueError("Config must contain configurable.thread_id")
        return thread_id

    @staticmethod
    def _get_checkpoint_ns(config: RunnableConfig) -> str:
        """Extract checkpoint_ns from config (defaults to empty string)."""
        return config.get("configurable", {}).get("checkpoint_ns", "")

    @staticmethod
    def _get_checkpoint_id(config: RunnableConfig) -> Optional[str]:
        """Extract checkpoint_id from config."""
        return config.get("configurable", {}).get("checkpoint_id")

    # ==================== Async Methods (Primary Implementation) ====================

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Fetch a checkpoint tuple asynchronously."""
        thread_id = self._get_thread_id(config)
        checkpoint_ns = self._get_checkpoint_ns(config)
        checkpoint_id = self._get_checkpoint_id(config)

        try:
            result = await self.client.get_tuple(
                thread_id=thread_id,
                checkpoint_ns=checkpoint_ns,
                checkpoint_id=checkpoint_id,
            )
        except APIException as e:
            logger.error(f"Failed to get checkpoint: {e}")
            return None

        if not result:
            return None

        return self._response_to_tuple(result)

    async def alist(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """List checkpoints asynchronously."""
        thread_id = None
        checkpoint_ns = None

        if config:
            thread_id = config.get("configurable", {}).get("thread_id")
            checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns")

        before_id = None
        if before:
            before_id = before.get("configurable", {}).get("checkpoint_id")

        try:
            results = await self.client.list(
                thread_id=thread_id,
                checkpoint_ns=checkpoint_ns,
                before=before_id,
                limit=limit,
            )
        except APIException as e:
            logger.error(f"Failed to list checkpoints: {e}")
            return

        for result in results:
            tuple_result = self._response_to_tuple(result)
            if tuple_result:
                yield tuple_result

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Store a checkpoint asynchronously."""
        thread_id = self._get_thread_id(config)
        checkpoint_ns = self._get_checkpoint_ns(config)

        checkpoint_id = self._get_checkpoint_id(config)
        if not checkpoint_id:
            checkpoint_id = checkpoint.get("id", _generate_checkpoint_id())

        api_config = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint_id,
            }
        }

        checkpoint_data = self._checkpoint_to_api(checkpoint)
        metadata_data = self._metadata_to_api(metadata)

        try:
            result = await self.client.put(
                config=api_config,
                checkpoint=checkpoint_data,
                metadata=metadata_data,
                new_versions=dict(new_versions) if new_versions else {},
            )
        except APIException as e:
            logger.error(f"Failed to store checkpoint: {e}")
            raise

        return result.get("config", api_config)

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """Store intermediate writes asynchronously (stub)."""
        logger.debug(
            f"aput_writes called (not persisted): task_id={task_id}, "
            f"writes_count={len(writes)}"
        )

    async def adelete_thread(self, thread_id: str) -> None:
        """Delete all checkpoints for a thread asynchronously."""
        try:
            await self.client.delete_thread(thread_id)
        except APIException as e:
            logger.error(f"Failed to delete thread checkpoints: {e}")
            raise

    # ==================== Sync Methods (Wrappers) ====================

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Fetch a checkpoint tuple synchronously (thread-safe)."""
        return self._executor.submit(asyncio.run, self.aget_tuple(config)).result()

    def list(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        """List checkpoints synchronously (thread-safe)."""

        async def collect():
            results = []
            async for item in self.alist(config, filter=filter, before=before, limit=limit):
                results.append(item)
            return results

        results = self._executor.submit(asyncio.run, collect()).result()
        yield from results

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Store a checkpoint synchronously (thread-safe)."""
        return self._executor.submit(
            asyncio.run,
            self.aput(config, checkpoint, metadata, new_versions)
        ).result()

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """Store intermediate writes synchronously (thread-safe)."""
        self._executor.submit(
            asyncio.run,
            self.aput_writes(config, writes, task_id, task_path)
        ).result()

    def delete_thread(self, thread_id: str) -> None:
        """Delete all checkpoints for a thread synchronously (thread-safe)."""
        self._executor.submit(asyncio.run, self.adelete_thread(thread_id)).result()

    # ==================== Data Conversion Helpers ====================

    def _serialize_value(
        self,
        value: Any,
        _visited: Optional[Set[int]] = None,
        _depth: int = 0
    ) -> Any:
        """Serialize a value for JSON transmission with cycle detection.

        Args:
            value: Value to serialize
            _visited: Set of visited object IDs (for cycle detection)
            _depth: Current recursion depth (for depth limit)

        Returns:
            Serialized value safe for JSON
        """
        # Initialize visited set on first call
        if _visited is None:
            _visited = set()

        # Depth protection (prevent stack overflow)
        MAX_DEPTH = 100
        if _depth > MAX_DEPTH:
            logger.warning(
                f"Serialization depth limit reached ({MAX_DEPTH}). "
                "Returning placeholder."
            )
            return {"__max_depth_exceeded__": True}

        # Handle bytes (before cycle check, as bytes are immutable)
        if isinstance(value, bytes):
            return {"__bytes__": base64.b64encode(value).decode("ascii")}

        # Cycle detection for container types
        if isinstance(value, (dict, list, tuple)):
            obj_id = id(value)
            if obj_id in _visited:
                logger.warning(
                    "Circular reference detected during serialization. "
                    "Returning placeholder."
                )
                return {"__circular_ref__": True}

            # Mark as visited
            _visited.add(obj_id)

            try:
                # Serialize based on type
                if isinstance(value, dict):
                    return {
                        k: self._serialize_value(v, _visited, _depth + 1)
                        for k, v in value.items()
                    }

                if isinstance(value, list):
                    return [
                        self._serialize_value(item, _visited, _depth + 1)
                        for item in value
                    ]

                if isinstance(value, tuple):
                    return {
                        "__tuple__": [
                            self._serialize_value(item, _visited, _depth + 1)
                            for item in value
                        ]
                    }
            finally:
                # Remove from visited after processing
                # This allows same object in different branches (DAG structure)
                _visited.discard(obj_id)

        # Handle custom serialization with serde
        if LANGGRAPH_AVAILABLE and hasattr(self, "serde") and self.serde is not None:
            try:
                type_str, serialized = self.serde.dumps_typed(value)
                if isinstance(serialized, bytes):
                    serialized = base64.b64encode(serialized).decode("ascii")
                return {"__serde_type__": type_str, "__serde_value__": serialized}
            except Exception as e:
                logger.warning(f"Failed to serialize value with serde: {e}")

        # Handle objects with serialization methods
        if hasattr(value, "model_dump"):
            return self._serialize_value(value.model_dump(), _visited, _depth + 1)
        if hasattr(value, "dict"):
            return self._serialize_value(value.dict(), _visited, _depth + 1)
        if hasattr(value, "to_dict"):
            return self._serialize_value(value.to_dict(), _visited, _depth + 1)

        # Return primitives as-is
        return value

    def _serialize_channel_values(self, channel_values: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize all channel values for API transmission."""
        return self._serialize_value(channel_values)

    def _deserialize_value(self, value: Any) -> Any:
        """Deserialize a value, decoding base64 bytes and reconstructing tuples."""
        if isinstance(value, dict):
            if "__bytes__" in value:
                return base64.b64decode(value["__bytes__"])
            if "__tuple__" in value:
                return tuple(self._deserialize_value(item) for item in value["__tuple__"])
            if "__serde_type__" in value and "__serde_value__" in value:
                if LANGGRAPH_AVAILABLE and hasattr(self, "serde") and self.serde is not None:
                    try:
                        serialized = value["__serde_value__"]
                        if isinstance(serialized, str):
                            serialized = base64.b64decode(serialized)
                        return self.serde.loads_typed((value["__serde_type__"], serialized))
                    except Exception as e:
                        logger.warning(f"Failed to deserialize value with serde: {e}")
                return value
            return {k: self._deserialize_value(v) for k, v in value.items()}

        if isinstance(value, list):
            return [self._deserialize_value(item) for item in value]

        return value

    def _deserialize_checkpoint(self, checkpoint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize checkpoint data received from API."""
        if not checkpoint_data:
            return checkpoint_data

        result = dict(checkpoint_data)
        if "channel_values" in result:
            result["channel_values"] = self._deserialize_value(result["channel_values"])
        return result

    def _checkpoint_to_api(self, checkpoint: Checkpoint) -> Dict[str, Any]:
        """Convert LangGraph Checkpoint to API format."""
        if isinstance(checkpoint, dict):
            channel_values = checkpoint.get("channel_values", {})
            return {
                "v": checkpoint.get("v", 1),
                "id": checkpoint.get("id", _generate_checkpoint_id()),
                "ts": checkpoint.get("ts", datetime.now(timezone.utc).isoformat()),
                "channel_values": self._serialize_channel_values(channel_values),
                "channel_versions": checkpoint.get("channel_versions", {}),
                "versions_seen": checkpoint.get("versions_seen", {}),
                "pending_sends": checkpoint.get("pending_sends", []),
            }
        channel_values = dict(getattr(checkpoint, "channel_values", {}))
        return {
            "v": getattr(checkpoint, "v", 1),
            "id": getattr(checkpoint, "id", _generate_checkpoint_id()),
            "ts": getattr(checkpoint, "ts", datetime.now(timezone.utc).isoformat()),
            "channel_values": self._serialize_channel_values(channel_values),
            "channel_versions": dict(getattr(checkpoint, "channel_versions", {})),
            "versions_seen": dict(getattr(checkpoint, "versions_seen", {})),
            "pending_sends": list(getattr(checkpoint, "pending_sends", [])),
        }

    def _serialize_writes(self, writes: Any) -> Any:
        """Serialize writes field which may contain LangChain objects."""
        if writes is None:
            return None
        return self._serialize_value(writes)

    def _metadata_to_api(self, metadata: CheckpointMetadata) -> Dict[str, Any]:
        """Convert LangGraph CheckpointMetadata to API format."""
        if isinstance(metadata, dict):
            return {
                "source": metadata.get("source", "input"),
                "step": metadata.get("step", -1),
                "writes": self._serialize_writes(metadata.get("writes")),
                "parents": metadata.get("parents", {}),
            }
        return {
            "source": getattr(metadata, "source", "input"),
            "step": getattr(metadata, "step", -1),
            "writes": self._serialize_writes(getattr(metadata, "writes", None)),
            "parents": dict(getattr(metadata, "parents", {})),
        }

    def _response_to_tuple(self, response: Dict[str, Any]) -> Optional[CheckpointTuple]:
        """Convert API response to LangGraph CheckpointTuple."""
        if not response:
            return None

        config = response.get("config", {})
        checkpoint_data = response.get("checkpoint", {})
        metadata_data = response.get("metadata", {})
        parent_config = response.get("parent_config")
        pending_writes = response.get("pending_writes")

        checkpoint_data = self._deserialize_checkpoint(checkpoint_data)

        if not LANGGRAPH_AVAILABLE:
            return (config, checkpoint_data, metadata_data, parent_config, pending_writes)

        return CheckpointTuple(
            config=config,
            checkpoint=checkpoint_data,
            metadata=metadata_data,
            parent_config=parent_config,
            pending_writes=pending_writes or [],
        )

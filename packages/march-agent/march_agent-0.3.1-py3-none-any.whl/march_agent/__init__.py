"""March AI Agent SDK - Synchronous Python framework for building AI agents."""

__version__ = "0.3.0"

from .app import MarchAgentApp
from .agent import Agent
from .message import Message
from .conversation import Conversation
from .conversation_client import ConversationClient
from .conversation_message import ConversationMessage
from .checkpoint_client import CheckpointClient
from .memory import Memory
from .memory_client import (
    MemoryClient,
    MemoryMessage,
    MemorySearchResult,
    UserSummary,
)
from .attachment_client import AttachmentClient, AttachmentInfo
from .streamer import Streamer
from .structural import Artifact, Surface, TextBlock, Stepper
from .loki_handler import LokiLogHandler
from .exceptions import (
    MarchAgentError,
    RegistrationError,
    KafkaError,
    ConfigurationError,
    APIException,
    HeartbeatError,
)

__all__ = [
    "MarchAgentApp",
    "Agent",
    "Message",
    "Conversation",
    "ConversationClient",
    "ConversationMessage",
    "CheckpointClient",
    "Memory",
    "MemoryClient",
    "MemoryMessage",
    "MemorySearchResult",
    "UserSummary",
    "AttachmentClient",
    "AttachmentInfo",
    "Streamer",
    "Artifact",
    "Surface",
    "TextBlock",
    "Stepper",
    "LokiLogHandler",
    "MarchAgentError",
    "RegistrationError",
    "KafkaError",
    "ConfigurationError",
    "APIException",
    "HeartbeatError",
]

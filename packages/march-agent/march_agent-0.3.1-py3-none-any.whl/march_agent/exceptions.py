"""Custom exceptions for March AI Agent framework."""


class MarchAgentError(Exception):
    """Base exception for all March Agent errors."""
    pass


class RegistrationError(MarchAgentError):
    """Raised when agent registration fails."""
    pass


class KafkaError(MarchAgentError):
    """Raised when Kafka operations fail."""
    pass


class HeartbeatError(MarchAgentError):
    """Raised when heartbeat operations fail."""
    pass


class MessageHandlerError(MarchAgentError):
    """Raised when message handler execution fails."""
    pass


class ConfigurationError(MarchAgentError):
    """Raised when configuration is invalid."""
    pass


class APIException(MarchAgentError):
    """Raised when conversation-store API requests fail."""
    pass

"""Typed message from conversation-store."""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List


@dataclass
class ConversationMessage:
    """A message from conversation-store.

    Represents a stored message in a conversation with full metadata.
    """

    id: str
    conversation_id: str
    role: str  # "user", "assistant", "system"
    content: str
    sequence_number: int
    from_: Optional[str] = None  # Sender (agent name or "user")
    to_: Optional[str] = None  # Recipient
    metadata: Optional[Dict[str, Any]] = None
    schema: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationMessage":
        """Create from conversation-store API response."""
        return cls(
            id=str(data.get("id", "")),
            conversation_id=str(data.get("conversation_id", "")),
            role=data.get("role", ""),
            content=data.get("content", ""),
            sequence_number=data.get("sequence_number", 0),
            from_=data.get("from_"),
            to_=data.get("to_"),
            metadata=data.get("metadata"),
            schema=data.get("schema"),
            response_schema=data.get("response_schema"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    @classmethod
    def from_list(cls, data: List[Dict[str, Any]]) -> List["ConversationMessage"]:
        """Create list from conversation-store API response."""
        return [cls.from_dict(item) for item in data]

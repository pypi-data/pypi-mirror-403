"""Message data structure."""

import json
from dataclasses import dataclass, field
from io import BytesIO
from typing import Dict, Any, Optional, TYPE_CHECKING

from .conversation import Conversation
from .conversation_client import ConversationClient

if TYPE_CHECKING:
    from .memory import Memory
    from .memory_client import MemoryClient
    from .attachment_client import AttachmentClient, AttachmentInfo


@dataclass
class Message:
    """Represents an incoming message."""

    content: str
    conversation_id: str
    user_id: str
    headers: Dict[str, str]
    raw_body: Dict[str, Any]
    conversation: Optional[Conversation] = None
    memory: Optional["Memory"] = None
    metadata: Optional[Dict[str, Any]] = None
    schema: Optional[Dict[str, Any]] = None
    attachment: Optional["AttachmentInfo"] = None
    _attachment_client: Optional["AttachmentClient"] = field(default=None, repr=False)

    @classmethod
    def from_kafka_message(
        cls,
        body: Dict[str, Any],
        headers: Dict[str, str],
        conversation_client: Optional[ConversationClient] = None,
        memory_client: Optional["MemoryClient"] = None,
        attachment_client: Optional["AttachmentClient"] = None,
        agent_name: Optional[str] = None,
    ):
        """Create Message from Kafka message."""
        from .memory import Memory
        from .attachment_client import AttachmentInfo

        conversation_id = headers.get("conversationId")
        user_id = headers.get("userId", "anonymous")

        # Parse metadata from header
        metadata = None
        metadata_header = headers.get("messageMetadata")
        if metadata_header:
            try:
                metadata = json.loads(metadata_header)
            except json.JSONDecodeError:
                pass

        # Parse schema from header
        schema = None
        schema_header = headers.get("messageSchema")
        if schema_header:
            try:
                schema = json.loads(schema_header)
            except json.JSONDecodeError:
                pass

        # Parse attachment from header or body
        attachment = None
        attachment_header = headers.get("attachment")
        if attachment_header:
            try:
                attachment_data = json.loads(attachment_header)
                attachment = AttachmentInfo.from_dict(attachment_data)
            except json.JSONDecodeError:
                pass
        # Also check body for attachment (fallback)
        if not attachment and body.get("attachment"):
            attachment = AttachmentInfo.from_dict(body["attachment"])

        conversation = None
        if conversation_id and conversation_client:
            conversation = Conversation(conversation_id, conversation_client, agent_name)

        memory = None
        if memory_client and user_id and conversation_id:
            memory = Memory(user_id, conversation_id, memory_client)

        return cls(
            content=body.get("content", ""),
            conversation_id=conversation_id,
            user_id=user_id,
            headers=headers,
            raw_body=body,
            conversation=conversation,
            memory=memory,
            metadata=metadata,
            schema=schema,
            attachment=attachment,
            _attachment_client=attachment_client,
        )

    def has_attachment(self) -> bool:
        """Check if message has an attachment."""
        return self.attachment is not None

    async def get_attachment_bytes(self) -> bytes:
        """
        Download attachment into memory as bytes.

        Returns:
            File content as bytes

        Raises:
            ValueError: If no attachment is available
        """
        if not self.attachment:
            raise ValueError("No attachment available")
        if not self._attachment_client:
            raise ValueError("AttachmentClient not available")
        return await self._attachment_client.download(self.attachment.url)

    async def get_attachment_base64(self) -> str:
        """
        Get attachment as base64 string (for LLM vision APIs).

        Returns:
            Base64 encoded string of the file content

        Raises:
            ValueError: If no attachment is available
        """
        if not self.attachment:
            raise ValueError("No attachment available")
        if not self._attachment_client:
            raise ValueError("AttachmentClient not available")
        return await self._attachment_client.download_as_base64(self.attachment.url)

    async def get_attachment_buffer(self) -> BytesIO:
        """
        Get attachment as BytesIO buffer (for document processing libraries).

        Returns:
            BytesIO buffer containing the file content

        Raises:
            ValueError: If no attachment is available
        """
        if not self.attachment:
            raise ValueError("No attachment available")
        if not self._attachment_client:
            raise ValueError("AttachmentClient not available")
        return await self._attachment_client.download_to_buffer(self.attachment.url)

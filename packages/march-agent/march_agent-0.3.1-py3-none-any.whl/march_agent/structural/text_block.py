"""TextBlock structural streamer for collapsible text content."""

from typing import Optional
from .base import StructuralStreamer
import uuid


class TextBlock(StructuralStreamer):
    """Manages collapsible text block with title and body.

    Both title and body support streaming (append) and update (replace).
    TextBlock events are NOT persisted to database.

    Example:
        block = TextBlock()  # ID auto-generated
        s.stream_by(block).set_variant("thinking")
        s.stream_by(block).stream_title("Deep ")
        s.stream_by(block).stream_title("Analysis...")
        s.stream_by(block).stream_body("Step 1: Check patterns\\n")
        s.stream_by(block).stream_body("Step 2: Validate\\n")
        s.stream_by(block).update_title("Analysis Complete")
        s.stream_by(block).done()
    """

    def __init__(self, id: Optional[str] = None, title: Optional[str] = None):
        super().__init__(id)
        self.initial_title = title

    def _generate_id(self) -> str:
        return f"text_block-{uuid.uuid4().hex[:8]}"

    def get_event_type_prefix(self) -> str:
        return "text_block"

    def stream_title(self, content: str) -> 'TextBlock':
        """Stream title content (appends to existing).

        Args:
            content: Content to append to title

        Returns:
            self for method chaining
        """
        return self._send_event("stream_title", content=content)

    def stream_body(self, content: str) -> 'TextBlock':
        """Stream body content (appends to existing).

        Args:
            content: Content to append to body

        Returns:
            self for method chaining
        """
        return self._send_event("stream_body", content=content)

    def update_title(self, title: str) -> 'TextBlock':
        """Replace entire title.

        Args:
            title: New title (replaces existing)

        Returns:
            self for method chaining
        """
        return self._send_event("update_title", title=title)

    def update_body(self, body: str) -> 'TextBlock':
        """Replace entire body.

        Args:
            body: New body (replaces existing)

        Returns:
            self for method chaining
        """
        return self._send_event("update_body", body=body)

    def set_variant(self, variant: str) -> 'TextBlock':
        """Set visual variant.

        Args:
            variant: Visual style (thinking, note, warning, error, success)

        Returns:
            self for method chaining
        """
        return self._send_event("set_variant", variant=variant)

    def done(self) -> 'TextBlock':
        """Mark text block as complete.

        Returns:
            self for method chaining
        """
        return self._send_event("done")

"""Surface structural streamer for embedded interactive components."""

from typing import Optional, Dict, Any
from .base import StructuralStreamer
import uuid


class Surface(StructuralStreamer):
    """Manages embedded surface lifecycle (identical to Artifact).

    Surfaces are embedded interactive components (iframes, embeds).
    Surface data is persisted to database as artifacts with surface type.

    Example:
        surface = Surface()
        s.stream_by(surface).generating("Loading calendar...")
        s.stream_by(surface).done(url="https://cal.com/embed", type="iframe")
    """

    def _generate_id(self) -> str:
        return f"surface-{uuid.uuid4().hex[:8]}"

    def get_event_type_prefix(self) -> str:
        return "surface"

    def generating(
        self,
        message: Optional[str] = None,
        progress: Optional[float] = None
    ) -> 'Surface':
        """Signal surface is loading.

        Args:
            message: Status message (e.g., "Loading calendar...")
            progress: Progress value 0.0-1.0

        Returns:
            self for method chaining
        """
        kwargs = {}
        if message is not None:
            kwargs["message"] = message
        if progress is not None:
            kwargs["progress"] = progress

        return self._send_event("generating", **kwargs)

    def done(
        self,
        url: str,
        type: str = "iframe",
        title: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'Surface':
        """Signal surface is ready and persist to database.

        Args:
            url: URL to surface
            type: Surface type (default: iframe)
            title: Display title
            description: Optional description
            metadata: Additional metadata

        Returns:
            self for method chaining
        """
        kwargs = {
            "url": url,
            "type": type,
        }
        if title:
            kwargs["title"] = title
        if description:
            kwargs["description"] = description
        if metadata:
            kwargs["metadata"] = metadata

        return self._send_event("done", **kwargs)

    def error(self, message: str) -> 'Surface':
        """Signal surface loading failed.

        Args:
            message: Error message

        Returns:
            self for method chaining
        """
        return self._send_event("error", message=message)

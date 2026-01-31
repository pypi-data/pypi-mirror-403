"""Artifact structural streamer for file/image/iframe artifacts."""

from typing import Optional, Dict, Any
from .base import StructuralStreamer
import uuid


class Artifact(StructuralStreamer):
    """Manages artifact lifecycle: generating → done.

    Artifacts are files, images, iframes that are generated and displayed.
    Artifact data is persisted to database on done().

    Example:
        artifact = Artifact()  # ID auto-generated
        s.stream_by(artifact).generating("Creating chart...", progress=0.5)
        s.stream_by(artifact).done(
            url="https://example.com/chart.png",
            type="image",
            title="Sales Chart"
        )
    """

    def _generate_id(self) -> str:
        return f"artifact-{uuid.uuid4().hex[:8]}"

    def get_event_type_prefix(self) -> str:
        return "artifact"

    def generating(
        self,
        message: Optional[str] = None,
        progress: Optional[float] = None
    ) -> 'Artifact':
        """Signal artifact is being generated.

        Args:
            message: Status message (e.g., "Creating chart...")
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
        type: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'Artifact':
        """Signal artifact is complete and persist to database.

        Args:
            url: URL to artifact
            type: Artifact type (image, iframe, document, video, audio, code, link, file)
            title: Display title
            description: Optional description
            metadata: Additional metadata (size, mimeType, dimensions, etc.)

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

    def error(self, message: str) -> 'Artifact':
        """Signal artifact generation failed.

        Args:
            message: Error message

        Returns:
            self for method chaining
        """
        return self._send_event("error", message=message)

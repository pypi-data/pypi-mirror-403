"""Artifact class for attaching files/URLs to messages."""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


class ArtifactType(str, Enum):
    """Artifact type enum for categorizing attachments."""

    DOCUMENT = "document"  # PDF, DOC, etc.
    IMAGE = "image"  # PNG, JPG, GIF, etc.
    IFRAME = "iframe"  # Embeddable content (maps, charts)
    VIDEO = "video"  # Video files or embeds
    AUDIO = "audio"  # Audio files
    CODE = "code"  # Code snippets with syntax highlighting
    LINK = "link"  # External links with preview
    FILE = "file"  # Generic file download


@dataclass
class Artifact:
    """Represents an artifact (URL attachment) for a message.

    Artifacts are URLs to files, images, iframes, or other resources
    that agents can attach to their responses.

    Example:
        artifact = Artifact(
            url="https://example.com/report.pdf",
            type=ArtifactType.DOCUMENT,
            title="Monthly Report",
            metadata={"size": 1024000, "mimeType": "application/pdf"}
        )
    """

    url: str
    type: ArtifactType
    title: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    position: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        d: Dict[str, Any] = {
            "url": self.url,
            "type": self.type.value,
        }
        if self.title:
            d["title"] = self.title
        if self.description:
            d["description"] = self.description
        if self.metadata:
            d["metadata"] = self.metadata
        if self.position is not None:
            d["position"] = self.position
        return d

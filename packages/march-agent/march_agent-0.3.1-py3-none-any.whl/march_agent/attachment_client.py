"""HTTP client for downloading attachments via gateway proxy."""

import base64
import logging
from dataclasses import dataclass
from io import BytesIO
from typing import Optional

import aiohttp

from .exceptions import APIException

logger = logging.getLogger(__name__)


@dataclass
class AttachmentInfo:
    """Attachment metadata from message."""

    id: str
    url: str
    filename: str
    content_type: str
    size: int
    object_key: Optional[str] = None

    @property
    def file_extension(self) -> str:
        """Get file extension without dot (e.g., 'pdf', 'png')."""
        if "." in self.filename:
            return self.filename.rsplit(".", 1)[-1].lower()
        return ""

    @property
    def file_type(self) -> str:
        """Get plain text file type (e.g., 'png', 'jpeg', 'pdf')."""
        # Map common MIME types to simple names
        mime_to_type = {
            "image/png": "png",
            "image/jpeg": "jpeg",
            "image/jpg": "jpeg",
            "image/gif": "gif",
            "image/webp": "webp",
            "image/svg+xml": "svg",
            "application/pdf": "pdf",
        }
        if self.content_type in mime_to_type:
            return mime_to_type[self.content_type]
        # Fallback to extension or content_type subtype
        if self.file_extension:
            return self.file_extension
        if "/" in self.content_type:
            return self.content_type.split("/")[-1]
        return "unknown"

    def is_image(self) -> bool:
        """Check if attachment is an image."""
        return self.content_type.startswith("image/")

    def is_pdf(self) -> bool:
        """Check if attachment is a PDF."""
        return self.content_type == "application/pdf"

    @classmethod
    def from_dict(cls, data: dict) -> "AttachmentInfo":
        """Create AttachmentInfo from dictionary."""
        return cls(
            id=data.get("id", ""),
            url=data.get("url", ""),
            filename=data.get("filename", ""),
            content_type=data.get("content_type", "application/octet-stream"),
            size=data.get("size", 0),
            object_key=data.get("object_key"),
        )


class AttachmentClient:
    """Client for downloading attachments into memory via gateway proxy."""

    def __init__(self, base_url: str):
        """
        Initialize the attachment client.

        Args:
            base_url: Base URL for the attachment service proxy (e.g., "http://gateway:8080/s/attachment")
        """
        self.base_url = base_url.rstrip("/")
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=120.0)  # 2 min for large files
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def download(self, url: str) -> bytes:
        """
        Download file into memory as bytes.

        Args:
            url: URL path to the attachment (e.g., "/attachments/file/tenant/conv/id_file.pdf")

        Returns:
            File content as bytes
        """
        # Normalize URL - remove leading slash if present
        url_path = url.lstrip("/")
        full_url = f"{self.base_url}/{url_path}"
        logger.info(f"Downloading attachment from: {full_url}")
        session = await self._get_session()

        try:
            async with session.get(full_url) as response:
                if response.status == 404:
                    raise APIException(f"Attachment not found: {url}")
                response.raise_for_status()
                data = await response.read()
                logger.debug(f"Downloaded attachment: {url} ({len(data)} bytes)")
                return data
        except aiohttp.ClientError as e:
            raise APIException(f"Failed to download attachment: {e}")

    async def download_as_base64(self, url: str) -> str:
        """
        Download and encode as base64 (for LLM vision APIs).

        Args:
            url: URL path to the attachment

        Returns:
            Base64 encoded string of the file content
        """
        data = await self.download(url)
        return base64.b64encode(data).decode("utf-8")

    async def download_to_buffer(self, url: str) -> BytesIO:
        """
        Download to BytesIO buffer (for PDF/document processing libraries).

        Args:
            url: URL path to the attachment

        Returns:
            BytesIO buffer containing the file content
        """
        data = await self.download(url)
        return BytesIO(data)

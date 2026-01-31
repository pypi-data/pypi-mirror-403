"""Comprehensive tests for AttachmentClient and AttachmentInfo."""

import pytest
import base64
from io import BytesIO
from unittest.mock import Mock, AsyncMock, patch
from march_agent.attachment_client import AttachmentClient, AttachmentInfo
from march_agent.exceptions import APIException
import aiohttp


class TestAttachmentInfo:
    """Test AttachmentInfo dataclass."""

    def test_attachment_info_creation(self):
        """Test creating AttachmentInfo."""
        info = AttachmentInfo(
            id="att-1",
            url="/attachments/file.pdf",
            filename="document.pdf",
            content_type="application/pdf",
            size=1024,
            object_key="tenant/conv/id_file.pdf"
        )

        assert info.id == "att-1"
        assert info.url == "/attachments/file.pdf"
        assert info.filename == "document.pdf"
        assert info.content_type == "application/pdf"
        assert info.size == 1024
        assert info.object_key == "tenant/conv/id_file.pdf"

    def test_attachment_info_from_dict_complete(self):
        """Test creating AttachmentInfo from complete dict."""
        data = {
            "id": "att-1",
            "url": "/files/image.png",
            "filename": "screenshot.png",
            "content_type": "image/png",
            "size": 2048,
            "object_key": "tenant/conv/id_screenshot.png"
        }

        info = AttachmentInfo.from_dict(data)

        assert info.id == "att-1"
        assert info.url == "/files/image.png"
        assert info.filename == "screenshot.png"
        assert info.content_type == "image/png"
        assert info.size == 2048
        assert info.object_key == "tenant/conv/id_screenshot.png"

    def test_attachment_info_from_dict_minimal(self):
        """Test creating AttachmentInfo with minimal fields."""
        data = {}

        info = AttachmentInfo.from_dict(data)

        assert info.id == ""
        assert info.url == ""
        assert info.filename == ""
        assert info.content_type == "application/octet-stream"
        assert info.size == 0
        assert info.object_key is None

    def test_file_extension_property(self):
        """Test file_extension property."""
        info = AttachmentInfo(
            id="1",
            url="/file",
            filename="document.pdf",
            content_type="application/pdf",
            size=1024
        )

        assert info.file_extension == "pdf"

    def test_file_extension_property_multiple_dots(self):
        """Test file_extension with multiple dots in filename."""
        info = AttachmentInfo(
            id="1",
            url="/file",
            filename="my.archive.tar.gz",
            content_type="application/gzip",
            size=1024
        )

        assert info.file_extension == "gz"

    def test_file_extension_property_no_extension(self):
        """Test file_extension when no extension."""
        info = AttachmentInfo(
            id="1",
            url="/file",
            filename="README",
            content_type="text/plain",
            size=100
        )

        assert info.file_extension == ""

    def test_file_extension_case_insensitive(self):
        """Test file_extension is lowercased."""
        info = AttachmentInfo(
            id="1",
            url="/file",
            filename="Document.PDF",
            content_type="application/pdf",
            size=1024
        )

        assert info.file_extension == "pdf"

    def test_file_type_property_png(self):
        """Test file_type for PNG image."""
        info = AttachmentInfo(
            id="1",
            url="/file",
            filename="image.png",
            content_type="image/png",
            size=1024
        )

        assert info.file_type == "png"

    def test_file_type_property_jpeg(self):
        """Test file_type for JPEG image."""
        info = AttachmentInfo(
            id="1",
            url="/file",
            filename="photo.jpg",
            content_type="image/jpeg",
            size=2048
        )

        assert info.file_type == "jpeg"

    def test_file_type_property_pdf(self):
        """Test file_type for PDF."""
        info = AttachmentInfo(
            id="1",
            url="/file",
            filename="doc.pdf",
            content_type="application/pdf",
            size=5000
        )

        assert info.file_type == "pdf"

    def test_file_type_property_gif(self):
        """Test file_type for GIF."""
        info = AttachmentInfo(
            id="1",
            url="/file",
            filename="animation.gif",
            content_type="image/gif",
            size=100
        )

        assert info.file_type == "gif"

    def test_file_type_property_webp(self):
        """Test file_type for WebP."""
        info = AttachmentInfo(
            id="1",
            url="/file",
            filename="image.webp",
            content_type="image/webp",
            size=800
        )

        assert info.file_type == "webp"

    def test_file_type_property_svg(self):
        """Test file_type for SVG."""
        info = AttachmentInfo(
            id="1",
            url="/file",
            filename="icon.svg",
            content_type="image/svg+xml",
            size=500
        )

        assert info.file_type == "svg"

    def test_file_type_property_fallback_to_extension(self):
        """Test file_type falls back to extension for unknown MIME type."""
        info = AttachmentInfo(
            id="1",
            url="/file",
            filename="data.json",
            content_type="application/json",
            size=200
        )

        assert info.file_type == "json"

    def test_file_type_property_fallback_to_mime_subtype(self):
        """Test file_type falls back to MIME subtype when no extension."""
        info = AttachmentInfo(
            id="1",
            url="/file",
            filename="file",
            content_type="application/zip",
            size=5000
        )

        assert info.file_type == "zip"

    def test_file_type_property_unknown(self):
        """Test file_type returns 'unknown' for unrecognized types."""
        info = AttachmentInfo(
            id="1",
            url="/file",
            filename="file",
            content_type="unknown",
            size=100
        )

        assert info.file_type == "unknown"

    def test_is_image_true_for_png(self):
        """Test is_image returns True for PNG."""
        info = AttachmentInfo(
            id="1",
            url="/file",
            filename="image.png",
            content_type="image/png",
            size=1024
        )

        assert info.is_image() is True

    def test_is_image_true_for_jpeg(self):
        """Test is_image returns True for JPEG."""
        info = AttachmentInfo(
            id="1",
            url="/file",
            filename="photo.jpg",
            content_type="image/jpeg",
            size=2048
        )

        assert info.is_image() is True

    def test_is_image_false_for_pdf(self):
        """Test is_image returns False for PDF."""
        info = AttachmentInfo(
            id="1",
            url="/file",
            filename="doc.pdf",
            content_type="application/pdf",
            size=5000
        )

        assert info.is_image() is False

    def test_is_image_false_for_text(self):
        """Test is_image returns False for text files."""
        info = AttachmentInfo(
            id="1",
            url="/file",
            filename="readme.txt",
            content_type="text/plain",
            size=100
        )

        assert info.is_image() is False

    def test_is_pdf_true(self):
        """Test is_pdf returns True for PDF."""
        info = AttachmentInfo(
            id="1",
            url="/file",
            filename="doc.pdf",
            content_type="application/pdf",
            size=5000
        )

        assert info.is_pdf() is True

    def test_is_pdf_false_for_image(self):
        """Test is_pdf returns False for images."""
        info = AttachmentInfo(
            id="1",
            url="/file",
            filename="image.png",
            content_type="image/png",
            size=1024
        )

        assert info.is_pdf() is False

    def test_is_pdf_false_for_text(self):
        """Test is_pdf returns False for text."""
        info = AttachmentInfo(
            id="1",
            url="/file",
            filename="doc.txt",
            content_type="text/plain",
            size=100
        )

        assert info.is_pdf() is False


class TestAttachmentClient:
    """Test AttachmentClient."""

    @pytest.mark.asyncio
    async def test_attachment_client_initialization(self):
        """Test AttachmentClient initialization."""
        client = AttachmentClient(base_url="http://gateway:8080/s/attachment")

        assert client.base_url == "http://gateway:8080/s/attachment"
        assert client._session is None

        await client.close()

    @pytest.mark.asyncio
    async def test_base_url_normalization(self):
        """Test that trailing slashes are removed."""
        client = AttachmentClient(base_url="http://gateway:8080/s/attachment/")

        assert client.base_url == "http://gateway:8080/s/attachment"

        await client.close()

    @pytest.mark.asyncio
    async def test_get_session_creates_session(self):
        """Test that _get_session creates aiohttp session."""
        client = AttachmentClient(base_url="http://gateway:8080")

        session = await client._get_session()

        assert isinstance(session, aiohttp.ClientSession)
        assert not session.closed

        await client.close()

    @pytest.mark.asyncio
    async def test_get_session_reuses_existing_session(self):
        """Test that _get_session reuses existing session."""
        client = AttachmentClient(base_url="http://gateway:8080")

        session1 = await client._get_session()
        session2 = await client._get_session()

        assert session1 is session2

        await client.close()

    @pytest.mark.asyncio
    async def test_get_session_recreates_closed_session(self):
        """Test that _get_session recreates closed session."""
        client = AttachmentClient(base_url="http://gateway:8080")

        session1 = await client._get_session()
        await client.close()

        session2 = await client._get_session()

        assert session1 is not session2
        assert session1.closed
        assert not session2.closed

        await client.close()

    @pytest.mark.asyncio
    async def test_close_session(self):
        """Test closing the client session."""
        client = AttachmentClient(base_url="http://gateway:8080")

        session = await client._get_session()
        await client.close()

        assert session.closed

    @pytest.mark.asyncio
    async def test_close_without_session(self):
        """Test closing when no session exists."""
        client = AttachmentClient(base_url="http://gateway:8080")

        await client.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_download_success(self):
        """Test successful file download."""
        client = AttachmentClient(base_url="http://gateway:8080/s/attachment")

        file_content = b"PDF file content here"

        with patch.object(client, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.read = AsyncMock(return_value=file_content)
            mock_response.raise_for_status = Mock()
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock()
            mock_get_session.return_value = mock_session

            data = await client.download("/attachments/file/tenant/conv/id_file.pdf")

            assert data == file_content
            # Verify URL construction
            call_args = mock_session.get.call_args
            assert call_args[0][0] == "http://gateway:8080/s/attachment/attachments/file/tenant/conv/id_file.pdf"

        await client.close()

    @pytest.mark.asyncio
    async def test_download_strips_leading_slash(self):
        """Test download strips leading slash from URL."""
        client = AttachmentClient(base_url="http://gateway:8080/s/attachment")

        with patch.object(client, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.read = AsyncMock(return_value=b"content")
            mock_response.raise_for_status = Mock()
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock()
            mock_get_session.return_value = mock_session

            await client.download("/files/test.pdf")

            # Should construct URL without double slash
            call_args = mock_session.get.call_args
            assert "s/attachment/files/test.pdf" in call_args[0][0]
            assert "s/attachment//files" not in call_args[0][0]

        await client.close()

    @pytest.mark.asyncio
    async def test_download_not_found(self):
        """Test download raises exception when file not found."""
        client = AttachmentClient(base_url="http://gateway:8080/s/attachment")

        with patch.object(client, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock()
            mock_get_session.return_value = mock_session

            with pytest.raises(APIException, match="Attachment not found"):
                await client.download("/files/nonexistent.pdf")

        await client.close()

    @pytest.mark.asyncio
    async def test_download_http_error(self):
        """Test download handles HTTP errors."""
        client = AttachmentClient(base_url="http://gateway:8080/s/attachment")

        with patch.object(client, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.raise_for_status = Mock(side_effect=aiohttp.ClientResponseError(
                request_info=Mock(),
                history=(),
                status=500
            ))
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock()
            mock_get_session.return_value = mock_session

            with pytest.raises(APIException, match="Failed to download attachment"):
                await client.download("/files/test.pdf")

        await client.close()

    @pytest.mark.asyncio
    async def test_download_network_error(self):
        """Test download handles network errors."""
        client = AttachmentClient(base_url="http://gateway:8080/s/attachment")

        with patch.object(client, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(side_effect=aiohttp.ClientError("Connection failed"))
            mock_get_session.return_value = mock_session

            with pytest.raises(APIException, match="Failed to download attachment"):
                await client.download("/files/test.pdf")

        await client.close()

    @pytest.mark.asyncio
    async def test_download_as_base64(self):
        """Test downloading and encoding as base64."""
        client = AttachmentClient(base_url="http://gateway:8080/s/attachment")

        file_content = b"Binary image data"
        expected_b64 = base64.b64encode(file_content).decode("utf-8")

        with patch.object(client, 'download', new_callable=AsyncMock) as mock_download:
            mock_download.return_value = file_content

            result = await client.download_as_base64("/files/image.png")

            assert result == expected_b64
            mock_download.assert_called_once_with("/files/image.png")

        await client.close()

    @pytest.mark.asyncio
    async def test_download_to_buffer(self):
        """Test downloading to BytesIO buffer."""
        client = AttachmentClient(base_url="http://gateway:8080/s/attachment")

        file_content = b"PDF binary content"

        with patch.object(client, 'download', new_callable=AsyncMock) as mock_download:
            mock_download.return_value = file_content

            buffer = await client.download_to_buffer("/files/doc.pdf")

            assert isinstance(buffer, BytesIO)
            assert buffer.read() == file_content
            mock_download.assert_called_once_with("/files/doc.pdf")

        await client.close()

    @pytest.mark.asyncio
    async def test_download_large_file(self):
        """Test downloading large file."""
        client = AttachmentClient(base_url="http://gateway:8080/s/attachment")

        # Simulate 5MB file
        large_content = b"x" * (5 * 1024 * 1024)

        with patch.object(client, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.read = AsyncMock(return_value=large_content)
            mock_response.raise_for_status = Mock()
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock()
            mock_get_session.return_value = mock_session

            data = await client.download("/files/large.zip")

            assert len(data) == 5 * 1024 * 1024

        await client.close()

    @pytest.mark.asyncio
    async def test_session_timeout_configuration(self):
        """Test that session has proper timeout configured."""
        client = AttachmentClient(base_url="http://gateway:8080/s/attachment")

        session = await client._get_session()

        # Timeout should be 120 seconds for large files
        assert session.timeout.total == 120.0

        await client.close()

    @pytest.mark.asyncio
    async def test_multiple_downloads_same_session(self):
        """Test multiple downloads reuse the same session."""
        client = AttachmentClient(base_url="http://gateway:8080/s/attachment")

        with patch.object(client, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.read = AsyncMock(return_value=b"content")
            mock_response.raise_for_status = Mock()
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock()
            mock_get_session.return_value = mock_session

            await client.download("/file1.pdf")
            await client.download("/file2.pdf")
            await client.download("/file3.pdf")

            # Session should be retrieved 3 times but same instance
            assert mock_get_session.call_count == 3

        await client.close()

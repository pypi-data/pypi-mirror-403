"""File attachment handling for Telegram Bot API.

Manages document uploads and downloads for large payloads.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO

if TYPE_CHECKING:
    from pyteledb.telegram.client import TelegramClient


@dataclass
class TelegramFile:
    """
    Represents a Telegram file.

    Attributes:
        file_id: Telegram file ID (for re-downloading).
        file_unique_id: Unique file identifier.
        file_size: File size in bytes.
        file_path: Relative path on Telegram servers (for download URL).
    """

    file_id: str
    file_unique_id: str
    file_size: int | None = None
    file_path: str | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> TelegramFile:
        """Create from API response data."""
        return cls(
            file_id=data["file_id"],
            file_unique_id=data["file_unique_id"],
            file_size=data.get("file_size"),
            file_path=data.get("file_path"),
        )


@dataclass
class Document:
    """
    Represents a Telegram document.

    Attributes:
        file: File information.
        file_name: Original filename.
        mime_type: MIME type.
    """

    file: TelegramFile
    file_name: str | None = None
    mime_type: str | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Document:
        """Create from API response data."""
        return cls(
            file=TelegramFile.from_api(data),
            file_name=data.get("file_name"),
            mime_type=data.get("mime_type"),
        )


class FileManager:
    """
    High-level file operations.

    Handles document upload/download for large payloads
    that don't fit in message text.
    """

    def __init__(self, client: TelegramClient, chat_id: int | str) -> None:
        """
        Initialize the file manager.

        Args:
            client: Telegram client instance.
            chat_id: Chat ID for all operations.
        """
        self.client = client
        self.chat_id = chat_id

    async def upload(
        self,
        file: BinaryIO | Path | str,
        filename: str | None = None,
        caption: str | None = None,
        disable_notification: bool = True,
    ) -> tuple[int, Document]:
        """
        Upload a file as a document.

        Args:
            file: File to upload (file object, Path, or path string).
            filename: Filename to use (defaults to Path.name).
            caption: Optional caption (max 1024 chars).
            disable_notification: Disable notification sound.

        Returns:
            Tuple of (message_id, Document).
        """
        # Handle different file input types
        if isinstance(file, (str, Path)):
            path = Path(file)
            filename = filename or path.name
            with open(path, "rb") as file_obj:
                result = await self.client.request(
                    "sendDocument",
                    params={
                        "chat_id": self.chat_id,
                        "caption": caption,
                        "disable_notification": disable_notification,
                    },
                    files={"document": (filename, file_obj)},
                )
        else:
            file_obj = file
            filename = filename or "document"
            result = await self.client.request(
                "sendDocument",
                params={
                    "chat_id": self.chat_id,
                    "caption": caption,
                    "disable_notification": disable_notification,
                },
                files={"document": (filename, file_obj)},
            )

        message_id = result["message_id"]
        document = Document.from_api(result["document"])
        return message_id, document

    async def upload_bytes(
        self,
        data: bytes,
        filename: str,
        caption: str | None = None,
        disable_notification: bool = True,
    ) -> tuple[int, Document]:
        """
        Upload bytes as a document.

        Args:
            data: Bytes to upload.
            filename: Filename to use.
            caption: Optional caption.
            disable_notification: Disable notification sound.

        Returns:
            Tuple of (message_id, Document).
        """
        import io

        file_obj = io.BytesIO(data)
        result = await self.client.request(
            "sendDocument",
            params={
                "chat_id": self.chat_id,
                "caption": caption,
                "disable_notification": disable_notification,
            },
            files={"document": (filename, file_obj)},
        )

        message_id = result["message_id"]
        document = Document.from_api(result["document"])
        return message_id, document

    async def get_file_info(self, file_id: str) -> TelegramFile:
        """
        Get file information for downloading.

        Args:
            file_id: Telegram file ID.

        Returns:
            TelegramFile with download path.
        """
        result = await self.client.request("getFile", {"file_id": file_id})
        return TelegramFile.from_api(result)

    async def download(
        self,
        file_id: str,
        destination: Path | str | None = None,
    ) -> bytes:
        """
        Download a file.

        Args:
            file_id: Telegram file ID.
            destination: Optional path to save the file.

        Returns:
            File contents as bytes.
        """
        import httpx

        # Get the file path
        file_info = await self.get_file_info(file_id)
        if not file_info.file_path:
            raise ValueError("File path not available")

        # Construct download URL
        token = self.client.config.token
        url = f"https://api.telegram.org/file/bot{token}/{file_info.file_path}"

        # Download
        async with httpx.AsyncClient() as http:
            response = await http.get(url)
            response.raise_for_status()
            content = response.content

        # Save if destination provided
        if destination:
            path = Path(destination)
            path.write_bytes(content)

        return content

    async def get_document_from_message(
        self,
        message_data: dict[str, Any],
    ) -> Document | None:
        """
        Extract document info from a message.

        Args:
            message_data: Raw message data from API.

        Returns:
            Document if present, None otherwise.
        """
        doc_data = message_data.get("document")
        if doc_data:
            return Document.from_api(doc_data)
        return None

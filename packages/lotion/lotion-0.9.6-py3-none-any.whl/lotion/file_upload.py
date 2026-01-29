"""File upload support for Notion API.

This module provides functionality to upload files to Notion using the
Direct Upload method (files up to 20MB).
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class FileUploadStatus(Enum):
    """Status of a file upload."""

    PENDING = "pending"
    UPLOADED = "uploaded"
    ARCHIVED = "archived"


@dataclass
class FileUpload:
    """Represents a file upload object from Notion API.

    Attributes:
        id: The unique identifier of the file upload.
        status: The current status of the file upload.
        created_time: ISO 8601 timestamp when the upload was created.
        expiry_time: ISO 8601 timestamp when the upload will expire (if pending).
        upload_url: The URL to send the file data to (if pending).
    """

    id: str
    status: FileUploadStatus
    created_time: str | None = None
    expiry_time: str | None = None
    upload_url: str | None = None

    @staticmethod
    def of(data: dict) -> "FileUpload":
        """Create a FileUpload instance from API response data.

        Args:
            data: The response dictionary from Notion API.

        Returns:
            A FileUpload instance.
        """
        return FileUpload(
            id=data["id"],
            status=FileUploadStatus(data["status"]),
            created_time=data.get("created_time"),
            expiry_time=data.get("expiry_time"),
            upload_url=data.get("upload_url"),
        )

    def is_uploaded(self) -> bool:
        """Check if the file has been successfully uploaded."""
        return self.status == FileUploadStatus.UPLOADED

    def is_pending(self) -> bool:
        """Check if the file upload is pending."""
        return self.status == FileUploadStatus.PENDING

    def to_block_reference(self) -> dict:
        """Convert to a block reference format for use in blocks.

        Returns:
            A dictionary with the file_upload reference format.
        """
        return {
            "type": "file_upload",
            "file_upload": {"id": self.id},
        }


def get_content_type(file_path: Path | str) -> str:
    """Infer the MIME content type from a file extension.

    Args:
        file_path: Path to the file.

    Returns:
        The MIME content type string.
    """
    path = Path(file_path) if isinstance(file_path, str) else file_path
    extension = path.suffix.lower()

    content_types = {
        # Images
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
        ".ico": "image/x-icon",
        ".bmp": "image/bmp",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
        # Documents
        ".pdf": "application/pdf",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xls": "application/vnd.ms-excel",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".ppt": "application/vnd.ms-powerpoint",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".txt": "text/plain",
        ".csv": "text/csv",
        ".json": "application/json",
        ".xml": "application/xml",
        ".html": "text/html",
        ".htm": "text/html",
        ".md": "text/markdown",
        # Audio
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".ogg": "audio/ogg",
        ".m4a": "audio/mp4",
        ".aac": "audio/aac",
        ".flac": "audio/flac",
        # Video
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".avi": "video/x-msvideo",
        ".mov": "video/quicktime",
        ".mkv": "video/x-matroska",
        ".wmv": "video/x-ms-wmv",
        # Archives
        ".zip": "application/zip",
        ".tar": "application/x-tar",
        ".gz": "application/gzip",
        ".rar": "application/vnd.rar",
        ".7z": "application/x-7z-compressed",
    }

    return content_types.get(extension, "application/octet-stream")

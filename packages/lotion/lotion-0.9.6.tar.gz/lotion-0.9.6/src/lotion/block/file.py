"""File block for Notion.

This module provides the File block class for representing file attachments
in Notion pages.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .block import Block
from .rich_text.rich_text import RichText

if TYPE_CHECKING:
    from lotion.file_upload import FileUpload


class File(Block):
    """File block for Notion.

    Supports three types of files:
    - external: Files hosted on external URLs
    - file: Files stored in Notion (from API response, read-only)
    - file_upload: Files uploaded via the File Upload API
    """

    file_caption: list
    file_type: str
    file_file: dict | None
    file_external: dict | None
    file_file_upload: dict | None
    file_name: str | None
    type: str = "file"

    def __init__(
        self,
        file_caption: list,
        file_type: str,
        file_file: dict | None = None,
        file_external: dict | None = None,
        file_file_upload: dict | None = None,
        file_name: str | None = None,
        id: str | None = None,
        archived: bool | None = None,
        created_time: str | None = None,
        last_edited_time: str | None = None,
        has_children: bool | None = None,
        parent: dict | None = None,
    ):
        super().__init__(id, archived, created_time, last_edited_time, has_children, parent)
        self.file_caption = file_caption
        self.file_type = file_type
        self.file_file = file_file
        self.file_external = file_external
        self.file_file_upload = file_file_upload
        self.file_name = file_name

    @staticmethod
    def of(block: dict) -> File:
        """Create a File block from API response data.

        Args:
            block: The block dictionary from Notion API.

        Returns:
            A File block instance.
        """
        file_data = block["file"]
        file_caption = file_data.get("caption", [])
        file_type = file_data.get("type", "")
        file_file = file_data.get("file")
        file_external = file_data.get("external")
        file_file_upload = file_data.get("file_upload")
        file_name = file_data.get("name")
        return File(
            id=block["id"],
            archived=block["archived"],
            created_time=block["created_time"],
            last_edited_time=block["last_edited_time"],
            has_children=block["has_children"],
            parent=block["parent"],
            file_caption=file_caption,
            file_type=file_type,
            file_file=file_file,
            file_external=file_external,
            file_file_upload=file_file_upload,
            file_name=file_name,
        )

    def to_dict_sub(self) -> dict:
        """Convert to Notion API format.

        Returns:
            A dictionary in Notion API format.
        """
        result = {"caption": self.file_caption}

        if self.file_name:
            result["name"] = self.file_name

        if self.file_type == "file":
            result["type"] = self.file_type
            result["file"] = self.file_file
        elif self.file_type == "external":
            result["type"] = self.file_type
            result["external"] = self.file_external
        elif self.file_type == "file_upload":
            result["type"] = self.file_type
            result["file_upload"] = self.file_file_upload
        else:
            msg = f"Invalid file type: {self.file_type}"
            raise ValueError(msg)

        return result

    def to_slack_text(self) -> str:
        """Convert to Slack text format.

        Returns:
            A string representation for Slack.
        """
        name_part = f" ({self.file_name})" if self.file_name else ""

        if self.file_type == "file":
            return f"{self.file_file['url']}{name_part}"
        if self.file_type == "external":
            return f"{self.file_external['url']}{name_part}"
        if self.file_type == "file_upload":
            return f"[file_upload:{self.file_file_upload.get('id', 'unknown')}]{name_part}"
        msg = f"Invalid file type: {self.file_type}"
        raise ValueError(msg)

    @property
    def url(self) -> str | None:
        """Get the file URL if available.

        Returns:
            The file URL, or None if not available.
        """
        if self.file_type == "file" and self.file_file:
            return self.file_file.get("url")
        if self.file_type == "external" and self.file_external:
            return self.file_external.get("url")
        return None

    @classmethod
    def from_external_url(cls, url: str, name: str | None = None, caption: str | None = None) -> File:
        """Create a File block from an external URL.

        Args:
            url: The URL of the file.
            name: Optional display name for the file.
            caption: Optional caption text.

        Returns:
            A File block with external type.
        """
        file_caption = []
        if caption:
            file_caption = RichText.from_plain_text(caption).to_dict()
        return File(
            file_caption=file_caption,
            file_type="external",
            file_external={"url": url},
            file_name=name,
        )

    @classmethod
    def from_file_upload(cls, file_upload: FileUpload, name: str | None = None, caption: str | None = None) -> File:
        """Create a File block from an uploaded file.

        Args:
            file_upload: The FileUpload object from Lotion.upload_file().
            name: Optional display name for the file.
            caption: Optional caption text.

        Returns:
            A File block with file_upload type.

        Example:
            >>> lotion = Lotion.get_instance()
            >>> file_upload = lotion.upload_file("/path/to/document.pdf")
            >>> file_block = File.from_file_upload(file_upload, name="My Document")
            >>> lotion.append_block(page_id, file_block)
        """
        file_caption = []
        if caption:
            file_caption = RichText.from_plain_text(caption).to_dict()
        return File(
            file_caption=file_caption,
            file_type="file_upload",
            file_file_upload={"id": file_upload.id},
            file_name=name,
        )

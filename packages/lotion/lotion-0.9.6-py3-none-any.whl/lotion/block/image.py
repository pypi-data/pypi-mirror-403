from __future__ import annotations

from typing import TYPE_CHECKING

from .block import Block
from .rich_text.rich_text import RichText

if TYPE_CHECKING:
    from lotion.file_upload import FileUpload


class Image(Block):
    """Image block for Notion.

    Supports three types of images:
    - external: Images hosted on external URLs
    - file: Images stored in Notion (from API response, read-only)
    - file_upload: Images uploaded via the File Upload API
    """

    image_caption: list
    image_type: str
    image_file: dict | None
    image_external: dict | None
    image_file_upload: dict | None
    type: str = "image"

    def __init__(
        self,
        image_caption: list,
        image_type: str,
        image_file: dict | None = None,
        image_external: dict | None = None,
        image_file_upload: dict | None = None,
        id: str | None = None,
        archived: bool | None = None,
        created_time: str | None = None,
        last_edited_time: str | None = None,
        has_children: bool | None = None,
        parent: dict | None = None,
    ):
        super().__init__(id, archived, created_time, last_edited_time, has_children, parent)
        self.image_caption = image_caption
        self.image_type = image_type
        self.image_file = image_file
        self.image_external = image_external
        self.image_file_upload = image_file_upload

    @staticmethod
    def of(block: dict) -> Image:
        image = block["image"]
        image_caption = image.get("caption", [])
        image_type = image.get("type", "")
        image_file = image.get("file")
        image_external = image.get("external")
        image_file_upload = image.get("file_upload")
        return Image(
            id=block["id"],
            archived=block["archived"],
            created_time=block["created_time"],
            last_edited_time=block["last_edited_time"],
            has_children=block["has_children"],
            parent=block["parent"],
            image_caption=image_caption,
            image_type=image_type,
            image_file=image_file,
            image_external=image_external,
            image_file_upload=image_file_upload,
        )

    def to_dict_sub(self) -> dict:
        if self.image_type == "file":
            # Read-only: Notion-hosted files cannot be created via API
            return {
                "caption": self.image_caption,
                "type": self.image_type,
                "file": self.image_file,
            }
        if self.image_type == "external":
            return {
                "caption": self.image_caption,
                "type": self.image_type,
                "external": self.image_external,
            }
        if self.image_type == "file_upload":
            return {
                "caption": self.image_caption,
                "type": self.image_type,
                "file_upload": self.image_file_upload,
            }
        msg = f"Invalid image type: {self.image_type}"
        raise ValueError(msg)

    def to_slack_text(self) -> str:
        if self.image_type == "file":
            return self.image_file["url"]
        if self.image_type == "external":
            return self.image_external["url"]
        if self.image_type == "file_upload":
            # file_upload doesn't have a direct URL until attached
            return f"[file_upload:{self.image_file_upload.get('id', 'unknown')}]"
        msg = f"Invalid image type: {self.image_type}"
        raise ValueError(msg)

    @classmethod
    def from_external_url(cls, url: str, alias_url: str | None = None) -> Image:
        """Create an Image block from an external URL.

        Args:
            url: The URL of the image.
            alias_url: Optional URL to display as caption link.

        Returns:
            An Image block with external type.
        """
        image_caption = []
        if alias_url:
            image_caption = RichText.from_plain_link(alias_url, alias_url).to_dict()
        return Image(
            image_caption=image_caption,
            image_type="external",
            image_external={"url": url},
        )

    @classmethod
    def from_file_upload(cls, file_upload: FileUpload, caption: str | None = None) -> Image:
        """Create an Image block from an uploaded file.

        Args:
            file_upload: The FileUpload object from Lotion.upload_file().
            caption: Optional caption text for the image.

        Returns:
            An Image block with file_upload type.

        Example:
            >>> lotion = Lotion.get_instance()
            >>> file_upload = lotion.upload_file("/path/to/image.png")
            >>> image = Image.from_file_upload(file_upload, caption="My image")
            >>> lotion.append_block(page_id, image)
        """
        image_caption = []
        if caption:
            image_caption = RichText.from_plain_text(caption).to_dict()
        return Image(
            image_caption=image_caption,
            image_type="file_upload",
            image_file_upload={"id": file_upload.id},
        )

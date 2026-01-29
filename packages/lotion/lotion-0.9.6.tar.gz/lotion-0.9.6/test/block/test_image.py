"""Unit tests for Image block."""

from unittest import TestCase

import pytest

from lotion.block.image import Image
from lotion.file_upload import FileUpload, FileUploadStatus


class TestImageBlock(TestCase):
    """Unit tests for Image block class."""

    @pytest.mark.minimum()
    def test_from_external_url(self):
        """Test creating Image from external URL."""
        image = Image.from_external_url("https://example.com/image.png")

        self.assertEqual(image.image_type, "external")
        self.assertEqual(image.image_external["url"], "https://example.com/image.png")
        self.assertEqual(image.type, "image")

    @pytest.mark.minimum()
    def test_from_external_url_with_caption(self):
        """Test creating Image from external URL with caption."""
        image = Image.from_external_url(
            "https://example.com/image.png",
            alias_url="https://example.com/link",
        )

        self.assertEqual(image.image_type, "external")
        self.assertIsNotNone(image.image_caption)
        self.assertGreater(len(image.image_caption), 0)

    @pytest.mark.minimum()
    def test_from_file_upload(self):
        """Test creating Image from file upload."""
        file_upload = FileUpload(
            id="test-upload-id",
            status=FileUploadStatus.UPLOADED,
        )

        image = Image.from_file_upload(file_upload)

        self.assertEqual(image.image_type, "file_upload")
        self.assertEqual(image.image_file_upload["id"], "test-upload-id")
        self.assertEqual(image.type, "image")

    @pytest.mark.minimum()
    def test_from_file_upload_with_caption(self):
        """Test creating Image from file upload with caption."""
        file_upload = FileUpload(
            id="test-upload-id",
            status=FileUploadStatus.UPLOADED,
        )

        image = Image.from_file_upload(file_upload, caption="My image")

        self.assertEqual(image.image_type, "file_upload")
        self.assertIsNotNone(image.image_caption)
        self.assertGreater(len(image.image_caption), 0)

    @pytest.mark.minimum()
    def test_to_dict_sub_external(self):
        """Test serialization of external image."""
        image = Image.from_external_url("https://example.com/image.png")

        result = image.to_dict_sub()

        self.assertEqual(result["type"], "external")
        self.assertEqual(result["external"]["url"], "https://example.com/image.png")
        self.assertIn("caption", result)

    @pytest.mark.minimum()
    def test_to_dict_sub_file_upload(self):
        """Test serialization of file_upload image."""
        file_upload = FileUpload(
            id="test-upload-id",
            status=FileUploadStatus.UPLOADED,
        )
        image = Image.from_file_upload(file_upload)

        result = image.to_dict_sub()

        self.assertEqual(result["type"], "file_upload")
        self.assertEqual(result["file_upload"]["id"], "test-upload-id")
        self.assertIn("caption", result)

    @pytest.mark.minimum()
    def test_of_parses_external_image(self):
        """Test parsing external image from API response."""
        block_data = {
            "id": "block-id",
            "type": "image",
            "archived": False,
            "created_time": "2025-01-01T00:00:00.000Z",
            "last_edited_time": "2025-01-01T00:00:00.000Z",
            "has_children": False,
            "parent": {"type": "page_id", "page_id": "page-id"},
            "image": {
                "type": "external",
                "external": {"url": "https://example.com/image.png"},
                "caption": [],
            },
        }

        image = Image.of(block_data)

        self.assertEqual(image.id, "block-id")
        self.assertEqual(image.image_type, "external")
        self.assertEqual(image.image_external["url"], "https://example.com/image.png")

    @pytest.mark.minimum()
    def test_of_parses_file_upload_image(self):
        """Test parsing file_upload image from API response."""
        block_data = {
            "id": "block-id",
            "type": "image",
            "archived": False,
            "created_time": "2025-01-01T00:00:00.000Z",
            "last_edited_time": "2025-01-01T00:00:00.000Z",
            "has_children": False,
            "parent": {"type": "page_id", "page_id": "page-id"},
            "image": {
                "type": "file_upload",
                "file_upload": {"id": "file-upload-id"},
                "caption": [],
            },
        }

        image = Image.of(block_data)

        self.assertEqual(image.id, "block-id")
        self.assertEqual(image.image_type, "file_upload")
        self.assertEqual(image.image_file_upload["id"], "file-upload-id")

    @pytest.mark.minimum()
    def test_of_parses_file_image(self):
        """Test parsing Notion-hosted file image from API response."""
        block_data = {
            "id": "block-id",
            "type": "image",
            "archived": False,
            "created_time": "2025-01-01T00:00:00.000Z",
            "last_edited_time": "2025-01-01T00:00:00.000Z",
            "has_children": False,
            "parent": {"type": "page_id", "page_id": "page-id"},
            "image": {
                "type": "file",
                "file": {
                    "url": "https://prod-files-secure.s3.us-west-2.amazonaws.com/...",
                    "expiry_time": "2025-01-01T01:00:00.000Z",
                },
                "caption": [],
            },
        }

        image = Image.of(block_data)

        self.assertEqual(image.id, "block-id")
        self.assertEqual(image.image_type, "file")
        self.assertIsNotNone(image.image_file)

    @pytest.mark.minimum()
    def test_to_slack_text_external(self):
        """Test Slack text for external image."""
        image = Image.from_external_url("https://example.com/image.png")

        result = image.to_slack_text()

        self.assertEqual(result, "https://example.com/image.png")

    @pytest.mark.minimum()
    def test_to_slack_text_file_upload(self):
        """Test Slack text for file_upload image."""
        file_upload = FileUpload(
            id="test-upload-id",
            status=FileUploadStatus.UPLOADED,
        )
        image = Image.from_file_upload(file_upload)

        result = image.to_slack_text()

        self.assertIn("test-upload-id", result)

"""Unit tests for File block."""

from unittest import TestCase

import pytest

from lotion.block.file import File
from lotion.file_upload import FileUpload, FileUploadStatus


class TestFileBlock(TestCase):
    """Unit tests for File block class."""

    @pytest.mark.minimum()
    def test_from_external_url(self):
        """Test creating File from external URL."""
        file_block = File.from_external_url("https://example.com/document.pdf")

        self.assertEqual(file_block.file_type, "external")
        self.assertEqual(file_block.file_external["url"], "https://example.com/document.pdf")
        self.assertEqual(file_block.type, "file")

    @pytest.mark.minimum()
    def test_from_external_url_with_name(self):
        """Test creating File from external URL with name."""
        file_block = File.from_external_url(
            "https://example.com/document.pdf",
            name="My Document",
        )

        self.assertEqual(file_block.file_type, "external")
        self.assertEqual(file_block.file_name, "My Document")

    @pytest.mark.minimum()
    def test_from_external_url_with_caption(self):
        """Test creating File from external URL with caption."""
        file_block = File.from_external_url(
            "https://example.com/document.pdf",
            caption="Download here",
        )

        self.assertEqual(file_block.file_type, "external")
        self.assertIsNotNone(file_block.file_caption)
        self.assertGreater(len(file_block.file_caption), 0)

    @pytest.mark.minimum()
    def test_from_file_upload(self):
        """Test creating File from file upload."""
        file_upload = FileUpload(
            id="test-upload-id",
            status=FileUploadStatus.UPLOADED,
        )

        file_block = File.from_file_upload(file_upload)

        self.assertEqual(file_block.file_type, "file_upload")
        self.assertEqual(file_block.file_file_upload["id"], "test-upload-id")
        self.assertEqual(file_block.type, "file")

    @pytest.mark.minimum()
    def test_from_file_upload_with_name_and_caption(self):
        """Test creating File from file upload with name and caption."""
        file_upload = FileUpload(
            id="test-upload-id",
            status=FileUploadStatus.UPLOADED,
        )

        file_block = File.from_file_upload(
            file_upload,
            name="Report.pdf",
            caption="Quarterly report",
        )

        self.assertEqual(file_block.file_type, "file_upload")
        self.assertEqual(file_block.file_name, "Report.pdf")
        self.assertGreater(len(file_block.file_caption), 0)

    @pytest.mark.minimum()
    def test_to_dict_sub_external(self):
        """Test serialization of external file."""
        file_block = File.from_external_url(
            "https://example.com/document.pdf",
            name="My Doc",
        )

        result = file_block.to_dict_sub()

        self.assertEqual(result["type"], "external")
        self.assertEqual(result["external"]["url"], "https://example.com/document.pdf")
        self.assertEqual(result["name"], "My Doc")
        self.assertIn("caption", result)

    @pytest.mark.minimum()
    def test_to_dict_sub_file_upload(self):
        """Test serialization of file_upload file."""
        file_upload = FileUpload(
            id="test-upload-id",
            status=FileUploadStatus.UPLOADED,
        )
        file_block = File.from_file_upload(file_upload, name="Upload.pdf")

        result = file_block.to_dict_sub()

        self.assertEqual(result["type"], "file_upload")
        self.assertEqual(result["file_upload"]["id"], "test-upload-id")
        self.assertEqual(result["name"], "Upload.pdf")
        self.assertIn("caption", result)

    @pytest.mark.minimum()
    def test_of_parses_external_file(self):
        """Test parsing external file from API response."""
        block_data = {
            "id": "block-id",
            "type": "file",
            "archived": False,
            "created_time": "2025-01-01T00:00:00.000Z",
            "last_edited_time": "2025-01-01T00:00:00.000Z",
            "has_children": False,
            "parent": {"type": "page_id", "page_id": "page-id"},
            "file": {
                "type": "external",
                "external": {"url": "https://example.com/document.pdf"},
                "caption": [],
                "name": "Document.pdf",
            },
        }

        file_block = File.of(block_data)

        self.assertEqual(file_block.id, "block-id")
        self.assertEqual(file_block.file_type, "external")
        self.assertEqual(file_block.file_external["url"], "https://example.com/document.pdf")
        self.assertEqual(file_block.file_name, "Document.pdf")

    @pytest.mark.minimum()
    def test_of_parses_file_upload_file(self):
        """Test parsing file_upload file from API response."""
        block_data = {
            "id": "block-id",
            "type": "file",
            "archived": False,
            "created_time": "2025-01-01T00:00:00.000Z",
            "last_edited_time": "2025-01-01T00:00:00.000Z",
            "has_children": False,
            "parent": {"type": "page_id", "page_id": "page-id"},
            "file": {
                "type": "file_upload",
                "file_upload": {"id": "file-upload-id"},
                "caption": [],
            },
        }

        file_block = File.of(block_data)

        self.assertEqual(file_block.id, "block-id")
        self.assertEqual(file_block.file_type, "file_upload")
        self.assertEqual(file_block.file_file_upload["id"], "file-upload-id")

    @pytest.mark.minimum()
    def test_of_parses_notion_hosted_file(self):
        """Test parsing Notion-hosted file from API response."""
        block_data = {
            "id": "block-id",
            "type": "file",
            "archived": False,
            "created_time": "2025-01-01T00:00:00.000Z",
            "last_edited_time": "2025-01-01T00:00:00.000Z",
            "has_children": False,
            "parent": {"type": "page_id", "page_id": "page-id"},
            "file": {
                "type": "file",
                "file": {
                    "url": "https://prod-files-secure.s3.us-west-2.amazonaws.com/...",
                    "expiry_time": "2025-01-01T01:00:00.000Z",
                },
                "caption": [],
            },
        }

        file_block = File.of(block_data)

        self.assertEqual(file_block.id, "block-id")
        self.assertEqual(file_block.file_type, "file")
        self.assertIsNotNone(file_block.file_file)

    @pytest.mark.minimum()
    def test_url_property_external(self):
        """Test url property for external file."""
        file_block = File.from_external_url("https://example.com/document.pdf")

        self.assertEqual(file_block.url, "https://example.com/document.pdf")

    @pytest.mark.minimum()
    def test_url_property_file_upload(self):
        """Test url property for file_upload (returns None)."""
        file_upload = FileUpload(
            id="test-upload-id",
            status=FileUploadStatus.UPLOADED,
        )
        file_block = File.from_file_upload(file_upload)

        self.assertIsNone(file_block.url)

    @pytest.mark.minimum()
    def test_to_slack_text_external(self):
        """Test Slack text for external file."""
        file_block = File.from_external_url(
            "https://example.com/document.pdf",
            name="My Doc",
        )

        result = file_block.to_slack_text()

        self.assertIn("https://example.com/document.pdf", result)
        self.assertIn("My Doc", result)

    @pytest.mark.minimum()
    def test_to_slack_text_file_upload(self):
        """Test Slack text for file_upload file."""
        file_upload = FileUpload(
            id="test-upload-id",
            status=FileUploadStatus.UPLOADED,
        )
        file_block = File.from_file_upload(file_upload, name="Upload.pdf")

        result = file_block.to_slack_text()

        self.assertIn("test-upload-id", result)
        self.assertIn("Upload.pdf", result)

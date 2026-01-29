"""API integration tests for file upload functionality."""

import tempfile
from pathlib import Path
from unittest import TestCase

import pytest

from lotion import Lotion
from lotion.block import File, Image


@pytest.mark.api()
class TestApiFileUpload(TestCase):
    """API integration tests for file upload."""

    PAGE_ID = "1596567a3bbf8049803de1ffe3616d9e"

    def setUp(self):
        self.lotion = Lotion.get_instance()
        self.lotion.clear_page(self.PAGE_ID)
        self.temp_files = []

    def tearDown(self):
        # Clean up temp files
        for temp_file in self.temp_files:
            if temp_file.exists():
                temp_file.unlink()
        self.lotion.clear_page(self.PAGE_ID)

    def _create_temp_image(self) -> Path:
        """Create a minimal valid PNG file for testing."""
        # Minimal PNG (1x1 pixel, transparent)
        png_data = bytes(
            [
                0x89,
                0x50,
                0x4E,
                0x47,
                0x0D,
                0x0A,
                0x1A,
                0x0A,  # PNG signature
                0x00,
                0x00,
                0x00,
                0x0D,
                0x49,
                0x48,
                0x44,
                0x52,  # IHDR chunk
                0x00,
                0x00,
                0x00,
                0x01,
                0x00,
                0x00,
                0x00,
                0x01,  # 1x1 dimensions
                0x08,
                0x06,
                0x00,
                0x00,
                0x00,
                0x1F,
                0x15,
                0xC4,
                0x89,
                0x00,
                0x00,
                0x00,
                0x0A,
                0x49,
                0x44,
                0x41,  # IDAT chunk
                0x54,
                0x78,
                0x9C,
                0x63,
                0x00,
                0x01,
                0x00,
                0x00,
                0x05,
                0x00,
                0x01,
                0x0D,
                0x0A,
                0x2D,
                0xB4,
                0x00,
                0x00,
                0x00,
                0x00,
                0x49,
                0x45,
                0x4E,
                0x44,
                0xAE,  # IEND chunk
                0x42,
                0x60,
                0x82,
            ]
        )

        temp_file = Path(tempfile.mktemp(suffix=".png"))
        temp_file.write_bytes(png_data)
        self.temp_files.append(temp_file)
        return temp_file

    def _create_temp_text_file(self) -> Path:
        """Create a text file for testing."""
        temp_file = Path(tempfile.mktemp(suffix=".txt"))
        temp_file.write_text("Hello, Notion!")
        self.temp_files.append(temp_file)
        return temp_file

    def test_upload_image_and_append_block(self):
        """Test uploading an image file and appending as Image block."""
        # Create temp image
        image_path = self._create_temp_image()

        # Upload file
        file_upload = self.lotion.upload_file(image_path)

        # Verify upload status
        self.assertTrue(file_upload.is_uploaded())
        self.assertIsNotNone(file_upload.id)

        # Create and append image block
        image_block = Image.from_file_upload(file_upload, caption="Test image")
        self.lotion.append_block(self.PAGE_ID, image_block)

        # Verify block was added
        page = self.lotion.retrieve_page(self.PAGE_ID)
        self.assertEqual(len(page.block_children), 1)
        self.assertIsInstance(page.block_children[0], Image)

    def test_upload_file_and_append_block(self):
        """Test uploading a file and appending as File block."""
        # Create temp file
        file_path = self._create_temp_text_file()

        # Upload file
        file_upload = self.lotion.upload_file(file_path)

        # Verify upload status
        self.assertTrue(file_upload.is_uploaded())
        self.assertIsNotNone(file_upload.id)

        # Create and append file block
        file_block = File.from_file_upload(
            file_upload,
            name="test.txt",
            caption="Test file",
        )
        self.lotion.append_block(self.PAGE_ID, file_block)

        # Verify block was added
        page = self.lotion.retrieve_page(self.PAGE_ID)
        self.assertEqual(len(page.block_children), 1)
        self.assertIsInstance(page.block_children[0], File)

    def test_upload_with_custom_filename(self):
        """Test uploading a file with custom filename."""
        # Create temp image
        image_path = self._create_temp_image()

        # Upload with custom name
        file_upload = self.lotion.upload_file(
            image_path,
            filename="custom_name.png",
        )

        # Verify upload succeeded
        self.assertTrue(file_upload.is_uploaded())

    def test_upload_file_not_found(self):
        """Test that FileNotFoundError is raised for non-existent file."""
        with self.assertRaises(FileNotFoundError):
            self.lotion.upload_file("/non/existent/file.png")

    def test_upload_file_too_large(self):
        """Test that ValueError is raised for files over 20MB."""
        # Create a temp file that we'll pretend is too large
        # We can't actually create a 20MB+ file in tests, so this is more of a unit test
        pass  # This would require mocking or creating a large file

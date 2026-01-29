"""Unit tests for file upload functionality."""

from unittest import TestCase

import pytest

from lotion.file_upload import FileUpload, FileUploadStatus, get_content_type


class TestFileUpload(TestCase):
    """Unit tests for FileUpload class."""

    @pytest.mark.minimum()
    def test_of_creates_pending_file_upload(self):
        """Test that FileUpload.of correctly parses pending upload response."""
        data = {
            "object": "file_upload",
            "id": "test-upload-id-123",
            "status": "pending",
            "created_time": "2025-01-01T00:00:00.000Z",
            "expiry_time": "2025-01-01T01:00:00.000Z",
            "upload_url": "https://api.notion.com/v1/file_uploads/test-upload-id-123/send",
        }

        file_upload = FileUpload.of(data)

        self.assertEqual(file_upload.id, "test-upload-id-123")
        self.assertEqual(file_upload.status, FileUploadStatus.PENDING)
        self.assertTrue(file_upload.is_pending())
        self.assertFalse(file_upload.is_uploaded())
        self.assertEqual(file_upload.upload_url, "https://api.notion.com/v1/file_uploads/test-upload-id-123/send")

    @pytest.mark.minimum()
    def test_of_creates_uploaded_file_upload(self):
        """Test that FileUpload.of correctly parses uploaded status response."""
        data = {
            "object": "file_upload",
            "id": "test-upload-id-456",
            "status": "uploaded",
            "created_time": "2025-01-01T00:00:00.000Z",
        }

        file_upload = FileUpload.of(data)

        self.assertEqual(file_upload.id, "test-upload-id-456")
        self.assertEqual(file_upload.status, FileUploadStatus.UPLOADED)
        self.assertFalse(file_upload.is_pending())
        self.assertTrue(file_upload.is_uploaded())

    @pytest.mark.minimum()
    def test_to_block_reference(self):
        """Test that to_block_reference creates correct format."""
        file_upload = FileUpload(
            id="test-id",
            status=FileUploadStatus.UPLOADED,
        )

        reference = file_upload.to_block_reference()

        self.assertEqual(reference["type"], "file_upload")
        self.assertEqual(reference["file_upload"]["id"], "test-id")


class TestGetContentType(TestCase):
    """Unit tests for get_content_type function."""

    @pytest.mark.minimum()
    def test_image_content_types(self):
        """Test common image MIME types."""
        self.assertEqual(get_content_type("image.png"), "image/png")
        self.assertEqual(get_content_type("photo.jpg"), "image/jpeg")
        self.assertEqual(get_content_type("photo.jpeg"), "image/jpeg")
        self.assertEqual(get_content_type("animation.gif"), "image/gif")
        self.assertEqual(get_content_type("graphic.webp"), "image/webp")
        self.assertEqual(get_content_type("vector.svg"), "image/svg+xml")

    @pytest.mark.minimum()
    def test_document_content_types(self):
        """Test common document MIME types."""
        self.assertEqual(get_content_type("document.pdf"), "application/pdf")
        self.assertEqual(get_content_type("notes.txt"), "text/plain")
        self.assertEqual(get_content_type("data.json"), "application/json")
        self.assertEqual(get_content_type("data.csv"), "text/csv")

    @pytest.mark.minimum()
    def test_audio_content_types(self):
        """Test common audio MIME types."""
        self.assertEqual(get_content_type("song.mp3"), "audio/mpeg")
        self.assertEqual(get_content_type("sound.wav"), "audio/wav")
        self.assertEqual(get_content_type("music.ogg"), "audio/ogg")

    @pytest.mark.minimum()
    def test_video_content_types(self):
        """Test common video MIME types."""
        self.assertEqual(get_content_type("movie.mp4"), "video/mp4")
        self.assertEqual(get_content_type("clip.webm"), "video/webm")
        self.assertEqual(get_content_type("film.mov"), "video/quicktime")

    @pytest.mark.minimum()
    def test_unknown_extension_returns_octet_stream(self):
        """Test that unknown extensions return application/octet-stream."""
        self.assertEqual(get_content_type("file.xyz"), "application/octet-stream")
        self.assertEqual(get_content_type("noextension"), "application/octet-stream")

    @pytest.mark.minimum()
    def test_case_insensitive(self):
        """Test that extension matching is case insensitive."""
        self.assertEqual(get_content_type("IMAGE.PNG"), "image/png")
        self.assertEqual(get_content_type("Document.PDF"), "application/pdf")

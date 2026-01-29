"""Tests for media uploader utility."""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from instapost.media.uploader import MediaUploader


class TestMediaUploader:
    """Test MediaUploader class."""

    def test_upload_image_valid_file(self, temp_image_file):
        """Test uploading a valid image file."""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.text = 'https://catbox.moe/image.jpg\n'
            mock_post.return_value = mock_response

            url = MediaUploader.upload_image(temp_image_file)

            assert url == 'https://catbox.moe/image.jpg'
            assert mock_post.called

    def test_upload_video_valid_file(self, temp_video_file):
        """Test uploading a valid video file."""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.text = 'https://catbox.moe/video.mp4\n'
            mock_post.return_value = mock_response

            url = MediaUploader.upload_video(temp_video_file)

            assert url == 'https://catbox.moe/video.mp4'

    def test_upload_image_not_found(self):
        """Test uploading non-existent image."""
        with pytest.raises(FileNotFoundError):
            MediaUploader.upload_image('/path/to/nonexistent/image.jpg')

    def test_upload_unsupported_format(self, temp_image_file):
        """Test uploading unsupported file format."""
        with patch('pathlib.Path.suffix', '.xyz'):
            with pytest.raises(ValueError, match='Unsupported'):
                MediaUploader.upload_image(temp_image_file)

    def test_upload_generic_method(self, temp_image_file):
        """Test generic upload method."""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.text = 'https://catbox.moe/file.jpg\n'
            mock_post.return_value = mock_response

            url = MediaUploader.upload(temp_image_file)
            assert url == 'https://catbox.moe/file.jpg'

    def test_upload_catbox_error(self, temp_image_file):
        """Test handling Catbox upload errors."""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.text = 'error uploading file'
            mock_post.return_value = mock_response

            with pytest.raises(Exception):
                MediaUploader.upload_image(temp_image_file)

    @pytest.mark.parametrize('filename,is_valid', [
        ('image.jpg', True),
        ('photo.png', True),
        ('animation.gif', True),
        ('video.mp4', True),
        ('clip.mov', True),
        ('document.pdf', False),
        ('archive.zip', False),
        ('script.py', False),
    ])
    def test_supported_formats(self, filename, is_valid):
        """Test file format validation."""
        ext = Path(filename).suffix.lower()
        is_supported = ext in (MediaUploader.SUPPORTED_IMAGES | MediaUploader.SUPPORTED_VIDEOS)
        assert is_supported == is_valid

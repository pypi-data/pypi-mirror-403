"""
Media upload utilities for converting local files to public URLs.
Uses Catbox for all file uploads (images and videos).
"""

import os
import requests
from pathlib import Path


class MediaUploader:
    """Upload local media files to Catbox and return public URLs."""

    CATBOX_UPLOAD_URL = "https://catbox.moe/user/api.php"

    # Supported file extensions
    SUPPORTED_IMAGES = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    SUPPORTED_VIDEOS = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.m4v'}

    @classmethod
    def upload(cls, file_path: str) -> str:
        """
        Upload a media file (image or video) to Catbox.

        Args:
            file_path: Path to local media file

        Returns:
            Public URL of the uploaded file

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file type is not supported
            requests.RequestException: If upload fails
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Media file not found: {file_path}")

        file_ext = Path(file_path).suffix.lower()

        # Validate file type
        if file_ext not in (cls.SUPPORTED_IMAGES | cls.SUPPORTED_VIDEOS):
            raise ValueError(
                f"Unsupported file type: {file_ext}. "
                f"Supported: {cls.SUPPORTED_IMAGES | cls.SUPPORTED_VIDEOS}"
            )

        return cls._upload_to_catbox(file_path)

    @classmethod
    def upload_image(cls, image_path: str) -> str:
        """
        Upload an image to Catbox.

        Args:
            image_path: Path to local image file

        Returns:
            Public URL of the uploaded image
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        file_ext = Path(image_path).suffix.lower()
        if file_ext not in cls.SUPPORTED_IMAGES:
            raise ValueError(f"Unsupported image format: {file_ext}")

        return cls._upload_to_catbox(image_path)

    @classmethod
    def upload_video(cls, video_path: str) -> str:
        """
        Upload a video to Catbox.

        Args:
            video_path: Path to local video file

        Returns:
            Public URL of the uploaded video
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        file_ext = Path(video_path).suffix.lower()
        if file_ext not in cls.SUPPORTED_VIDEOS:
            raise ValueError(f"Unsupported video format: {file_ext}")

        return cls._upload_to_catbox(video_path)

    @classmethod
    def _upload_to_catbox(cls, file_path: str) -> str:
        """
        Internal method to upload file to Catbox.

        Args:
            file_path: Path to file

        Returns:
            Public URL

        Raises:
            requests.RequestException: If upload fails
        """
        with open(file_path, 'rb') as f:
            files = {'fileToUpload': f}
            data = {'reqtype': 'fileupload'}
            response = requests.post(cls.CATBOX_UPLOAD_URL, data=data, files=files)

        response.raise_for_status()
        url = response.text.strip()

        if not url or url.startswith('error'):
            raise requests.RequestException(f"Catbox upload failed: {url}")

        return url

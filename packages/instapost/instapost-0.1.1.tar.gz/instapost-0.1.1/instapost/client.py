from typing import Optional
import os

from .api.base import BaseInstagramClient
from .posting.image import ImagePoster
from .posting.reel import ReelPoster
from .posting.carousel import CarouselPoster
from .media.uploader import MediaUploader


class InstagramPoster(BaseInstagramClient):
    """Unified client for posting images, reels, and carousels to Instagram."""

    def __init__(self, access_token: str, ig_user_id: str):
        super().__init__(access_token, ig_user_id)
        self._image = ImagePoster(access_token, ig_user_id)
        self._reel = ReelPoster(access_token, ig_user_id)
        self._carousel = CarouselPoster(access_token, ig_user_id)

    def upload(self, *args, **kwargs) -> str:
        """Upload content. Use upload_image, upload_reel, or upload_carousel for specific types."""
        raise NotImplementedError("Use upload_image, upload_reel, or upload_carousel instead")

    def post(self, *args, **kwargs) -> dict:
        """Post content. Use post_image, post_reel, or post_carousel for specific types."""
        raise NotImplementedError("Use post_image, post_reel, or post_carousel instead")

    # Image methods
    def upload_image(self, image_url: str, caption: str = "") -> str:
        """Upload a single image and return container ID."""
        return self._image.upload(image_url, caption)

    def post_image(self, image_url: str, caption: str = "") -> dict:
        """Upload and publish a single image.

        Args:
            image_url: URL or local file path to image
            caption: Optional caption

        Returns:
            API response with published media ID
        """
        # Auto-upload if local file
        if os.path.exists(image_url):
            image_url = MediaUploader.upload_image(image_url)

        return self._image.post(image_url, caption)

    # Reel methods
    def upload_reel(
        self,
        video_url: str,
        caption: str = "",
        cover_url: Optional[str] = None,
        share_to_feed: bool = True,
        timeout: int = 120,
    ) -> str:
        """Upload a reel and return container ID."""
        return self._reel.upload(video_url, caption, cover_url, share_to_feed, timeout)

    def post_reel(
        self,
        video_url: str,
        caption: str = "",
        cover_url: Optional[str] = None,
        share_to_feed: bool = True,
        timeout: int = 120,
    ) -> dict:
        """Upload and publish a reel.

        Args:
            video_url: URL or local file path to video
            caption: Optional caption
            cover_url: Optional URL or local path to cover image
            share_to_feed: Whether to also share to feed
            timeout: Video processing timeout in seconds

        Returns:
            API response with published media ID
        """
        # Auto-upload if local files
        if os.path.exists(video_url):
            video_url = MediaUploader.upload_video(video_url)

        if cover_url and os.path.exists(cover_url):
            cover_url = MediaUploader.upload_image(cover_url)

        return self._reel.post(video_url, caption, cover_url, share_to_feed, timeout)

    # Carousel methods
    def upload_carousel(self, media_urls: list[dict], caption: str = "") -> str:
        """Upload a carousel and return container ID."""
        return self._carousel.upload(media_urls, caption)

    def post_carousel(self, media_urls: list[dict], caption: str = "") -> dict:
        """Upload and publish a carousel.

        Args:
            media_urls: List of dicts with 'media' (local file path or publicly accessible URL)
                       and 'type' keys. Type must be 'IMAGE' or 'VIDEO'
            caption: Optional caption

        Returns:
            API response with published media ID
        """
        # Auto-upload local files
        processed_urls = []
        for item in media_urls:
            media = item['media']
            if os.path.exists(media):
                media = MediaUploader.upload(media)

            processed_urls.append({
                'media': media,
                'type': item['type']
            })

        return self._carousel.post(processed_urls, caption)

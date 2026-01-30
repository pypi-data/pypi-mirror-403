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
    def upload_image(self, image: str, caption: str = "") -> str:
        """Upload a single image and return container ID."""
        return self._image.upload(image, caption)

    def post_image(self, image: str, caption: str = "") -> dict:
        """Upload and publish a single image.

        Args:
            image: URL or local file path to image
            caption: Optional caption

        Returns:
            API response with published media ID
        """
        # Auto-upload if local file
        if os.path.exists(image):
            image = MediaUploader.upload_image(image)

        return self._image.post(image, caption)

    # Reel methods
    def upload_reel(
        self,
        video: str,
        caption: str = "",
        cover: Optional[str] = None,
        share_to_feed: bool = True,
        timeout: int = 120,
    ) -> str:
        """Upload a reel and return container ID."""
        return self._reel.upload(video, caption, cover, share_to_feed, timeout)

    def post_reel(
        self,
        video: str,
        caption: str = "",
        cover: Optional[str] = None,
        share_to_feed: bool = True,
        timeout: int = 120,
    ) -> dict:
        """Upload and publish a reel.

        Args:
            video: URL or local file path to video
            caption: Optional caption
            cover: Optional URL or local path to cover image
            share_to_feed: Whether to also share to feed
            timeout: Video processing timeout in seconds

        Returns:
            API response with published media ID
        """
        # Auto-upload if local files
        if os.path.exists(video):
            video = MediaUploader.upload_video(video)

        if cover and os.path.exists(cover):
            cover = MediaUploader.upload_image(cover)

        return self._reel.post(video, caption, cover, share_to_feed, timeout)

    # Carousel methods
    def upload_carousel(self, media_items: list[dict], caption: str = "") -> str:
        """Upload a carousel and return container ID."""
        return self._carousel.upload(media_items, caption)

    def post_carousel(self, media_items: list[dict], caption: str = "") -> dict:
        """Upload and publish a carousel.

        Args:
            media_items: List of dicts with 'media' (local file path or publicly accessible URL)
                        and 'type' keys. Type must be 'IMAGE' or 'VIDEO'
            caption: Optional caption

        Returns:
            API response with published media ID
        """
        # Auto-upload local files
        processed_items = []
        for item in media_items:
            media = item['media']
            if os.path.exists(media):
                media = MediaUploader.upload(media)

            processed_items.append({
                'media': media,
                'type': item['type']
            })

        return self._carousel.post(processed_items, caption)

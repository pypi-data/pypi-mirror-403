from typing import Optional

from ..api.base import BaseInstagramClient


class ReelPoster(BaseInstagramClient):
    """Post reels to Instagram."""

    def upload(
        self,
        video: str,
        caption: str = "",
        cover: Optional[str] = None,
        share_to_feed: bool = True,
        timeout: int = 120,
    ) -> str:
        """
        Upload a reel to Instagram.

        Args:
            video: Local file path or publicly accessible URL of the video (MP4, max 1GB, 3-90 seconds).
            caption: Optional caption for the reel.
            cover: Optional local file path or URL for custom cover image.
            share_to_feed: Whether to also share the reel to the feed.
            timeout: Maximum time to wait for video processing in seconds.

        Returns:
            Container ID for publishing.
        """
        params = {
            "media_type": "REELS",
            "video_url": video,
            "caption": caption,
            "share_to_feed": str(share_to_feed).lower(),
        }
        if cover:
            params["cover_url"] = cover

        container_id = self._create_container(params)
        self._wait_for_container(container_id, timeout=timeout)
        return container_id

    def post(
        self,
        video: str,
        caption: str = "",
        cover: Optional[str] = None,
        share_to_feed: bool = True,
        timeout: int = 120,
    ) -> dict:
        """Upload and publish a reel."""
        return self.publish(self.upload(video, caption, cover, share_to_feed, timeout))

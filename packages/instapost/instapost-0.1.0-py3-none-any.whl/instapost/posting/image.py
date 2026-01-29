from ..api.base import BaseInstagramClient


class ImagePoster(BaseInstagramClient):
    """Post single images to Instagram."""

    def upload(self, image: str, caption: str = "") -> str:
        """
        Upload a single image to Instagram.

        Args:
            image: Local file path or publicly accessible URL of the image (JPEG, max 8MB).
            caption: Optional caption for the post.

        Returns:
            Container ID for publishing.
        """
        return self._create_container({"image_url": image, "caption": caption})

    def post(self, image: str, caption: str = "") -> dict:
        """Upload and publish a single image."""
        return self.publish(self.upload(image, caption))

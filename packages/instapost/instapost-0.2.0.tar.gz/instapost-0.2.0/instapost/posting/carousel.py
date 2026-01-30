from ..api.base import BaseInstagramClient


class CarouselPoster(BaseInstagramClient):
    """Post carousels (multiple images/videos) to Instagram."""

    MIN_ITEMS = 2
    MAX_ITEMS = 10

    def upload(self, media_items: list[dict], caption: str = "") -> str:
        """
        Upload a carousel to Instagram.

        Args:
            media_items: List of dicts with 'media' (local file path or publicly accessible URL)
                        and 'type' ('IMAGE' or 'VIDEO') keys.
            caption: Optional caption for the carousel.

        Returns:
            Container ID for publishing.
        """
        if not self.MIN_ITEMS <= len(media_items) <= self.MAX_ITEMS:
            raise ValueError(f"Carousel must have between {self.MIN_ITEMS} and {self.MAX_ITEMS} items")

        children_ids = [self._create_child(media) for media in media_items]
        return self._create_container({
            "media_type": "CAROUSEL",
            "children": ",".join(children_ids),
            "caption": caption,
        })

    def post(self, media_items: list[dict], caption: str = "") -> dict:
        """Upload and publish a carousel."""
        return self.publish(self.upload(media_items, caption))

    def _create_child(self, media: dict) -> str:
        """Create a child container for a carousel item."""
        media_type = media.get("type", "IMAGE").upper()
        params = {"is_carousel_item": "true"}

        if media_type == "IMAGE":
            params["image_url"] = media["media"]
        else:
            params["media_type"] = "VIDEO"
            params["video_url"] = media["media"]

        container_id = self._create_container(params)

        if media_type == "VIDEO":
            self._wait_for_container(container_id)

        return container_id

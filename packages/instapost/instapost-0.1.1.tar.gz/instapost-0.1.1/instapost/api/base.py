import requests
import time
from abc import ABC, abstractmethod

from ..exceptions import ContainerProcessingError, ContainerTimeoutError


class BaseInstagramClient(ABC):
    """Base class for Instagram API clients."""

    BASE_URL = "https://graph.instagram.com"

    def __init__(self, access_token: str, ig_user_id: str):
        self.access_token = access_token
        self.ig_user_id = ig_user_id

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make a request to the Graph API."""
        url = f"{self.BASE_URL}/{endpoint}"
        kwargs.setdefault("params", {})["access_token"] = self.access_token
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()

    def _create_container(self, params: dict) -> str:
        """Create a media container and return its ID."""
        result = self._request("POST", "me/media", params=params)
        return result["id"]

    def _publish_container(self, container_id: str) -> dict:
        """Publish a media container."""
        return self._request(
            "POST",
            "me/media_publish",
            params={"creation_id": container_id},
        )

    def _wait_for_container(self, container_id: str, timeout: int = 60, interval: int = 5) -> None:
        """Wait for a media container to finish processing."""
        elapsed = 0
        while elapsed < timeout:
            result = self._request("GET", container_id, params={"fields": "status_code,status"})
            status = result.get("status_code")

            if status == "FINISHED":
                return
            if status == "ERROR":
                raise ContainerProcessingError(f"Container processing failed: {result.get('status')}")

            time.sleep(interval)
            elapsed += interval

        raise ContainerTimeoutError(f"Container {container_id} did not finish processing in {timeout}s")

    def verify(self) -> dict:
        """Verify credentials and return account info."""
        return self._request(
            "GET",
            "me",
            params={"fields": "id,username,name"},
        )

    def publish(self, container_id: str) -> dict:
        """
        Publish a previously uploaded media container.

        Args:
            container_id: The container ID returned by upload().

        Returns:
            API response with the published media ID.
        """
        return self._publish_container(container_id)

    @abstractmethod
    def upload(self, *args, **kwargs) -> str:
        """Upload content and return the container ID."""
        pass

    def post(self, *args, **kwargs) -> dict:
        """Upload and publish content in one step."""
        container_id = self.upload(*args, **kwargs)
        return self.publish(container_id)

"""Tests for exceptions."""
import pytest

from instapost.exceptions import (
    InstagramAPIError,
    ContainerProcessingError,
    ContainerTimeoutError,
)


class TestExceptions:
    """Test exception classes."""

    def test_instagram_api_error(self):
        """Test InstagramAPIError can be raised and caught."""
        with pytest.raises(InstagramAPIError):
            raise InstagramAPIError("API error occurred")

    def test_container_processing_error(self):
        """Test ContainerProcessingError is subclass of InstagramAPIError."""
        error = ContainerProcessingError("Processing failed")
        assert isinstance(error, InstagramAPIError)

    def test_container_timeout_error(self):
        """Test ContainerTimeoutError is subclass of InstagramAPIError."""
        error = ContainerTimeoutError("Timeout waiting for container")
        assert isinstance(error, InstagramAPIError)

    def test_exception_messages(self):
        """Test exception messages are preserved."""
        msg = "Custom error message"

        with pytest.raises(InstagramAPIError, match=msg):
            raise InstagramAPIError(msg)

        with pytest.raises(ContainerProcessingError, match=msg):
            raise ContainerProcessingError(msg)

        with pytest.raises(ContainerTimeoutError, match=msg):
            raise ContainerTimeoutError(msg)

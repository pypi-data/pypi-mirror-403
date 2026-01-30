class InstagramAPIError(Exception):
    """Raised when Instagram API returns an error."""
    pass


class ContainerProcessingError(InstagramAPIError):
    """Raised when a media container fails to process."""
    pass


class ContainerTimeoutError(InstagramAPIError):
    """Raised when a media container times out during processing."""
    pass

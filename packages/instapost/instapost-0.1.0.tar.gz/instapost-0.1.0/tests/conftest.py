import pytest
from unittest.mock import patch
import tempfile
import os


@pytest.fixture
def mock_requests():
    """Mock requests library."""
    with patch('instapost.api.base.requests') as mock:
        yield mock


@pytest.fixture
def mock_os_path_exists():
    """Mock os.path.exists to control file existence checks."""
    with patch('os.path.exists') as mock:
        yield mock


@pytest.fixture
def instagram_client():
    """Create a test Instagram client with mocked requests."""
    from instapost import InstagramPoster
    return InstagramPoster(access_token='test_token_123', ig_user_id='user_123')


@pytest.fixture
def base_client():
    """Create a test base client."""
    from instapost.api.base import BaseInstagramClient

    class TestClient(BaseInstagramClient):
        def upload(self):
            return "test_container_id"

    return TestClient(access_token='test_token_123', ig_user_id='user_123')


@pytest.fixture
def temp_image_file():
    """Create a temporary image file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        f.write(b'fake image data')
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_video_file():
    """Create a temporary video file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
        f.write(b'fake video data')
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

"""Tests for API base client."""
import pytest
from unittest.mock import Mock, patch

from instapost.api.base import BaseInstagramClient
from instapost.exceptions import ContainerProcessingError, ContainerTimeoutError


class ConcreteClient(BaseInstagramClient):
    """Concrete implementation for testing."""
    def upload(self):
        return "test_id"


class TestBaseInstagramClient:
    """Test BaseInstagramClient class."""

    def test_client_initialization(self):
        """Test client initializes with correct credentials."""
        client = ConcreteClient(access_token='token123', ig_user_id='user456')
        assert client.access_token == 'token123'
        assert client.ig_user_id == 'user456'
        assert client.BASE_URL == 'https://graph.instagram.com'

    def test_request_success(self):
        """Test successful API request."""
        client = ConcreteClient(access_token='token', ig_user_id='user')

        with patch('instapost.api.base.requests.request') as mock_request:
            mock_response = Mock()
            mock_response.json.return_value = {'id': 'container_123', 'status': 'OK'}
            mock_request.return_value = mock_response

            result = client._request('GET', 'me/media')

            assert result == {'id': 'container_123', 'status': 'OK'}
            assert mock_request.called
            call_kwargs = mock_request.call_args.kwargs
            assert call_kwargs['params']['access_token'] == 'token'

    def test_create_container(self):
        """Test creating a media container."""
        client = ConcreteClient(access_token='token', ig_user_id='user')

        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {'id': 'container_456'}

            container_id = client._create_container({'caption': 'Test'})

            assert container_id == 'container_456'
            mock_request.assert_called_once_with('POST', 'me/media', params={'caption': 'Test'})

    def test_publish_container(self):
        """Test publishing a container."""
        client = ConcreteClient(access_token='token', ig_user_id='user')

        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {'media_id': 'post_789'}

            result = client._publish_container('container_456')

            assert result == {'media_id': 'post_789'}
            mock_request.assert_called_once_with(
                'POST',
                'me/media_publish',
                params={'creation_id': 'container_456'}
            )

    def test_wait_for_container_finished(self):
        """Test waiting for container to finish processing."""
        client = ConcreteClient(access_token='token', ig_user_id='user')

        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {'status_code': 'FINISHED'}

            client._wait_for_container('container_123', timeout=10)
            assert mock_request.called

    def test_wait_for_container_error(self):
        """Test handling container processing errors."""
        client = ConcreteClient(access_token='token', ig_user_id='user')

        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {'status_code': 'ERROR', 'status': 'Processing failed'}

            with pytest.raises(ContainerProcessingError):
                client._wait_for_container('container_123')

    def test_wait_for_container_timeout(self):
        """Test container processing timeout."""
        client = ConcreteClient(access_token='token', ig_user_id='user')

        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {'status_code': 'PROCESSING'}

            with pytest.raises(ContainerTimeoutError):
                client._wait_for_container('container_123', timeout=1, interval=0.5)

    def test_verify_credentials(self):
        """Test credential verification."""
        client = ConcreteClient(access_token='token', ig_user_id='user')

        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {
                'id': 'user_123',
                'username': 'testuser',
                'name': 'Test User'
            }

            result = client.verify()

            assert result['username'] == 'testuser'
            mock_request.assert_called_once_with(
                'GET',
                'me',
                params={'fields': 'id,username,name'}
            )

    def test_publish_container_method(self):
        """Test publish method."""
        client = ConcreteClient(access_token='token', ig_user_id='user')

        with patch.object(client, '_publish_container') as mock_publish:
            mock_publish.return_value = {'media_id': 'post_123'}

            result = client.publish('container_456')

            assert result == {'media_id': 'post_123'}

    def test_post_method(self):
        """Test post method (upload + publish)."""
        client = ConcreteClient(access_token='token', ig_user_id='user')

        with patch.object(client, 'upload', return_value='container_789'):
            with patch.object(client, 'publish', return_value={'media_id': 'post_999'}):
                result = client.post()

                assert result == {'media_id': 'post_999'}

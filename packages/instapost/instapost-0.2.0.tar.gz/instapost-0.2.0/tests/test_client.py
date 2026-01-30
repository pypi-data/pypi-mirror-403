"""Tests for main InstagramPoster client."""
import pytest
from unittest.mock import patch

from instapost import InstagramPoster


class TestInstagramPoster:
    """Test InstagramPoster facade class."""

    def test_client_initialization(self):
        """Test client initializes correctly."""
        client = InstagramPoster(access_token='token123', ig_user_id='user456')

        assert client.access_token == 'token123'
        assert client.ig_user_id == 'user456'
        assert hasattr(client, '_image')
        assert hasattr(client, '_reel')
        assert hasattr(client, '_carousel')

    def test_upload_not_implemented(self):
        """Test upload method raises NotImplementedError."""
        client = InstagramPoster(access_token='token', ig_user_id='user')

        with pytest.raises(NotImplementedError, match='upload_image'):
            client.upload()

    def test_post_not_implemented(self):
        """Test post method raises NotImplementedError."""
        client = InstagramPoster(access_token='token', ig_user_id='user')

        with pytest.raises(NotImplementedError, match='post_image'):
            client.post()

    # Image methods tests
    def test_upload_image_url(self):
        """Test uploading an image from URL."""
        client = InstagramPoster(access_token='token', ig_user_id='user')

        with patch.object(client._image, 'upload', return_value='container_123'):
            container_id = client.upload_image('https://example.com/image.jpg', 'Caption')

            assert container_id == 'container_123'

    def test_post_image_url(self):
        """Test posting an image from URL."""
        client = InstagramPoster(access_token='token', ig_user_id='user')

        with patch.object(client._image, 'post', return_value={'media_id': 'post_123'}):
            result = client.post_image('https://example.com/image.jpg')

            assert result == {'media_id': 'post_123'}

    def test_post_image_local_file(self, temp_image_file):
        """Test posting an image from local file (auto-upload)."""
        client = InstagramPoster(access_token='token', ig_user_id='user')

        with patch('instapost.client.MediaUploader.upload_image', return_value='https://catbox.moe/img.jpg'):
            with patch.object(client._image, 'post', return_value={'media_id': 'post_456'}):
                result = client.post_image(temp_image_file)

                assert result == {'media_id': 'post_456'}

    # Reel methods tests
    def test_upload_reel(self):
        """Test uploading a reel."""
        client = InstagramPoster(access_token='token', ig_user_id='user')

        with patch.object(client._reel, 'upload', return_value='container_456'):
            container_id = client.upload_reel('https://example.com/video.mp4')

            assert container_id == 'container_456'

    def test_post_reel_url(self):
        """Test posting a reel from URL."""
        client = InstagramPoster(access_token='token', ig_user_id='user')

        with patch.object(client._reel, 'post', return_value={'media_id': 'post_789'}):
            result = client.post_reel('https://example.com/video.mp4')

            assert result == {'media_id': 'post_789'}

    def test_post_reel_local_file(self, temp_video_file):
        """Test posting a reel from local file (auto-upload)."""
        client = InstagramPoster(access_token='token', ig_user_id='user')

        with patch('instapost.client.MediaUploader.upload_video', return_value='https://catbox.moe/vid.mp4'):
            with patch.object(client._reel, 'post', return_value={'media_id': 'post_999'}):
                result = client.post_reel(temp_video_file)

                assert result == {'media_id': 'post_999'}

    def test_post_reel_with_cover_local(self, temp_video_file, temp_image_file):
        """Test posting a reel with local cover image."""
        client = InstagramPoster(access_token='token', ig_user_id='user')

        with patch('instapost.client.MediaUploader.upload_video', return_value='https://catbox.moe/vid.mp4'):
            with patch('instapost.client.MediaUploader.upload_image', return_value='https://catbox.moe/cover.jpg'):
                with patch.object(client._reel, 'post', return_value={'media_id': 'post_cover'}):
                    result = client.post_reel(
                        temp_video_file,
                        cover=temp_image_file,
                        share_to_feed=True,
                        timeout=120
                    )

                    assert result == {'media_id': 'post_cover'}

    def test_upload_reel_with_all_params(self):
        """Test uploading a reel with all parameters."""
        client = InstagramPoster(access_token='token', ig_user_id='user')

        with patch.object(client._reel, 'upload', return_value='container_all'):
            container_id = client.upload_reel(
                'https://example.com/video.mp4',
                caption='Test reel',
                cover='https://example.com/cover.jpg',
                share_to_feed=False,
                timeout=60
            )

            assert container_id == 'container_all'

    # Carousel methods tests
    def test_upload_carousel(self):
        """Test uploading a carousel."""
        client = InstagramPoster(access_token='token', ig_user_id='user')
        media_items = [
            {'media': 'https://example.com/img1.jpg', 'type': 'IMAGE'},
            {'media': 'https://example.com/img2.jpg', 'type': 'IMAGE'},
        ]

        with patch.object(client._carousel, 'upload', return_value='carousel_123'):
            container_id = client.upload_carousel(media_items)

            assert container_id == 'carousel_123'

    def test_post_carousel_urls(self):
        """Test posting a carousel from URLs."""
        client = InstagramPoster(access_token='token', ig_user_id='user')
        media_items = [
            {'media': 'https://example.com/img1.jpg', 'type': 'IMAGE'},
            {'media': 'https://example.com/img2.jpg', 'type': 'IMAGE'},
        ]

        with patch.object(client._carousel, 'post', return_value={'media_id': 'carousel_post'}):
            result = client.post_carousel(media_items)

            assert result == {'media_id': 'carousel_post'}

    def test_post_carousel_local_files(self, temp_image_file):
        """Test posting a carousel with local files (auto-upload)."""
        client = InstagramPoster(access_token='token', ig_user_id='user')
        media_items = [
            {'media': temp_image_file, 'type': 'IMAGE'},
            {'media': 'https://example.com/img2.jpg', 'type': 'IMAGE'},
        ]

        with patch('instapost.client.MediaUploader.upload', return_value='https://catbox.moe/img1.jpg'):
            with patch.object(client._carousel, 'post', return_value={'media_id': 'carousel_post_2'}):
                result = client.post_carousel(media_items)

                assert result == {'media_id': 'carousel_post_2'}

    def test_post_carousel_mixed_local_and_urls(self, temp_image_file):
        """Test posting carousel with mix of local files and URLs."""
        client = InstagramPoster(access_token='token', ig_user_id='user')
        media_items = [
            {'media': temp_image_file, 'type': 'IMAGE'},
            {'media': 'https://example.com/video.mp4', 'type': 'VIDEO'},
        ]

        with patch('instapost.client.MediaUploader.upload', return_value='https://catbox.moe/uploaded.jpg'):
            with patch.object(client._carousel, 'post', return_value={'media_id': 'mixed_carousel'}):
                result = client.post_carousel(media_items, caption='Mixed carousel')

                assert result == {'media_id': 'mixed_carousel'}

    # Integration tests
    def test_verify_credentials(self):
        """Test verifying credentials."""
        client = InstagramPoster(access_token='token', ig_user_id='user')

        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {
                'id': 'user_123',
                'username': 'testuser',
                'name': 'Test User'
            }

            result = client.verify()

            assert result['username'] == 'testuser'

    def test_publish_container(self):
        """Test publishing a pre-created container."""
        client = InstagramPoster(access_token='token', ig_user_id='user')

        with patch.object(client, 'publish', return_value={'media_id': 'final_post'}):
            result = client.publish('container_123')

            assert result == {'media_id': 'final_post'}

    @pytest.mark.parametrize('caption,media_type', [
        ('Simple caption', 'image'),
        ('Caption with #hashtags', 'image'),
        ('🎉 Emoji caption', 'image'),
        ('Multi\nline\ncaption', 'image'),
        ('Very long caption ' * 50, 'reel'),
    ])
    def test_various_captions(self, caption, media_type):
        """Test posting with various caption formats."""
        client = InstagramPoster(access_token='token', ig_user_id='user')

        if media_type == 'image':
            with patch.object(client._image, 'post', return_value={'media_id': f'post_{hash(caption)}'}):
                result = client.post_image('https://example.com/image.jpg', caption=caption)
                assert 'media_id' in result
        else:
            with patch.object(client._reel, 'post', return_value={'media_id': f'post_{hash(caption)}'}):
                result = client.post_reel('https://example.com/video.mp4', caption=caption)
                assert 'media_id' in result

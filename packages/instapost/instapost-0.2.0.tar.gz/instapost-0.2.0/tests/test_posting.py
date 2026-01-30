"""Tests for posting classes (Image, Reel, Carousel)."""
import pytest
from unittest.mock import patch

from instapost.posting.image import ImagePoster
from instapost.posting.reel import ReelPoster
from instapost.posting.carousel import CarouselPoster


class TestImagePoster:
    """Test ImagePoster class."""

    def test_upload_image(self):
        """Test uploading a single image."""
        poster = ImagePoster(access_token='token', ig_user_id='user')

        with patch.object(poster, '_create_container') as mock_create:
            mock_create.return_value = 'container_123'

            container_id = poster.upload('https://example.com/image.jpg', 'Test caption')

            assert container_id == 'container_123'
            mock_create.assert_called_once_with({
                'image_url': 'https://example.com/image.jpg',
                'caption': 'Test caption'
            })

    def test_post_image(self):
        """Test posting a single image (upload + publish)."""
        poster = ImagePoster(access_token='token', ig_user_id='user')

        with patch.object(poster, 'upload', return_value='container_456'):
            with patch.object(poster, 'publish', return_value={'media_id': 'post_123'}):
                result = poster.post('https://example.com/image.jpg')

                assert result == {'media_id': 'post_123'}


class TestReelPoster:
    """Test ReelPoster class."""

    def test_upload_reel(self):
        """Test uploading a reel."""
        poster = ReelPoster(access_token='token', ig_user_id='user')

        with patch.object(poster, '_create_container', return_value='container_789'):
            with patch.object(poster, '_wait_for_container'):
                container_id = poster.upload(
                    'https://example.com/video.mp4',
                    caption='Reel caption',
                    cover='https://example.com/cover.jpg',
                    share_to_feed=True,
                    timeout=120
                )

                assert container_id == 'container_789'

    def test_upload_reel_minimal(self):
        """Test uploading a reel with minimal parameters."""
        poster = ReelPoster(access_token='token', ig_user_id='user')

        with patch.object(poster, '_create_container', return_value='container_101'):
            with patch.object(poster, '_wait_for_container'):
                container_id = poster.upload('https://example.com/video.mp4')

                assert container_id == 'container_101'

    def test_upload_reel_without_cover(self):
        """Test uploading a reel without cover image."""
        poster = ReelPoster(access_token='token', ig_user_id='user')

        with patch.object(poster, '_create_container', return_value='container_111'):
            with patch.object(poster, '_wait_for_container'):
                poster.upload('https://example.com/video.mp4', cover=None)

                # Verify _create_container was called
                call_args = poster._create_container.call_args[0][0]
                assert 'cover_url' not in call_args

    def test_post_reel(self):
        """Test posting a reel."""
        poster = ReelPoster(access_token='token', ig_user_id='user')

        with patch.object(poster, 'upload', return_value='container_222'):
            with patch.object(poster, 'publish', return_value={'media_id': 'post_456'}):
                result = poster.post('https://example.com/video.mp4')

                assert result == {'media_id': 'post_456'}


class TestCarouselPoster:
    """Test CarouselPoster class."""

    def test_upload_carousel_valid(self):
        """Test uploading a valid carousel."""
        poster = CarouselPoster(access_token='token', ig_user_id='user')
        media_items = [
            {'media': 'https://example.com/img1.jpg', 'type': 'IMAGE'},
            {'media': 'https://example.com/img2.jpg', 'type': 'IMAGE'},
        ]

        with patch.object(poster, '_create_child', side_effect=['child_1', 'child_2']):
            with patch.object(poster, '_create_container', return_value='carousel_123'):
                container_id = poster.upload(media_items, caption='Carousel')

                assert container_id == 'carousel_123'

    def test_upload_carousel_too_few_items(self):
        """Test carousel with too few items."""
        poster = CarouselPoster(access_token='token', ig_user_id='user')
        media_items = [
            {'media': 'https://example.com/img1.jpg', 'type': 'IMAGE'},
        ]

        with pytest.raises(ValueError, match='between'):
            poster.upload(media_items)

    def test_upload_carousel_too_many_items(self):
        """Test carousel with too many items."""
        poster = CarouselPoster(access_token='token', ig_user_id='user')
        media_items = [{'media': f'https://example.com/img{i}.jpg', 'type': 'IMAGE'} for i in range(12)]

        with pytest.raises(ValueError, match='between'):
            poster.upload(media_items)

    def test_upload_carousel_mixed_media(self):
        """Test carousel with mixed image and video."""
        poster = CarouselPoster(access_token='token', ig_user_id='user')
        media_items = [
            {'media': 'https://example.com/img1.jpg', 'type': 'IMAGE'},
            {'media': 'https://example.com/video1.mp4', 'type': 'VIDEO'},
        ]

        with patch.object(poster, '_create_child', side_effect=['child_1', 'child_2']):
            with patch.object(poster, '_create_container', return_value='carousel_456'):
                container_id = poster.upload(media_items)

                assert container_id == 'carousel_456'

    def test_create_child_image(self):
        """Test creating a carousel child item (image)."""
        poster = CarouselPoster(access_token='token', ig_user_id='user')
        media = {'media': 'https://example.com/img.jpg', 'type': 'IMAGE'}

        with patch.object(poster, '_create_container', return_value='child_img_123'):
            child_id = poster._create_child(media)

            assert child_id == 'child_img_123'

    def test_create_child_video(self):
        """Test creating a carousel child item (video)."""
        poster = CarouselPoster(access_token='token', ig_user_id='user')
        media = {'media': 'https://example.com/video.mp4', 'type': 'VIDEO'}

        with patch.object(poster, '_create_container', return_value='child_vid_456'):
            with patch.object(poster, '_wait_for_container'):
                child_id = poster._create_child(media)

                assert child_id == 'child_vid_456'

    def test_post_carousel(self):
        """Test posting a carousel."""
        poster = CarouselPoster(access_token='token', ig_user_id='user')

        with patch.object(poster, 'upload', return_value='carousel_789'):
            with patch.object(poster, 'publish', return_value={'media_id': 'post_789'}):
                result = poster.post([
                    {'media': 'https://example.com/img1.jpg', 'type': 'IMAGE'},
                    {'media': 'https://example.com/img2.jpg', 'type': 'IMAGE'},
                ])

                assert result == {'media_id': 'post_789'}

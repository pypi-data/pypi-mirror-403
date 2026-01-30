# instapost


<img src="logo.png" width="300px" align="right" alt="logo">

A simple and powerful Python library for posting to Instagram using the Instagram Graph API. 

Post images, reels, and carousels with just a few lines of code. Auto-upload local files or use remote URLs. 




**How it works:**

```python
from instapost import InstagramPoster

poster = InstagramPoster(access_token="YOUR_TOKEN",
                         ig_user_id="YOUR_IG_ID"
)

poster.post_image(image="./photo.jpg",
                  caption="Check this out! 📸")
```

That's it. Your photo is on Instagram.

## Setup (5 minutes)

**What you need:**
- Instagram Business account (connected to Facebook)
- Meta for Developers account (free)

**Steps:**

1. Create a Meta App → [developers.facebook.com/apps/create](https://developers.facebook.com/apps/create/)
2. Click **Add Product** and set up Instagram
3. In **App Roles > Roles**, assign **Instagram Tester** to your account
4. Go to **Instagram > API Setup with Instagram login**, add your account, click **Generate token**
5. Copy the token—you're done!

✨ **That's it.** No app review needed for personal use. Your token works immediately in Development Mode.

## Usage

```python
from instapost import InstagramPoster

poster = InstagramPoster(
    access_token="YOUR_TOKEN",
    ig_user_id="YOUR_IG_ID"
)

# Post an image
poster.post_image(image="./photo.jpg", caption="Check this out! 📸")

# Post a reel
poster.post_reel(video="./video.mp4", caption="New reel! 🎬", share_to_feed=True)

# Post a carousel
poster.post_carousel(
    media_items=[
        {"media": "./photo1.jpg", "type": "IMAGE"},
        {"media": "./video.mp4", "type": "VIDEO"},
    ],
    caption="Swipe through! 👉"
)

# Verify you're connected
print(poster.verify()['username'])
```

**Local files?** Just pass the file path—instapost auto-uploads to Catbox. Remote URLs work too. Mix them in one post.

## Requirements

- Instagram Business account connected to Facebook
- Meta for Developers account (free)
- Python 3.7+

## Installation

```bash
pip install instapost
```

## Media Specs

| Type | Format | Size | Duration |
|------|--------|------|----------|
| Images | JPEG, PNG, WebP, GIF | ≤ 8MB | — |
| Reels | MP4 | ≤ 1GB | 3-90s |
| Carousel | 2-10 items | per item | — |

## How it works

- **Local files** → Auto-upload to Catbox → Send to Instagram API
- **Remote URLs** → Send directly to Instagram API

## Learn more

- [Instagram Graph API Docs](https://developers.facebook.com/docs/instagram-platform/content-publishing)
- [Meta for Developers](https://developers.facebook.com)

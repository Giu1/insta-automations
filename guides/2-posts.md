# 2 · Scheduling posts

File: **`config/posts.yaml`**

## One post

```yaml
  - id: 2026-10-01-autumn-menu
    brand: marketermilano
    publish_at: "2026-10-01 09:00"
    type: image
    media_url: https://your-site.com/images/autumn-menu.jpg
    caption: |
      Our autumn menu is here 🍂
      Come try it this week.
      #autumn #menu
```

| Field | Rules |
|---|---|
| `id` | Unique. Use the date plus a word, e.g. `2026-10-01-autumn-menu`. **Never reuse an id**: the app remembers ids it already published so nothing goes out twice. Changing an id after publishing would publish again. |
| `brand` | Must exist in `config/brands.yaml`. |
| `publish_at` | `"YYYY-MM-DD HH:MM"` in the brand's timezone (see brands.yaml). Goes out within 1 minute of that time. Past dates publish immediately the next time the app runs. |
| `type` | `image` (photo post), `reel` (video), `story` (image or video). |
| `media_url` | A **public** `https://` link straight to the file. Instagram downloads it. Google Drive "share" links or Dropbox pages do **not** work; use a direct file link (Dropbox: change `dl=0` to `raw=1`; or use your website / an image host). JPG/PNG for images, MP4 for video (up to 90 s for reels). |
| `caption` | Text of the post. The `|` lets you write several lines. Stories ignore the caption. |

## Where to host images/videos for free

- Your own website (best).
- GitHub: put the file in the `docs/media/` folder of this project and use `https://<user>.github.io/<repo>/media/file.jpg`.
- Cloudinary / Imgur direct links.

## Checking what is scheduled

```
python -m app.tools posts
```

Shows each post with `waiting`, `published <id>` or `FAILED: <reason>`. If a post failed, fix the cause (usually the media link), give it a **new id**, and it will be retried.

## Testing a post right now

```
python -m app.tools publish-now 2026-10-01-autumn-menu
```

This really publishes on Instagram; use a test post.

## Limits

Instagram allows about 25–100 API posts per account per day. Keep it reasonable.

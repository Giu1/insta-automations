# Insta Automations

Multi-brand Instagram automation using **only the official Meta Graph API**:

- Schedule image / Reels / Stories posts
- Public replies when a comment contains specific words
- Auto-replies in DMs **only after the person messages first** (Instagram’s 24-hour window)

No browser bots, no cold DMs, no account-creation scripts.

## Architecture

```
Instagram / Messenger  --webhooks-->  FastAPI  --rules.yaml-->  Graph API replies
                                              |
                         /api/posts           +-- SQLite queue --> publisher (every 30s)
                                              |                   Graph: media -> wait -> media_publish
                         brands.yaml + Page tokens in .env
```

Each **brand** is one Instagram Professional account linked to a Facebook Page. Incoming webhooks are routed by Instagram user id or Page id.

## Meta app setup (once)

1. Convert each Instagram account to **Professional** and attach it to a **Facebook Page**.
2. Create a Meta app → add **Instagram** + **Webhooks**.
3. Permissions to request (App Review for other people’s accounts; your own Pages can use them in Dev mode):
   - `instagram_business_basic`
   - `instagram_business_content_publish`
   - `instagram_manage_comments`
   - `instagram_manage_messages`
   - `pages_manage_metadata` / `pages_read_engagement` as required by current docs
4. Subscribe the Page/Instagram account to webhook fields: `comments`, `messages`.
5. Generate a **long-lived Page access token** per brand. Put it in `.env` as `BRAND_*_PAGE_TOKEN`.
6. Callback URL: `https://<your-public-host>/webhooks/meta`  
   Verify token must match `META_WEBHOOK_VERIFY_TOKEN`.

Local dev: expose the app with ngrok or Cloudflare Tunnel so Meta can POST webhooks.

Official guides:

- [Content publishing](https://developers.facebook.com/docs/instagram-platform/content-publishing)
- [Instagram webhooks](https://developers.facebook.com/docs/graph-api/webhooks/getting-started/webhooks-for-instagram)
- [Instagram messaging](https://developers.facebook.com/docs/messenger-platform/instagram)

## Run locally

```powershell
cd C:\Users\lucas\Pictures\Insta_Automations
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# edit .env, config\brands.yaml, config\rules.yaml
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

## Schedule a post

Media URLs must be **publicly fetchable by Meta** (not localhost).

```powershell
curl -X POST http://127.0.0.1:8080/api/posts `
  -H "X-API-Key: change-me" `
  -H "Content-Type: application/json" `
  -d '{
    "brand": "acme",
    "caption": "Morning brew",
    "image_url": "https://example.com/photo.jpg",
    "media_type": "IMAGE",
    "publish_at": "2026-09-10T08:00:00+00:00"
  }'
```

The worker publishes due items every 30 seconds (container → `FINISHED` → `media_publish`). Stay under Meta’s daily publish cap per account.

## Keyword replies

Edit `config/rules.yaml`. **First matching rule wins.**

- **Comments** → public reply on that comment.
- **DMs** → `me/messages` to the sender IGSID. Echoes and your own account are ignored.
- `"*"` is the fallback. With `dm_default_once_per_day: true`, that fallback is sent at most once per sender per 24 hours so you do not loop.

You cannot legally/API-wise open a DM with someone who has never messaged you. This app never does that.

## Limits and policy

- Only Professional accounts you control (or that completed Facebook Login for Business).
- DMs: user-initiated 24-hour messaging window.
- Do not use this for spam, mass follow, or unsolicited outreach.

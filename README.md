# Insta Automations

Small, auditable service that uses **only the official Instagram API (Instagram Login)** to:

- reply publicly to **comments** that contain configured keywords,
- reply to **Direct messages** from people who message first (24-hour window),
- **publish scheduled posts**, reels and stories from a content calendar,

in **English, Portuguese (PT / BR) and Spanish**, choosing the language the person wrote in.

It never sends unsolicited messages, never follows/likes, never scrapes, and never creates accounts.

## For editors (no coding)

Edit the files in `config/` and run the check. Start with **[guides/README.md](guides/README.md)**.

| File | Purpose |
|---|---|
| `config/replies.yaml` | keyword rules and replies in 4 languages |
| `config/posts.yaml` | scheduled posts |
| `config/brands.yaml` | Instagram accounts managed |

## For the technical person

```
pip install -r requirements.txt
copy .env.example .env         # fill INSTAGRAM_APP_SECRET, WEBHOOK_VERIFY_TOKEN, BRAND_*_TOKEN
python -m app.tools check      # validates config + tokens
python -m app.tools subscribe  # enables comments/messages webhooks
uvicorn app.main:app --port 8080
```

Endpoints: `GET/POST /webhooks/meta` (Meta), `GET /health`, `GET /privacy`, `GET /data-deletion`, `POST /deauthorize`.

Hosting and Meta setup: [guides/5-hosting.md](guides/5-hosting.md), [guides/6-meta-app-review.md](guides/6-meta-app-review.md).

## Code map (≈600 lines)

```
app/
  main.py        FastAPI app, scheduler (publish every minute, refresh tokens daily), legal routes
  webhooks.py    signature check, comment/message handlers
  replies.py     keyword matching -> which reply
  i18n.py        language detection (en / pt-PT / pt-BR / es) and translation fallback
  publisher.py   publishes due posts from posts.yaml
  instagram.py   Instagram API client
  tokens.py      token lookup + daily refresh
  config.py      loads/validates brands.yaml, replies.yaml, posts.yaml
  db.py          SQLite: seen events, welcomes sent, published posts, refreshed tokens
  tools.py       CLI: check, try, posts, whoami, publish-now, subscribe
docs/            privacy + data-deletion pages (GitHub Pages)
guides/          plain-language documentation
```

## Data handling

Stored: Instagram account ids, access tokens (env / SQLite), comment and message ids (deduplication), sender ids for 24h welcome throttling, scheduled post results. Nothing else. See `docs/privacy.html`.

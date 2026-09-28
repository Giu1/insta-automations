# 5 · Running it 24/7 (for the technical person)

Instagram sends comments and messages to a URL. That URL must be online all the time, so the app needs a small always-on server. GitHub Actions is **not** suitable (jobs stop after minutes); GitHub Pages only hosts the static legal pages.

## Recommended free setup

| Piece | Service | Notes |
|---|---|---|
| Privacy / data-deletion pages | GitHub Pages (`docs/` folder) | Already live: https://giu1.github.io/insta-automations/ |
| The app (webhooks + scheduler) | Render.com free web service, Fly.io, or Railway | `render.yaml` is included: "New → Blueprint" and point it at the repo |
| Secrets | The host's *Environment* settings | Never put `.env` in git |

Render free tier sleeps after 15 minutes without traffic; Meta's webhook call wakes it, but the first reply can take ~30 s and the 1-minute scheduler pauses while asleep. Add a free uptime pinger (e.g. cron-job.org → `/health` every 10 minutes) to keep it awake, or use a paid tier.

## Environment variables on the host

```
INSTAGRAM_APP_SECRET=...
WEBHOOK_VERIFY_TOKEN=...
BRAND_MARKETERMILANO_TOKEN=...
```

Tokens refreshed by the app are saved in the database, so use a persistent disk (Render: add a disk mounted at `/app/data`) or set `DATABASE_URL` to a hosted Postgres. Without persistence the app still works; it just falls back to the `.env` token after a redeploy.

## After deploying

1. Meta App Dashboard → Instagram → *Configure webhooks*: Callback `https://<your-host>/webhooks/meta`, Verify token = `WEBHOOK_VERIFY_TOKEN`.
2. App settings → Basic: Deauthorize callback `https://<your-host>/deauthorize`; Privacy and Data deletion URLs from GitHub Pages.
3. `python -m app.tools subscribe` (from any machine with the `.env`).
4. Open `https://<your-host>/health` → `{"status":"ok", ...}`.

## Local development

```
scripts\start.bat          # runs on http://127.0.0.1:8080
ngrok http 8080            # gives a temporary public https URL for Meta
```

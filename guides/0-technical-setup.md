# 0 · Technical setup — everything needed, in order

Audience: the person who installs and connects the app. Editors only need guides 1–4.
Time: ~1 hour the first time, excluding Meta's review wait.

## A. What you need before starting

| Item | Where |
|---|---|
| Instagram **Professional** account (Business or Creator), set to **public** | Instagram app → Settings → Account type and tools |
| A Facebook account that will own the Meta developer app | facebook.com |
| A Meta developer account | https://developers.facebook.com (accept terms) |
| Python 3.11+ on the machine that will run the app (or Docker on the host) | https://python.org |
| Git + a GitHub account (legal pages + code hosting) | Already done: https://github.com/Giu1/insta-automations |
| A second Instagram account for testing comments and DMs | any personal account |

No Facebook Page and no WhatsApp number are required with the Instagram Login setup used here.

## B. Meta app (once)

1. **My Apps → Create app** → type **Business** → name it.
2. **Use cases → Add** → **Manage messaging & content on Instagram**. Do not add ads, Threads, Messenger, WhatsApp.
3. **Customize** → left menu **API setup with Instagram login**.
4. **Permissions and features** → make sure these four have **Add / Ready for testing**:
   - `instagram_business_basic`
   - `instagram_business_manage_comments`
   - `instagram_business_manage_messages`
   - `instagram_business_content_publish`
5. **App settings → Basic** → fill: display name, contact email, app icon 1024×1024, category, and
   - Privacy Policy URL: `https://giu1.github.io/insta-automations/privacy.html`
   - User data deletion URL: `https://giu1.github.io/insta-automations/data-deletion.html`
   - Terms of Service URL (optional): same privacy URL
6. **App roles → Roles → Instagram testers** → add the brand's Instagram account → accept the invite in the Instagram app (Settings → Apps and websites → Tester invites).

Values to copy from the dashboard:

| Value | Where | Goes to |
|---|---|---|
| **Instagram app secret** (32 hex chars, click *Show*) | Instagram → API setup with Instagram login | `.env` → `INSTAGRAM_APP_SECRET` |
| **Access token** per account | same page → *Generate access tokens* → Add account → Generate token | `.env` → `BRAND_<NAME>_TOKEN` |

## C. Files on the machine

```
git clone https://github.com/Giu1/insta-automations.git
cd insta-automations
pip install -r requirements.txt
copy .env.example .env
```

`.env` (never commit; the host's environment settings in production):

```
INSTAGRAM_APP_SECRET=<32-char Instagram app secret>
WEBHOOK_VERIFY_TOKEN=<any word you invent>
BRAND_MARKETERMILANO_TOKEN=<access token from Generate token>
```

Optional: `META_APP_SECRET` (App settings → Basic, accepted as a second signing secret), `DATABASE_URL` (Postgres URL instead of SQLite), `LOG_LEVEL`.

`config/brands.yaml` — one block per account. Leave the two ids empty the first time, then:

```
python -m app.tools whoami      # prints instagram_id and instagram_app_user_id -> paste into brands.yaml
python -m app.tools check       # must end with "All good."
```

`config/replies.yaml` and `config/posts.yaml` — see guides 1 and 2. Defaults are valid.

## D. Run it and expose it

Local (development):

```
scripts\start.bat               # http://127.0.0.1:8080
ngrok http 8080                 # public https URL, changes every restart
```

Production (24/7): see [5-hosting.md](5-hosting.md). Short version: Render → New → Blueprint → this repo → set the three env vars → deploy → note `https://<service>.onrender.com`.

Health check: `GET https://<host>/health` → `{"status":"ok","brands":{"marketermilano":{"token":true}}}`.

## E. Webhooks (connect Instagram to the app)

1. Meta → Instagram → API setup with Instagram login → **Configure webhooks**:
   - Callback URL: `https://<host>/webhooks/meta`
   - Verify token: exactly the `WEBHOOK_VERIFY_TOKEN` value
   - **Verify and save** (the app must be running and reachable).
2. Subscribe to fields **comments** and **messages**.
3. From the machine with `.env`: `python -m app.tools subscribe` → `{"success": true}` per brand. (The dashboard toggle "Webhook Subscription" is unreliable; the command is authoritative.)
4. Use the dashboard **Test → Send to my server** on *comments*: the app log shows a `POST /webhooks/meta 200`.

Meta callbacks in **App settings → Basic**:
- Deauthorize callback URL: `https://<host>/deauthorize`
- Data deletion request URL: the GitHub Pages URL above (Meta accepts a page with instructions).

## F. Go live

Meta only sends **real** comments and messages once the app is **Live** and the permissions have **Advanced Access**.

1. Top of the dashboard: switch **Development → Live**. Requires the Basic settings from step B.5.
2. **Complete app review** → request Advanced Access for the four permissions → follow [6-meta-app-review.md](6-meta-app-review.md) (screencast + wording). Business Verification may be requested.
3. While waiting, testers listed in App roles can already trigger real events.

## G. Verify end to end

| Test | Expected |
|---|---|
| Second account comments "preço?" on a post | public reply under the comment within ~5 s; log: `comment <id> -> rule 'price' (pt-PT)` |
| Second account sends a DM first | reply in Direct; log: `message <id> -> rule ...` |
| Same DM again within 24 h with no keyword | no second welcome |
| `python -m app.tools posts` | lists the calendar; a post with a past `publish_at` publishes within 1 min |
| `python -m app.tools publish-now <id>` | real post appears on the profile |

## H. Maintenance

- **Tokens**: refreshed automatically every day (60-day tokens never lapse while the app runs). If the account changes password or Meta revokes access: *Generate token* again → replace in env → restart → `tools check`.
- **Config edits**: no restart needed; run `tools check` after each change.
- **Adding an account**: [3-brands-and-check.md](3-brands-and-check.md).
- **Updating code**: `git pull` + restart (Render redeploys automatically on push).
- **Logs**: terminal locally; the host's Logs tab in production. Meaningful lines start with `[brandname]`.
- **Rotate secrets** if a token or secret was ever pasted somewhere public: Meta → *Reset* app secret; regenerate tokens; update env.

## I. Endpoints and data (for auditors)

| Endpoint | Purpose |
|---|---|
| `GET /webhooks/meta` | Meta verification handshake |
| `POST /webhooks/meta` | Comment/message events, HMAC-SHA256 verified with the Instagram app secret |
| `GET /health` | Liveness + token presence |
| `GET /privacy`, `GET /data-deletion` | Legal pages (also on GitHub Pages) |
| `POST /deauthorize` | Meta deauthorize callback (acknowledges) |

Outbound calls (all to `graph.instagram.com`): `me`, `refresh_access_token`, `me/subscribed_apps`, `{comment}/replies`, `me/messages`, `me/media`, `{container}?fields=status_code`, `me/media_publish`.

Stored data (SQLite `data/app.db` or Postgres): seen comment/message ids, `(brand, sender, time)` for the 24h welcome throttle, published post ids and results, refreshed tokens. No message bodies, no follower data.

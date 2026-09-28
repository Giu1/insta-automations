# 3 · Brands (Instagram accounts) and the check tool

File: **`config/brands.yaml`** — one block per Instagram account.

```yaml
brands:
  marketermilano:                    # short name, letters only, used in the other files
    name: Marketer Milano
    instagram_id: "17841431544171129"
    instagram_app_user_id: "38522968214016994"
    token_env: BRAND_MARKETERMILANO_TOKEN
    default_language: pt-PT          # en | pt-PT | pt-BR | es
    timezone: Europe/Lisbon
```

## Adding a second account

1. In the Meta App Dashboard → Instagram → *API setup with Instagram login* → **Add account**, log in with the new Professional account, click **Generate token**.
2. In `.env` add a line `BRAND_NEWNAME_TOKEN=<the token>`.
3. In `brands.yaml` copy the block, rename it (`newname:`), set `token_env: BRAND_NEWNAME_TOKEN`, leave the two ids empty for a moment.
4. Run `python -m app.tools whoami` → it prints both ids; paste them into the block.
5. Run `python -m app.tools subscribe` so Instagram starts sending that account's comments and messages.
6. Add a `newname:` section in `replies.yaml`.

## The check tool

```
python -m app.tools check
```

(or double-click `scripts\check.bat`). It validates the three config files and confirms each token still works with Instagram. Run it after every edit.

Other commands:

| Command | Purpose |
|---|---|
| `python -m app.tools try "some text"` | Which reply would be sent for that text, and in which language |
| `python -m app.tools posts` | Scheduled / published / failed posts |
| `python -m app.tools whoami` | Account behind each token |
| `python -m app.tools subscribe` | Re-enable webhooks for all brands |

## Tokens

Tokens last 60 days; the app refreshes them automatically every day, so you normally never touch them again. If Instagram ever says a token is invalid (password change, security review), generate a new one in the Meta dashboard and replace the line in `.env`, then restart the app.

# 6 · Meta App Review checklist

Meta reviews the whole app. Keep the request minimal and consistent with what the code does.

## Permissions to request (Instagram API with Instagram Login)

| Permission | Why (use this wording) |
|---|---|
| `instagram_business_basic` | Identify the connected Instagram professional account |
| `instagram_business_manage_comments` | Reply publicly to comments that contain specific keywords (e.g. price, opening hours) |
| `instagram_business_manage_messages` | Reply to people who send a Direct message to the business first, within the 24-hour window |
| `instagram_business_content_publish` | Publish scheduled posts, reels and stories the business prepared |

Do not request anything else.

## Before submitting

- App is **Live**, has an icon (1024×1024), category, contact email.
- Privacy Policy URL: https://giu1.github.io/insta-automations/privacy.html
- Data deletion URL: https://giu1.github.io/insta-automations/data-deletion.html
- Deauthorize callback: `https://<your-host>/deauthorize`
- Webhook configured and at least one successful API call made with each permission (run `tools check`, `tools try`, publish a test post, reply to a test comment and a test DM).
- Business verification completed if Meta asks for it.

## Screencast (2–4 minutes, no cuts)

1. Show the Meta login / Add account flow granting the permissions.
2. From a second Instagram account, comment "preço?" on a post → show the automatic public reply appearing.
3. From the second account, send a Direct message first → show the automatic reply.
4. Show `config/posts.yaml` with a scheduled post, then the post appearing on the profile (or `tools publish-now`).
5. Show `config/replies.yaml` briefly to demonstrate the business controls the texts.

## Wording for "How will you use this permission"

> The app is an internal tool for the business's own Instagram professional account. It replies to comments containing pre-defined keywords, answers Direct messages only after the user contacts the business, and publishes content the business scheduled. It never sends unsolicited messages, does not follow/like/scrape, and stores only IDs needed to avoid duplicate replies.

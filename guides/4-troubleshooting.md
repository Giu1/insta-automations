# 4 · Troubleshooting

Start with `python -m app.tools check`. Then look at the app log (the terminal, or your host's log page).

| You see | Meaning | Fix |
|---|---|---|
| `!! replies.yaml is not valid YAML` | A typo (indentation, missing quote) | Compare with a working block; put text with `:` or `#` in quotes |
| `!! rule 'x' has unknown language(s)` | Language key misspelled | Use exactly `en`, `pt-PT`, `pt-BR`, `es` |
| `!! [brand] token rejected by Instagram` | Token expired or revoked | Generate a new token in the Meta dashboard → `.env` → restart |
| `webhook rejected: bad signature` in the log | `INSTAGRAM_APP_SECRET` wrong | Copy the *Instagram app secret* (32 characters, click **Show**), not the access token |
| Comment posted but no reply, log says `no rule matched` | No keyword found | Add the word to `keywords`, test with `tools try` |
| No line at all appears in the log after a comment | Instagram is not sending events | App must be **Live** in Meta; run `tools subscribe`; the Instagram account must be **public**; the commenter must not be the brand itself |
| Reply went out in the wrong language | Short text, hard to detect | Add the missing translation; set `default_language` to your main audience |
| `FAILED: ... media` in `tools posts` | Instagram could not download the file | Use a direct public https link to a JPG/PNG/MP4 |
| `Verify token does not match` while saving the webhook in Meta | Different word in `.env` vs Meta | Make `WEBHOOK_VERIFY_TOKEN` identical to the box in Meta |

## Safe restart (local Windows)

Close the black window running the app and double-click `scripts\start.bat` again. Nothing is lost: handled comments, sent welcomes and published posts are stored in `data/app.db`.

## Things the app will never do

- Message people who did not message first
- Follow / unfollow / like automatically
- Reply to the same comment twice
- Publish the same post id twice

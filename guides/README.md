# Guides (no coding needed)

Everything you change day to day lives in the `config/` folder. You edit three text files and the app picks up the changes automatically (no restart needed):

| File | What it controls | Guide |
|---|---|---|
| `config/replies.yaml` | Automatic replies to comments and Direct messages, in 4 languages | [1-replies.md](1-replies.md) |
| `config/posts.yaml` | Which posts go out and when (content calendar) | [2-posts.md](2-posts.md) |
| `config/brands.yaml` | Which Instagram accounts are managed | [3-brands-and-check.md](3-brands-and-check.md) |

Also:

- [0-technical-setup.md](0-technical-setup.md) — complete install and Meta configuration checklist (technical person)
- [4-troubleshooting.md](4-troubleshooting.md) — what to do when something does not work
- [5-hosting.md](5-hosting.md) — running it 24/7 for free (for the person who sets it up)
- [6-meta-app-review.md](6-meta-app-review.md) — checklist for Meta's App Review

## Three rules to keep in mind

1. **Indentation matters.** Copy an existing block and change the text; keep the spaces at the start of each line as they are.
2. **Quotes.** If your text contains `:` or `#`, wrap it in double quotes `"like this"`.
3. **After editing, run the check** (double-click `scripts\check.bat` on Windows, or `python -m app.tools check`). It tells you in plain words if something is wrong.

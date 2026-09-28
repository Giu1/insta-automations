# 1 · Editing automatic replies

File: **`config/replies.yaml`**

## What the app does

- **Comments** on your posts/reels → if the comment contains one of your keywords, the app answers **publicly under that comment**.
- **Direct messages** → if someone **writes to you first**, the app replies in Direct. It never messages people who did not write first (Instagram does not allow it).
- Replies are sent in the **language the person used**: English (`en`), Portuguese from Portugal (`pt-PT`), Portuguese from Brazil (`pt-BR`) or Spanish (`es`, neutral Latin-American Spanish).
- Your own comments/messages are ignored.

## Anatomy of a rule

```yaml
      - name: price                                   # a short label, only for you
        keywords: [price, preço, quanto custa, precio] # any of these words triggers the rule
        reply:
          en: "Prices are in the link in our bio."
          pt-PT: "Os preços estão no link da bio."
          pt-BR: "Os preços estão no link da bio."
          es: "Los precios están en el link de la bio."
```

- Keywords ignore capital letters and accents. `preço`, `Preco`, `PREÇO` all match.
- Keywords match whole words: `open` matches "are you open?" but not "opening" — add both if you want both.
- Multi-word keywords are fine: `how much`, `quanto custa`.
- Rules are read **top to bottom, the first match wins**. Put specific rules first.
- You may skip a language. If it is missing, the app uses the brand's `default_language`, then English.

## The welcome / fallback rule (messages only)

```yaml
      - name: welcome
        keywords: ["*"]
        reply:
          en: "Thanks for your message! We'll reply shortly."
```

`"*"` means "any message". Keep it as the **last** rule under `messages`. With `welcome_once_per_day: true` a person receives it at most once every 24 hours, so there are no loops.

Do **not** use `"*"` under `comments` — you would reply to every single comment.

## Adding a new rule

1. Copy an existing rule block (from `- name:` to the last language line).
2. Paste it **above** the `welcome` rule (or at the end of `comments`).
3. Change `name`, `keywords` and the four texts.
4. Run the check: `scripts\check.bat` (Windows) or `python -m app.tools check`.
5. Preview: `python -m app.tools try "quanto custa?"` shows exactly which reply would go out and in which language.

## Removing a rule

Delete the whole block, from its `- name:` line down to its last language line. Run the check.

## Tips for good replies

- Keep it short; comments are public.
- Do not promise things a human will not follow up on.
- Never ask for passwords, card numbers or personal data in automatic replies.

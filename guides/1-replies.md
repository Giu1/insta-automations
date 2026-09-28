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

## How the language is chosen

`replies.yaml` does not filter by language; it only stores the translations. The app decides in two steps:

1. **Keywords are language-independent.** A rule fires if *any* of its keywords appears in the text. That is why each `keywords` list mixes English, Portuguese and Spanish words (`price, preço, precio`). You never write separate keywords per language.
2. **The language is detected from the whole message**, then the matching `reply:` key is used:
   - English words (*how much, please, do you…*) → `en`
   - Spanish words (*hola, cuánto, gracias, tienen…*) → `es`
   - Portuguese words (*olá, quanto, obrigado, não…*) → Portuguese, then: *tu / estou a / autocarro* → `pt-PT`; *você / vc / pra / a gente* → `pt-BR`
   - Nothing recognisable, or a tie → the brand's `default_language` from `brands.yaml`
   - If the chosen language has no text in the rule → the other Portuguese variant, then the default language, then `en`.

Example: "Hola, cuánto cuesta?" → keyword `cuánto` fires the `price` rule → words *hola, cuanto* mean `es` → the `es:` text is sent.

Preview any sentence with `python -m app.tools try "Oi, quanto custa pra gente?"` — it shows the rule, the language and the exact text.

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

## Links in replies

Replies are plain text, so a link is just typed into the text. Instagram makes it clickable in Direct messages:

```yaml
      - name: booking
        keywords: [book, booking, agendar, marcar, reservar, cita, agenda]
        reply:
          en: "You can book here: https://your-site.com/book"
          pt-PT: "Podes marcar aqui: https://your-site.com/book"
          pt-BR: "Você pode agendar aqui: https://your-site.com/book"
          es: "Puedes reservar aquí: https://your-site.com/book"
```

- **Keep the double quotes** around text with a link; the `:` in `https:` breaks the file otherwise.
- **Messages**: links are fine and clickable.
- **Comments**: links show as plain text (not clickable) and Instagram may hide repeated link comments as spam. Prefer "link in bio" in comment replies and put the real link in the message reply.
- No formatting (bold, markdown) exists in Instagram replies; write the URL as-is. Short links look cleaner.

## Tips for good replies

- Keep it short; comments are public.
- Do not promise things a human will not follow up on.
- Never ask for passwords, card numbers or personal data in automatic replies.

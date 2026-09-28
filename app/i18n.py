"""Very small language detector: English, Portuguese (Portugal / Brazil), Spanish.

No external services. It counts common words; when unsure it uses the brand's default language.
"""

from __future__ import annotations

import re
import unicodedata

LANG_EN, LANG_PT_PT, LANG_PT_BR, LANG_ES = "en", "pt-PT", "pt-BR", "es"


def normalize(text: str) -> str:
    """lowercase, remove accents, collapse spaces -> 'Preço?' becomes 'preco?'"""
    text = unicodedata.normalize("NFKD", (text or "").lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip()


def _count(text: str, words: tuple[str, ...]) -> int:
    return sum(1 for w in words if re.search(rf"(?<!\w){re.escape(w)}(?!\w)", text))


_EN = ("hello", "hi", "hey", "thanks", "thank you", "please", "how much", "price", "hours", "open",
       "where", "when", "what", "do you", "are you", "i want", "can i", "is it", "the", "and")
_ES = ("hola", "gracias", "por favor", "cuanto", "precio", "horario", "donde", "cuando", "que tal",
       "buenas", "buenos dias", "quiero", "tienen", "tienes", "abren", "abierto", "hacen", "envios",
       "ustedes", "usted", "los", "las", "con", "para", "esta", "estan", "hay")
_PT = ("ola", "oi", "obrigado", "obrigada", "por favor", "quanto", "preco", "horario", "onde", "quando",
       "bom dia", "boa tarde", "boa noite", "quero", "tem", "voces", "voce", "nao", "sim", "abrem",
       "aberto", "fazem", "envio", "entrega", "com", "os", "da", "dos", "das", "um", "uma", "muito")

_PT_BR = ("voce", "vc", "vcs", "a gente", "legal", "cade", "ta", "pra", "pro", "valeu", "beleza",
          "celular", "onibus", "tchau", "oi", "bora", "gente", "obrigado por", "seu", "sua")
_PT_PT = ("tu", "estas", "es", "autocarro", "telemovel", "fixe", "pequeno-almoco", "casa de banho",
          "se faz favor", "sff", "bue", "esta a", "estou a", "estao a", "pois", "vos", "consigo", "vossa")


def detect_language(text: str, default: str = LANG_EN) -> str:
    t = normalize(text)
    scores = {LANG_EN: _count(t, _EN), LANG_ES: _count(t, _ES), "pt": _count(t, _PT)}
    best = max(scores.values())
    if best == 0:
        return default
    winners = [lang for lang, s in scores.items() if s == best]
    if len(winners) > 1:
        # tie: prefer the brand default's family
        family = "pt" if default.startswith("pt") else default
        lang = family if family in winners else winners[0]
    else:
        lang = winners[0]
    if lang != "pt":
        return lang
    br, pt = _count(t, _PT_BR), _count(t, _PT_PT)
    if br > pt:
        return LANG_PT_BR
    if pt > br:
        return LANG_PT_PT
    return default if default in (LANG_PT_PT, LANG_PT_BR) else LANG_PT_PT


def pick_text(replies: dict[str, str], language: str, default: str) -> str | None:
    """Choose the best available translation for a reply."""
    sibling = {LANG_PT_PT: LANG_PT_BR, LANG_PT_BR: LANG_PT_PT}.get(language)
    for key in (language, sibling, default, LANG_EN):
        if key and replies.get(key):
            return replies[key]
    return next(iter(replies.values()), None)

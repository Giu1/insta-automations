"""Decide which reply (if any) to send for a comment or message."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.config import Brand, Rule, load_replies
from app.i18n import detect_language, normalize, pick_text


@dataclass(frozen=True)
class Decision:
    rule: str
    language: str
    text: str
    is_catch_all: bool


def _matches(text_norm: str, rule: Rule) -> bool:
    if rule.is_catch_all:
        return True
    for kw in rule.keywords:
        pattern = rf"(?<!\w){re.escape(normalize(kw))}(?!\w)"
        if re.search(pattern, text_norm):
            return True
    return False


def decide(brand: Brand, text: str, rules: tuple[Rule, ...]) -> Decision | None:
    """First matching rule wins. Returns None when nothing matches."""
    text_norm = normalize(text)
    if not text_norm:
        return None
    language = detect_language(text, brand.default_language)
    for rule in rules:
        if _matches(text_norm, rule):
            reply = pick_text(rule.replies, language, brand.default_language)
            if reply:
                return Decision(rule=rule.name, language=language, text=reply, is_catch_all=rule.is_catch_all)
    return None


def decide_comment(brand: Brand, text: str) -> Decision | None:
    return decide(brand, text, load_replies(brand.slug).comments)


def decide_message(brand: Brand, text: str) -> Decision | None:
    return decide(brand, text, load_replies(brand.slug).messages)

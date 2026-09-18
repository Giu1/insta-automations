from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from app.settings import get_settings


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def rule_matches(text: str, needles: list[str]) -> bool:
    if any(n == "*" for n in needles):
        return True
    haystack = _normalize(text)
    return any(_normalize(n) in haystack for n in needles)


def load_rules() -> dict[str, Any]:
    path: Path = get_settings().rules_path
    if not path.exists():
        return {"brands": {}}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {"brands": {}}


def brand_rules(slug: str) -> dict[str, Any]:
    return (load_rules().get("brands") or {}).get(slug) or {}


def first_reply(text: str, rules: list[dict[str, Any]]) -> tuple[str | None, bool]:
    """Return (reply, is_wildcard)."""
    for rule in rules:
        needles = [str(x) for x in rule.get("match") or []]
        if not needles:
            continue
        if rule_matches(text, needles):
            return str(rule["reply"]), any(n == "*" for n in needles)
    return None, False


def utcnow() -> datetime:
    return datetime.now(timezone.utc)

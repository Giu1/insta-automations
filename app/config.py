"""Loads and validates the three editable files in config/.

- brands.yaml   -> which Instagram accounts we manage
- replies.yaml  -> keyword rules and multilingual replies
- posts.yaml    -> content calendar (scheduled posts)

Files are re-read when they change, so edits do not require a restart.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml

from app.settings import get_settings

LANGUAGES = ("en", "pt-PT", "pt-BR", "es")
POST_TYPES = ("image", "reel", "story")


class ConfigError(ValueError):
    """Raised with a plain-language message when a config file is wrong."""


# ---------- YAML loading with change detection ----------

_cache: dict[Path, tuple[float, Any]] = {}


def load_yaml(path: Path) -> dict:
    if not path.exists():
        raise ConfigError(f"Missing file: {path.name} (expected in the config folder)")
    mtime = path.stat().st_mtime
    cached = _cache.get(path)
    if cached and cached[0] == mtime:
        return cached[1]
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path.name} is not valid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"{path.name} must start with a key (for example 'brands:')")
    _cache[path] = (mtime, data)
    return data


def _path(name: str) -> Path:
    return get_settings().config_dir / name


# ---------- Brands ----------


@dataclass(frozen=True)
class Brand:
    slug: str
    name: str
    instagram_ids: frozenset[str]  # all ids that identify this account in webhooks
    token_env: str
    default_language: str
    timezone: str

    @property
    def env_token(self) -> str:
        return os.getenv(self.token_env, "").strip()

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)


def load_brands() -> dict[str, Brand]:
    raw = load_yaml(_path("brands.yaml")).get("brands") or {}
    if not raw:
        raise ConfigError("brands.yaml has no brands. Add at least one under 'brands:'.")
    brands: dict[str, Brand] = {}
    for slug, item in raw.items():
        item = item or {}
        ids = {str(item.get(k)) for k in ("instagram_id", "instagram_app_user_id") if item.get(k)}
        if not ids:
            raise ConfigError(f"Brand '{slug}': add 'instagram_id' (run: python -m app.tools whoami)")
        lang = str(item.get("default_language") or "en")
        if lang not in LANGUAGES:
            raise ConfigError(f"Brand '{slug}': default_language must be one of {', '.join(LANGUAGES)}")
        tz = str(item.get("timezone") or "Europe/Lisbon")
        try:
            ZoneInfo(tz)
        except Exception as exc:  # noqa: BLE001
            raise ConfigError(f"Brand '{slug}': unknown timezone '{tz}'") from exc
        brands[str(slug)] = Brand(
            slug=str(slug),
            name=str(item.get("name") or slug),
            instagram_ids=frozenset(ids),
            token_env=str(item.get("token_env") or f"BRAND_{str(slug).upper()}_TOKEN"),
            default_language=lang,
            timezone=tz,
        )
    return brands


def brand_for_id(instagram_id: str) -> Brand | None:
    needle = str(instagram_id)
    for brand in load_brands().values():
        if needle in brand.instagram_ids:
            return brand
    return None


# ---------- Replies ----------


@dataclass(frozen=True)
class Rule:
    name: str
    keywords: tuple[str, ...]
    replies: dict[str, str]  # language -> text

    @property
    def is_catch_all(self) -> bool:
        return "*" in self.keywords


@dataclass(frozen=True)
class BrandReplies:
    comments: tuple[Rule, ...] = ()
    messages: tuple[Rule, ...] = ()
    welcome_once_per_day: bool = True


def _parse_rules(items: Any, where: str) -> tuple[Rule, ...]:
    rules: list[Rule] = []
    for i, item in enumerate(items or [], start=1):
        if not isinstance(item, dict):
            raise ConfigError(f"{where}: rule #{i} must have 'keywords' and 'reply'")
        name = str(item.get("name") or f"rule-{i}")
        keywords = tuple(str(k).strip() for k in (item.get("keywords") or []) if str(k).strip())
        if not keywords:
            raise ConfigError(f"{where}: rule '{name}' needs at least one keyword (or \"*\")")
        reply = item.get("reply")
        if isinstance(reply, str):
            replies = {"en": reply}
        elif isinstance(reply, dict) and reply:
            replies = {str(k): str(v) for k, v in reply.items() if str(v).strip()}
            bad = [k for k in replies if k not in LANGUAGES]
            if bad:
                raise ConfigError(f"{where}: rule '{name}' has unknown language(s) {bad}. Use {', '.join(LANGUAGES)}")
        else:
            raise ConfigError(f"{where}: rule '{name}' needs a 'reply' (text per language)")
        rules.append(Rule(name=name, keywords=keywords, replies=replies))
    return tuple(rules)


def load_replies(brand_slug: str) -> BrandReplies:
    raw = (load_yaml(_path("replies.yaml")).get("brands") or {}).get(brand_slug) or {}
    return BrandReplies(
        comments=_parse_rules(raw.get("comments"), f"replies.yaml > {brand_slug} > comments"),
        messages=_parse_rules(raw.get("messages"), f"replies.yaml > {brand_slug} > messages"),
        welcome_once_per_day=bool(raw.get("welcome_once_per_day", True)),
    )


# ---------- Posts (content calendar) ----------


@dataclass(frozen=True)
class Post:
    id: str
    brand: str
    publish_at: datetime  # timezone-aware UTC
    type: str  # image | reel | story
    media_url: str
    caption: str = ""
    extra: dict = field(default_factory=dict)


def load_posts() -> list[Post]:
    raw = load_yaml(_path("posts.yaml")).get("posts") or []
    brands = load_brands()
    posts: list[Post] = []
    seen: set[str] = set()
    for i, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise ConfigError(f"posts.yaml: post #{i} is not a list of fields")
        pid = str(item.get("id") or "").strip()
        if not pid:
            raise ConfigError(f"posts.yaml: post #{i} needs a unique 'id' (for example 2026-10-01-launch)")
        if pid in seen:
            raise ConfigError(f"posts.yaml: id '{pid}' is used twice. Each post needs its own id")
        seen.add(pid)
        brand = brands.get(str(item.get("brand") or ""))
        if not brand:
            raise ConfigError(f"posts.yaml: post '{pid}' has unknown brand '{item.get('brand')}'")
        ptype = str(item.get("type") or "image").lower()
        if ptype not in POST_TYPES:
            raise ConfigError(f"posts.yaml: post '{pid}' type must be one of {', '.join(POST_TYPES)}")
        media_url = str(item.get("media_url") or "").strip()
        if not media_url.startswith("https://"):
            raise ConfigError(f"posts.yaml: post '{pid}' media_url must be a public https:// link")
        when = item.get("publish_at")
        if isinstance(when, datetime):
            dt = when
        else:
            try:
                dt = datetime.fromisoformat(str(when).strip().replace(" ", "T"))
            except ValueError as exc:
                raise ConfigError(
                    f"posts.yaml: post '{pid}' publish_at must look like 2026-10-01 09:00"
                ) from exc
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=brand.tz)
        posts.append(
            Post(
                id=pid,
                brand=brand.slug,
                publish_at=dt.astimezone(timezone.utc),
                type=ptype,
                media_url=media_url,
                caption=str(item.get("caption") or "").strip(),
            )
        )
    return sorted(posts, key=lambda p: p.publish_at)

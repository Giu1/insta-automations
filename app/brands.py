from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from app.settings import get_settings


class Brand:
    def __init__(self, slug: str, data: dict[str, Any]) -> None:
        self.slug = slug
        self.name: str = data["name"]
        self.ig_user_id: str = str(data["ig_user_id"])
        self.instagram_app_user_id: str = str(data.get("instagram_app_user_id") or "")
        self.facebook_page_id: str = str(data.get("facebook_page_id") or "")
        self.token_env: str = data["token_env"]

    def ids(self) -> set[str]:
        return {i for i in (self.ig_user_id, self.instagram_app_user_id, self.facebook_page_id) if i and i != "0"}

    @property
    def page_token(self) -> str:
        token = os.getenv(self.token_env, "")
        if not token:
            raise RuntimeError(f"Missing Page token env var {self.token_env} for brand {self.slug}")
        return token


def load_brands() -> dict[str, Brand]:
    path: Path = get_settings().brands_path
    if not path.exists():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {slug: Brand(slug, item) for slug, item in (raw.get("brands") or {}).items()}


def brand_by_ig_id(ig_user_id: str) -> Brand | None:
    needle = str(ig_user_id)
    for brand in load_brands().values():
        if needle in brand.ids():
            return brand
    return None


def brand_by_page_id(page_id: str) -> Brand | None:
    for brand in load_brands().values():
        if brand.facebook_page_id == str(page_id):
            return brand
    return None

"""Access tokens: read from .env, keep them alive with Instagram's refresh endpoint."""

from __future__ import annotations

import logging

from app.config import Brand, load_brands
from app.db import SessionLocal, StoredToken, now
from app.instagram import Instagram, InstagramError

log = logging.getLogger("tokens")


def token_for(brand: Brand) -> str:
    """Most recent token: a refreshed one saved in the database, else the .env value."""
    with SessionLocal() as session:
        stored = session.get(StoredToken, brand.slug)
        if stored and stored.token:
            return stored.token
    return brand.env_token


def client_for(brand: Brand) -> Instagram:
    return Instagram(token_for(brand))


def refresh_all() -> None:
    """Daily job. Instagram long-lived tokens last 60 days; refreshing keeps them alive forever."""
    for brand in load_brands().values():
        try:
            result = client_for(brand).refresh_token()
        except InstagramError as exc:
            # "at least 24 hours old" errors are normal on the first day; anything else is worth seeing.
            log.warning("[%s] token refresh skipped: %s", brand.slug, exc)
            continue
        new_token = result.get("access_token")
        if new_token:
            with SessionLocal() as session:
                session.merge(StoredToken(brand=brand.slug, token=new_token, refreshed_at=now()))
                session.commit()
            log.info("[%s] token refreshed (valid ~%s days)", brand.slug, int(result.get("expires_in", 0)) // 86400)

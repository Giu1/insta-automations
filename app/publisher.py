"""Publishes posts from config/posts.yaml when their time comes."""

from __future__ import annotations

import logging

from app.config import ConfigError, Post, load_brands, load_posts
from app.db import PublishedPost, SessionLocal, now, record_post
from app.instagram import InstagramError
from app.tokens import client_for

log = logging.getLogger("publisher")


def publish_post(post: Post) -> tuple[str, str | None, str | None]:
    """Returns (status, media_id, error)."""
    brand = load_brands()[post.brand]
    try:
        media_id = client_for(brand).publish(post_type=post.type, media_url=post.media_url, caption=post.caption)
        log.info("[%s] published '%s' -> media %s", brand.slug, post.id, media_id)
        return "published", media_id, None
    except InstagramError as exc:
        log.error("[%s] publishing '%s' failed: %s", brand.slug, post.id, exc)
        return "failed", None, str(exc)


def publish_due() -> None:
    """Runs every minute. Each post id is attempted once; results are stored so nothing posts twice."""
    try:
        posts = load_posts()
    except ConfigError as exc:
        log.error("posts.yaml problem, nothing published: %s", exc)
        return
    current = now()
    with SessionLocal() as session:
        for post in posts:
            if post.publish_at > current or session.get(PublishedPost, post.id):
                continue
            status, media_id, error = publish_post(post)
            record_post(session, post.id, post.brand, status, media_id, error)

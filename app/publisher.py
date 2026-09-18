from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.brands import load_brands
from app.db import ScheduledPost
from app.graph import GraphError, create_media_container, publish_container, wait_container_ready


def publish_due_posts(session: Session) -> None:
    now = datetime.now(timezone.utc)
    due = (
        session.query(ScheduledPost)
        .filter(ScheduledPost.status == "queued", ScheduledPost.publish_at <= now)
        .order_by(ScheduledPost.publish_at.asc())
        .limit(10)
        .all()
    )
    brands = load_brands()
    for post in due:
        brand = brands.get(post.brand_slug)
        if not brand:
            post.status = "failed"
            post.last_error = f"unknown brand {post.brand_slug}"
            session.commit()
            continue
        post.status = "publishing"
        session.commit()
        try:
            container_id = create_media_container(
                brand.ig_user_id,
                brand.page_token,
                caption=post.caption,
                image_url=post.image_url,
                video_url=post.video_url,
                media_type=post.media_type,
            )
            post.graph_container_id = container_id
            session.commit()
            wait_container_ready(container_id, brand.page_token)
            media_id = publish_container(brand.ig_user_id, container_id, brand.page_token)
            post.graph_media_id = media_id
            post.status = "published"
            post.published_at = datetime.now(timezone.utc)
            post.last_error = None
        except (GraphError, RuntimeError) as exc:
            post.status = "failed"
            post.last_error = str(exc)
        session.commit()

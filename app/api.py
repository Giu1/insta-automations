from datetime import datetime
import os

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from app.brands import load_brands
from app.db import ScheduledPost, SessionLocal
from app.rules import utcnow
from app.settings import get_settings

router = APIRouter(prefix="/api")


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if not x_api_key or x_api_key != get_settings().api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


class ScheduleIn(BaseModel):
    brand: str
    caption: str = ""
    image_url: str | None = None
    video_url: str | None = None
    media_type: str = Field(default="IMAGE")
    publish_at: datetime


@router.get("/brands")
def list_brands(_: None = Depends(require_api_key)) -> dict:
    return {
        "brands": [
            {
                "slug": b.slug,
                "name": b.name,
                "ig_user_id": b.ig_user_id,
                "facebook_page_id": b.facebook_page_id,
                "token_configured": bool(os.getenv(b.token_env)),
            }
            for b in load_brands().values()
        ]
    }


@router.post("/posts")
def schedule_post(body: ScheduleIn, _: None = Depends(require_api_key)) -> dict:
    if body.brand not in load_brands():
        raise HTTPException(status_code=400, detail="Unknown brand")
    if body.media_type.upper() == "IMAGE" and not body.image_url:
        raise HTTPException(status_code=400, detail="image_url required")
    if body.media_type.upper() in {"REELS", "STORIES", "VIDEO"} and not body.video_url:
        raise HTTPException(status_code=400, detail="video_url required")
    session = SessionLocal()
    try:
        post = ScheduledPost(
            brand_slug=body.brand,
            caption=body.caption,
            image_url=body.image_url,
            video_url=body.video_url,
            media_type=body.media_type.upper(),
            publish_at=body.publish_at,
            status="queued",
            created_at=utcnow(),
        )
        session.add(post)
        session.commit()
        session.refresh(post)
        return {"id": post.id, "status": post.status}
    finally:
        session.close()


@router.get("/posts")
def list_posts(_: None = Depends(require_api_key)) -> dict:
    session = SessionLocal()
    try:
        rows = session.query(ScheduledPost).order_by(ScheduledPost.publish_at.desc()).limit(100).all()
        return {
            "posts": [
                {
                    "id": p.id,
                    "brand": p.brand_slug,
                    "caption": p.caption,
                    "media_type": p.media_type,
                    "publish_at": p.publish_at.isoformat(),
                    "status": p.status,
                    "graph_media_id": p.graph_media_id,
                    "last_error": p.last_error,
                }
                for p in rows
            ]
        }
    finally:
        session.close()

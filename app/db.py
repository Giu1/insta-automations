from datetime import datetime, timedelta, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.settings import get_settings


class Base(DeclarativeBase):
    pass


class ScheduledPost(Base):
    __tablename__ = "scheduled_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brand_slug: Mapped[str] = mapped_column(String(64), index=True)
    caption: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_type: Mapped[str] = mapped_column(String(32), default="IMAGE")  # IMAGE, REELS, STORIES, VIDEO
    publish_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(32), default="queued")  # queued, publishing, published, failed
    graph_container_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    graph_media_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ProcessedEvent(Base):
    __tablename__ = "processed_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_key: Mapped[str] = mapped_column(String(191), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DmDefaultSent(Base):
    __tablename__ = "dm_default_sent"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brand_slug: Mapped[str] = mapped_column(String(64), index=True)
    sender_id: Mapped[str] = mapped_column(String(64), index=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def is_default_sent_recent(session, brand_slug: str, sender_id: str, hours: int = 24) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    row = (
        session.query(DmDefaultSent)
        .filter(
            DmDefaultSent.brand_slug == brand_slug,
            DmDefaultSent.sender_id == sender_id,
            DmDefaultSent.sent_at >= cutoff,
        )
        .first()
    )
    return row is not None


engine = create_engine(
    get_settings().database_url,
    connect_args={"check_same_thread": False} if get_settings().database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    from pathlib import Path

    if get_settings().database_url.startswith("sqlite"):
        Path("data").mkdir(exist_ok=True)
    Base.metadata.create_all(engine)

"""SQLite storage: what we already handled, welcome messages sent, published posts, refreshed tokens."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import DateTime, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.settings import get_settings


def now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class SeenEvent(Base):
    __tablename__ = "seen_events"
    key: Mapped[str] = mapped_column(String(191), primary_key=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class WelcomeSent(Base):
    __tablename__ = "welcome_sent"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brand: Mapped[str] = mapped_column(String(64), index=True)
    sender: Mapped[str] = mapped_column(String(64), index=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PublishedPost(Base):
    __tablename__ = "published_posts"
    post_id: Mapped[str] = mapped_column(String(191), primary_key=True)
    brand: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16))  # published | failed
    media_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class StoredToken(Base):
    __tablename__ = "tokens"
    brand: Mapped[str] = mapped_column(String(64), primary_key=True)
    token: Mapped[str] = mapped_column(Text)
    refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


_url = get_settings().database_url
engine = create_engine(_url, connect_args={"check_same_thread": False} if _url.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    if _url.startswith("sqlite"):
        Path("data").mkdir(exist_ok=True)
    Base.metadata.create_all(engine)


# ----- helpers -----


def mark_seen(session: Session, key: str) -> bool:
    """Returns True the first time a key is seen, False if already handled."""
    if session.get(SeenEvent, key):
        return False
    session.add(SeenEvent(key=key, at=now()))
    session.commit()
    return True


def welcome_sent_recently(session: Session, brand: str, sender: str, hours: int = 24) -> bool:
    cutoff = now() - timedelta(hours=hours)
    stmt = select(WelcomeSent).where(
        WelcomeSent.brand == brand, WelcomeSent.sender == sender, WelcomeSent.at >= cutoff
    )
    return session.execute(stmt).first() is not None


def record_welcome(session: Session, brand: str, sender: str) -> None:
    session.add(WelcomeSent(brand=brand, sender=sender, at=now()))
    session.commit()


def record_post(session: Session, post_id: str, brand: str, status: str, media_id: str | None, error: str | None) -> None:
    session.merge(PublishedPost(post_id=post_id, brand=brand, status=status, media_id=media_id, error=error, at=now()))
    session.commit()

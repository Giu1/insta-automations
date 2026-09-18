from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.brands import brand_by_ig_id, brand_by_page_id
from app.db import DmDefaultSent, ProcessedEvent, SessionLocal, is_default_sent_recent
from app.graph import GraphError, reply_to_comment, send_dm
from app.rules import brand_rules, first_reply, utcnow
from app.settings import get_settings

from pathlib import Path

LOG_PATH = Path(__file__).resolve().parents[1] / "data" / "webhooks.log"


def _log(msg: str) -> None:
    print(msg, flush=True)
    LOG_PATH.parent.mkdir(exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(msg + "\n")


def _verify_signature(
    raw: bytes,
    header256: str | None,
    header1: str | None = None,
) -> None:
    settings = get_settings()
    if settings.webhook_skip_signature:
        _log("[webhook] signature check skipped (WEBHOOK_SKIP_SIGNATURE)")
        return
    secrets = [s.strip() for s in (settings.instagram_app_secret, settings.meta_app_secret) if s and s.strip()]
    headers = [h.strip() for h in (header256, header1) if h and h.strip()]
    if not secrets or not headers:
        raise HTTPException(status_code=401, detail="Missing signature")
    for secret in secrets:
        key = secret.encode()
        digest256 = hmac.new(key, raw, hashlib.sha256).hexdigest()
        digest1 = hmac.new(key, raw, hashlib.sha1).hexdigest()
        candidates = {
            f"sha256={digest256}",
            digest256,
            f"sha1={digest1}",
            digest1,
        }
        for header in headers:
            for c in candidates:
                if len(header) == len(c) and hmac.compare_digest(header, c):
                    return
                lowered = header.lower()
                if len(lowered) == len(c) and hmac.compare_digest(lowered, c):
                    return
    _log("[webhook] bad signature; set INSTAGRAM_APP_SECRET from Instagram app secret Show")
    raise HTTPException(status_code=401, detail="Bad signature")


def _seen(session: Session, key: str) -> bool:
    if session.query(ProcessedEvent).filter_by(event_key=key).first():
        return True
    session.add(ProcessedEvent(event_key=key, created_at=utcnow()))
    session.commit()
    return False


@router.get("/webhooks/meta")
def verify_webhook(request: Request) -> Response:
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == get_settings().meta_webhook_verify_token:
        return Response(content=params.get("hub.challenge", ""), media_type="text/plain")
    if not params.get("hub.mode"):
        return Response(
            content='{"ok":true,"hint":"Open this URL only from Meta Verify. Opening it in Chrome is not a test."}',
            media_type="application/json",
        )
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhooks/meta")
async def receive_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    x_hub_signature: str | None = Header(default=None),
) -> dict[str, str]:
    raw = await request.body()
    print(f"[webhook] POST bytes={len(raw)} sig256={bool(x_hub_signature_256)} sig1={bool(x_hub_signature)}", flush=True)
    _verify_signature(raw, x_hub_signature_256, x_hub_signature)
    payload = json.loads(raw.decode("utf-8") or "{}")
    print(
        f"[webhook] object={payload.get('object')} entries={len(payload.get('entry') or [])}",
        flush=True,
    )
    session = SessionLocal()
    try:
        for entry in payload.get("entry") or []:
            _handle_entry(session, entry)
    finally:
        session.close()
    return {"ok": "true"}


def _handle_entry(session: Session, entry: dict) -> None:
    entry_id = str(entry.get("id") or "")
    brand = brand_by_ig_id(entry_id) or brand_by_page_id(entry_id)
    if not brand:
        print(f"[webhook] unmatched entry id={entry_id}", flush=True)
        return

    for change in entry.get("changes") or []:
        field = change.get("field")
        value = change.get("value") or {}
        print(f"[webhook] field={field}", flush=True)
        if field == "comments":
            _handle_comment(session, brand, value)
        elif field in {"messages", "message"}:
            _handle_dm(session, brand, value)

    for messaging in entry.get("messaging") or []:
        _handle_dm(session, brand, messaging)


def _handle_comment(session: Session, brand, value: dict) -> None:
    comment_id = str(value.get("id") or "")
    text = str(value.get("text") or (value.get("message") or {}).get("text") or "")
    from_id = str((value.get("from") or {}).get("id") or "")
    if not comment_id or not text:
        return
    if _seen(session, f"comment:{comment_id}"):
        return

    rules = brand_rules(brand.slug)
    if rules.get("ignore_own_account", True) and from_id in brand.ids():
        return

    reply, _ = first_reply(text, rules.get("comments") or [])
    if not reply:
        return
    try:
        reply_to_comment(comment_id, reply, brand.page_token)
    except GraphError as exc:
        print(f"[comments] {brand.slug} failed: {exc}")


def _handle_dm(session: Session, brand, messaging: dict) -> None:
    sender = str((messaging.get("sender") or {}).get("id") or "")
    message = messaging.get("message") or {}
    mid = str(message.get("mid") or "")
    text = str(message.get("text") or "")
    if message.get("is_echo"):
        return
    if not sender or not mid:
        return
    if _seen(session, f"dm:{mid}"):
        return
    if not text:
        return

    rules = brand_rules(brand.slug)
    if rules.get("ignore_own_account", True) and sender in brand.ids():
        return

    reply, is_wildcard = first_reply(text, rules.get("dms") or [])
    if not reply:
        return
    if is_wildcard and rules.get("dm_default_once_per_day", True):
        if is_default_sent_recent(session, brand.slug, sender):
            return
    try:
        send_dm(brand.ig_user_id, sender, reply, brand.page_token)
    except GraphError as exc:
        print(f"[dms] {brand.slug} failed: {exc}")
        return
    if is_wildcard and rules.get("dm_default_once_per_day", True):
        session.add(
            DmDefaultSent(
                brand_slug=brand.slug,
                sender_id=sender,
                sent_at=datetime.now(timezone.utc),
            )
        )
        session.commit()

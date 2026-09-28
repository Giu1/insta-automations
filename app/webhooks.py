"""Receives Instagram webhooks (comments, messages) and sends the configured reply."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, Response

from app.config import Brand, ConfigError, brand_for_id, load_replies
from app.db import SessionLocal, mark_seen, record_welcome, welcome_sent_recently
from app.instagram import InstagramError
from app.replies import decide_comment, decide_message
from app.settings import get_settings
from app.tokens import client_for

log = logging.getLogger("webhooks")
router = APIRouter()


# ----- security -----


def _signature_ok(raw: bytes, header: str | None) -> bool:
    s = get_settings()
    if not header:
        return False
    for secret in (s.instagram_app_secret, s.meta_app_secret):
        if secret and hmac.compare_digest(header, "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()):
            return True
    return False


# ----- endpoints -----


@router.get("/webhooks/meta")
def verify(request: Request) -> Response:
    """Meta calls this once when you save the webhook URL in the dashboard."""
    q = request.query_params
    if q.get("hub.mode") == "subscribe" and q.get("hub.verify_token") == get_settings().webhook_verify_token:
        return Response(q.get("hub.challenge", ""), media_type="text/plain")
    raise HTTPException(403, "Verify token does not match")


@router.post("/webhooks/meta")
async def receive(request: Request, tasks: BackgroundTasks, x_hub_signature_256: str | None = Header(None)) -> dict:
    raw = await request.body()
    if not _signature_ok(raw, x_hub_signature_256):
        log.warning("webhook rejected: bad signature (check INSTAGRAM_APP_SECRET)")
        raise HTTPException(401, "Bad signature")
    payload = json.loads(raw or b"{}")
    tasks.add_task(handle_payload, payload)  # reply after answering Meta quickly
    return {"ok": True}


# ----- processing -----


def handle_payload(payload: dict) -> None:
    for entry in payload.get("entry") or []:
        brand = brand_for_id(str(entry.get("id") or ""))
        if not brand:
            log.info("ignored event for unknown account id=%s", entry.get("id"))
            continue
        try:
            for change in entry.get("changes") or []:
                if change.get("field") == "comments":
                    _comment(brand, change.get("value") or {})
            for msg in entry.get("messaging") or []:
                _message(brand, msg)
        except ConfigError as exc:
            log.error("[%s] config problem, no reply sent: %s", brand.slug, exc)


def _comment(brand: Brand, value: dict) -> None:
    comment_id = str(value.get("id") or "")
    text = str(value.get("text") or "")
    author = str((value.get("from") or {}).get("id") or "")
    if not comment_id or not text or author in brand.instagram_ids:
        return
    with SessionLocal() as session:
        if not mark_seen(session, f"comment:{comment_id}"):
            return
    decision = decide_comment(brand, text)
    if not decision:
        log.info("[%s] comment %s: no rule matched", brand.slug, comment_id)
        return
    try:
        client_for(brand).reply_to_comment(comment_id, decision.text)
        log.info("[%s] comment %s -> rule '%s' (%s)", brand.slug, comment_id, decision.rule, decision.language)
    except InstagramError as exc:
        log.error("[%s] comment reply failed: %s", brand.slug, exc)


def _message(brand: Brand, msg: dict) -> None:
    message = msg.get("message") or {}
    sender = str((msg.get("sender") or {}).get("id") or "")
    mid = str(message.get("mid") or "")
    text = str(message.get("text") or "")
    if message.get("is_echo") or not sender or not mid or not text or sender in brand.instagram_ids:
        return
    with SessionLocal() as session:
        if not mark_seen(session, f"message:{mid}"):
            return
        decision = decide_message(brand, text)
        if not decision:
            log.info("[%s] message %s: no rule matched", brand.slug, mid)
            return
        once = load_replies(brand.slug).welcome_once_per_day
        if decision.is_catch_all and once and welcome_sent_recently(session, brand.slug, sender):
            return
        try:
            client_for(brand).send_message(sender, decision.text)
            log.info("[%s] message %s -> rule '%s' (%s)", brand.slug, mid, decision.rule, decision.language)
        except InstagramError as exc:
            log.error("[%s] message reply failed: %s", brand.slug, exc)
            return
        if decision.is_catch_all and once:
            record_welcome(session, brand.slug, sender)

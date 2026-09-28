"""Thin client for the official Instagram API (Instagram Login, graph.instagram.com)."""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.settings import get_settings


class InstagramError(RuntimeError):
    pass


class Instagram:
    def __init__(self, token: str) -> None:
        if not token:
            raise InstagramError("No access token configured for this brand")
        self.token = token
        s = get_settings()
        self.base = f"{s.graph_api_host.rstrip('/')}/{s.graph_api_version}"

    # ----- low level -----
    def _request(self, method: str, path: str, **kwargs: Any) -> dict:
        # Token goes in a header (never in the URL) so it cannot leak into logs.
        headers = {"Authorization": f"Bearer {self.token}"}
        with httpx.Client(timeout=60, headers=headers) as client:
            r = client.request(method, f"{self.base}/{path.lstrip('/')}", **kwargs)
        try:
            body = r.json()
        except ValueError:
            body = {"error": {"message": r.text[:300]}}
        if r.status_code >= 400 or "error" in body:
            err = body.get("error", {})
            raise InstagramError(f"{err.get('message', body)} (code {err.get('code')}, sub {err.get('error_subcode')})")
        return body

    def get(self, path: str, **params: Any) -> dict:
        return self._request("GET", path, params=params)

    def post(self, path: str, data: dict | None = None, json: dict | None = None) -> dict:
        return self._request("POST", path, data=data, json=json)

    # ----- account -----
    def me(self) -> dict:
        return self.get("me", fields="id,user_id,username,account_type")

    def refresh_token(self) -> dict:
        """Extends a long-lived token by 60 days. Works only if the token is older than 24h."""
        return self.get("refresh_access_token", grant_type="ig_refresh_token")

    def subscribe_webhooks(self, fields: str = "comments,messages") -> dict:
        return self.post("me/subscribed_apps", data={"subscribed_fields": fields})

    # ----- replies -----
    def reply_to_comment(self, comment_id: str, text: str) -> dict:
        return self.post(f"{comment_id}/replies", data={"message": text})

    def send_message(self, recipient_id: str, text: str) -> dict:
        return self.post("me/messages", json={"recipient": {"id": recipient_id}, "message": {"text": text}})

    # ----- publishing -----
    def publish(self, *, post_type: str, media_url: str, caption: str) -> str:
        """Create container -> wait until ready -> publish. Returns the new media id."""
        data: dict[str, Any] = {"caption": caption}
        if post_type == "image":
            data["image_url"] = media_url
        elif post_type == "reel":
            data.update(media_type="REELS", video_url=media_url)
        elif post_type == "story":
            data["media_type"] = "STORIES"
            key = "video_url" if media_url.lower().endswith((".mp4", ".mov")) else "image_url"
            data[key] = media_url
        else:
            raise InstagramError(f"Unknown post type '{post_type}'")
        container = str(self.post("me/media", data=data)["id"])
        deadline = time.time() + 300
        while time.time() < deadline:
            status = self.get(container, fields="status_code").get("status_code")
            if status == "FINISHED":
                break
            if status in ("ERROR", "EXPIRED"):
                raise InstagramError(f"Instagram could not process the media (status {status})")
            time.sleep(5)
        else:
            raise InstagramError("Media took too long to process")
        return str(self.post("me/media_publish", data={"creation_id": container})["id"])

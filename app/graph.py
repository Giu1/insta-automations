from __future__ import annotations

import time
from typing import Any

import httpx

from app.settings import get_settings


class GraphError(RuntimeError):
    pass


def _url(path: str) -> str:
    settings = get_settings()
    host = settings.graph_api_host.rstrip("/")
    return f"{host}/{settings.graph_api_version}/{path.lstrip('/')}"


def graph_get(path: str, token: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    q = dict(params or {})
    q["access_token"] = token
    with httpx.Client(timeout=60) as client:
        r = client.get(_url(path), params=q)
    data = r.json()
    if r.status_code >= 400 or "error" in data:
        raise GraphError(str(data))
    return data


def graph_post(path: str, token: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = dict(data or {})
    payload["access_token"] = token
    with httpx.Client(timeout=120) as client:
        r = client.post(_url(path), data=payload)
    body = r.json()
    if r.status_code >= 400 or "error" in body:
        raise GraphError(str(body))
    return body


def reply_to_comment(comment_id: str, message: str, token: str) -> dict[str, Any]:
    return graph_post(f"{comment_id}/replies", token, {"message": message})


def send_dm(ig_user_id: str, igsid: str, text: str, token: str) -> dict[str, Any]:
    with httpx.Client(timeout=60) as client:
        r = client.post(
            _url(f"{ig_user_id}/messages"),
            params={"access_token": token},
            json={"recipient": {"id": igsid}, "message": {"text": text}},
        )
    body = r.json()
    if r.status_code >= 400 or "error" in body:
        raise GraphError(str(body))
    return body


def create_media_container(
    ig_user_id: str,
    token: str,
    *,
    caption: str,
    image_url: str | None,
    video_url: str | None,
    media_type: str,
) -> str:
    payload: dict[str, Any] = {"caption": caption}
    media_type = media_type.upper()
    if media_type in {"REELS", "STORIES", "VIDEO"}:
        payload["media_type"] = media_type
        if not video_url:
            raise GraphError("video_url required for REELS/STORIES/VIDEO")
        payload["video_url"] = video_url
    else:
        if not image_url:
            raise GraphError("image_url required for IMAGE")
        payload["image_url"] = image_url
    data = graph_post(f"{ig_user_id}/media", token, payload)
    return str(data["id"])


def wait_container_ready(container_id: str, token: str, timeout_s: int = 180) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        data = graph_get(container_id, token, {"fields": "status_code"})
        status = data.get("status_code")
        if status == "FINISHED":
            return
        if status in {"ERROR", "EXPIRED"}:
            raise GraphError(str(data))
        time.sleep(3)
    raise GraphError(f"container {container_id} not ready in time")


def publish_container(ig_user_id: str, container_id: str, token: str) -> str:
    data = graph_post(f"{ig_user_id}/media_publish", token, {"creation_id": container_id})
    return str(data["id"])

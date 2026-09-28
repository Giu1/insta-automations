"""Web server: Instagram webhooks, scheduled publishing, legal pages, health check."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

from app.config import ConfigError, load_brands
from app.db import init_db
from app.publisher import publish_due
from app.settings import get_settings
from app.tokens import refresh_all, token_for
from app.webhooks import router as webhooks

logging.basicConfig(level=get_settings().log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
for noisy in ("httpx", "httpcore", "apscheduler"):
    logging.getLogger(noisy).setLevel(logging.WARNING)
scheduler = BackgroundScheduler(timezone="UTC")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    scheduler.add_job(publish_due, "interval", minutes=1, id="publish", max_instances=1)
    scheduler.add_job(refresh_all, "interval", days=1, id="refresh-tokens")
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="Insta Automations", docs_url=None, redoc_url=None, lifespan=lifespan)
app.include_router(webhooks)


@app.get("/health")
def health() -> JSONResponse:
    try:
        brands = {b.slug: {"token": bool(token_for(b))} for b in load_brands().values()}
        return JSONResponse({"status": "ok", "brands": brands})
    except ConfigError as exc:
        return JSONResponse({"status": "config-error", "detail": str(exc)}, status_code=500)


@app.get("/privacy")
def privacy() -> FileResponse:
    return FileResponse(get_settings().docs_dir / "privacy.html")


@app.get("/data-deletion")
def data_deletion() -> FileResponse:
    return FileResponse(get_settings().docs_dir / "data-deletion.html")


@app.post("/deauthorize")
def deauthorize() -> dict:
    """Meta calls this when a user removes the app. We only acknowledge."""
    return {"success": True}

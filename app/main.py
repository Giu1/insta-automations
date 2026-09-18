from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from app.api import router as api_router
from app.db import SessionLocal, init_db
from app.publisher import publish_due_posts
from app.legal import router as legal_router
from app.webhooks import router as webhook_router

scheduler = BackgroundScheduler()


def _tick() -> None:
    session = SessionLocal()
    try:
        publish_due_posts(session)
    finally:
        session.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    scheduler.add_job(_tick, "interval", seconds=30, id="publish_due", replace_existing=True)
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="Insta Automations", lifespan=lifespan)
app.include_router(webhook_router)
app.include_router(api_router)
app.include_router(legal_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

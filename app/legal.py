from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

PUBLIC = Path(__file__).resolve().parents[1] / "public"
router = APIRouter()


@router.get("/privacy")
@router.get("/legal/privacy")
def privacy() -> FileResponse:
    return FileResponse(PUBLIC / "privacy.html", media_type="text/html")


@router.get("/data-deletion")
@router.get("/legal/data-deletion")
def data_deletion() -> FileResponse:
    return FileResponse(PUBLIC / "data-deletion.html", media_type="text/html")


@router.post("/legal/deauthorize")
def deauthorize() -> JSONResponse:
    """Meta deauthorize callback. Always acknowledge."""
    return JSONResponse({"success": True})

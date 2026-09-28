"""Environment settings. Values come from .env (local) or the host's secret env vars."""

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    # From Meta App Dashboard -> Instagram -> API setup with Instagram login -> "Instagram app secret"
    instagram_app_secret: str = ""
    # Optional: Meta App settings -> Basic -> App secret (accepted as a fallback for signatures)
    meta_app_secret: str = ""
    # Any string you choose; must match the "Verify token" typed in the Meta webhook settings
    webhook_verify_token: str = "change-me"

    graph_api_host: str = "https://graph.instagram.com"
    graph_api_version: str = "v21.0"

    database_url: str = "sqlite:///./data/app.db"
    config_dir: Path = ROOT / "config"
    docs_dir: Path = ROOT / "docs"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()

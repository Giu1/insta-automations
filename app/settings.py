from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    meta_app_id: str = ""
    meta_app_secret: str = ""
    instagram_app_secret: str = ""
    webhook_skip_signature: bool = False
    meta_webhook_verify_token: str = "change-me"
    graph_api_version: str = "v21.0"
    graph_api_host: str = "https://graph.instagram.com"
    api_key: str = "change-me"
    public_base_url: str = ""
    host: str = "0.0.0.0"
    port: int = 8080
    database_url: str = "sqlite:///./data/app.db"
    brands_path: Path = ROOT / "config" / "brands.yaml"
    rules_path: Path = ROOT / "config" / "rules.yaml"


@lru_cache
def get_settings() -> Settings:
    return Settings()

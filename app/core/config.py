from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "china-job-aggregator"
    env: Literal["dev", "test", "prod"] = "dev"
    debug: bool = False
    api_prefix: str = "/api/v1"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/jobdb"
    log_level: str = "INFO"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    scheduler_enabled: bool = True
    scheduler_timezone: str = "Asia/Shanghai"
    scheduler_default_interval_minutes: int = 30

    crawler_default_timeout_seconds: int = 20
    crawler_default_retry_count: int = 3
    crawler_default_backoff_seconds: float = 1.0
    sites_config_path: str = "configs/sites.yaml"


@lru_cache
def get_settings() -> Settings:
    return Settings()

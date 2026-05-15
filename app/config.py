from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Order MVP API"
    app_version: str = "1.0.0"
    debug: bool = False

    database_url: str = "sqlite:///./orders.db"

    api_key: str = "dev-api-key-change-in-production"

    max_upload_size_mb: int = 10
    allowed_origins: list[str] = ["*"]

    rate_limit_requests: int = 100
    rate_limit_period: str = "minute"

    secret_key: str = "change-this-secret-key-in-production"
    access_token_expire_minutes: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()

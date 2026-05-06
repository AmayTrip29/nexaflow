"""NexaFlow — Application Configuration"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    APP_NAME: str = "NexaFlow"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Auth
    SECRET_KEY: str = "nexaflow-dev-secret-key-please-change-in-prod-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./nexaflow.db"

    # Analysis limits
    MAX_FILE_SIZE_KB: int = 500
    MAX_FILES_PER_REVIEW: int = 20
    ANALYSIS_TIMEOUT_SECONDS: int = 30

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100


settings = Settings()

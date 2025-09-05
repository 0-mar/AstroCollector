import logging
from pathlib import Path
from typing import Any

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    PROJECT_NAME: str = "AstroCollector"
    DEBUG: bool = False
    APPLAUSE_TOKEN: str

    DB_USER: str = Field(..., alias="POSTGRES_USER")
    DB_PASSWORD: str = Field(..., alias="POSTGRES_PASSWORD")
    DB_PORT: int = Field(..., alias="POSTGRES_PORT")
    DB_NAME: str = Field(..., alias="POSTGRES_DB")
    DB_HOST: str = Field(..., alias="POSTGRES_HOST")
    CACHE_PORT: str = Field(..., alias="REDIS_PORT")

    LOGGING_CONSOLE_LEVEL: int = logging.INFO
    TASK_DATA_DELETE_INTERVAL: int = 2  # in hours
    MAX_PAGINATION_BATCH_COUNT: int = 5000

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SYNC_DATABASE_URL(self) -> str:
        return f"postgresql+psycopg3://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def LOGGING_CONFIG(self) -> dict[str, Any]:
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "base": {
                    "()": "uvicorn.logging.DefaultFormatter",
                    "fmt": "%(asctime)s : %(name)s : %(levelname)s : %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": self.LOGGING_CONSOLE_LEVEL,
                    "formatter": "base",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "root": {
                    "level": "DEBUG",
                    "handlers": [
                        "console",
                    ],
                },
            },
        }

    model_config = SettingsConfigDict(
        env_file=(Path(".env")),
        env_file_encoding="utf-8",
        populate_by_name=True,
    )


settings = Settings()

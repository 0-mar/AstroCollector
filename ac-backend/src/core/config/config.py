import logging
from pathlib import Path
from typing import Any, Literal

from passlib.context import CryptContext
from pydantic import Field, computed_field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    PROJECT_NAME: str = "AstroCollector"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ROOT_DIR(self) -> Path:
        return Path.joinpath(Path(__file__).parent.parent.parent.parent).resolve()

    DEBUG: bool = False
    APPLAUSE_TOKEN: str

    DB_USER: str = Field(..., alias="POSTGRES_USER")
    DB_PASSWORD: str = Field(..., alias="POSTGRES_PASSWORD")
    DB_PORT: int = Field(..., alias="POSTGRES_PORT")
    DB_NAME: str = Field(..., alias="POSTGRES_DB")
    DB_HOST: str = Field(..., alias="POSTGRES_HOST")

    REDIS_HOST: str = Field(..., alias="REDIS_HOST")
    REDIS_PORT: str = Field(..., alias="REDIS_PORT")

    OBJECT_SEARCH_RADIUS: float = 30

    @computed_field  # type: ignore[prop-decorator]
    @property
    def CELERY_CONFIG(self) -> dict[str, Any]:
        return {
            "broker_url": f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0",
            "task_ignore_result": True,
            # "result_backend": f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1",
            "result_expires": self.TASK_DATA_DELETE_INTERVAL
            * 3600,  # Task results expire in 1 hour (cleanup)
            "task_track_started": True,  # Enable tracking the STARTED state of tasks
            "task_acks_late": True,  # Acknowledge tasks after execution, not before
            "worker_prefetch_multiplier": 1,  # Each worker grabs only 1 task at a time
            "worker_hijack_root_logger": False,  # Keep previously configured handlers on the root logger
            "beat_schedule": {
                "database-cleanup": {
                    "task": "src.tasks.tasks.clear_task_data",
                    "schedule": self.TASK_DATA_DELETE_INTERVAL * 3600,
                },
            },
        }

    @computed_field  # type: ignore[prop-decorator]
    @property
    def PLUGIN_DIR(self) -> Path:
        return Path.joinpath(self.ROOT_DIR, "plugins").resolve()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def TEMP_DIR(self) -> Path:
        return Path.joinpath(self.ROOT_DIR, "temp").resolve()

    LOGGING_LEVEL: int = logging.INFO

    @computed_field  # type: ignore[prop-decorator]
    @property
    def LOGGING_DIR(self) -> Path:
        return Path.joinpath(self.ROOT_DIR, "logs").resolve()

    TASK_DATA_DELETE_INTERVAL: int = 2  # in hours
    MAX_PAGINATION_BATCH_COUNT: int = 5000

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SYNC_DATABASE_URL(self) -> str:
        return f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def LOGGING_CONFIG(self) -> dict[str, Any]:
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "base": {
                    "()": "uvicorn.logging.DefaultFormatter",
                    "fmt": "[%(levelname)s %(asctime)s]: %(name)s - %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": self.LOGGING_LEVEL,
                    "formatter": "base",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "class": "logging.handlers.TimedRotatingFileHandler",
                    "level": self.LOGGING_LEVEL,
                    "utc": True,
                    "formatter": "base",
                    "filename": self.LOGGING_DIR / "api.log",
                    # Rotate daily
                    "when": "midnight",
                    # Number of files to keep.
                    "backupCount": 8,
                    # every day
                    "interval": 1,
                },
            },
            "loggers": {
                "root": {
                    "level": "DEBUG",
                    "handlers": ["console", "file"],
                },
            },
        }

    # -----------------------
    # Auth settings
    # -----------------------
    REFRESH_TOKEN_EXPIRE_SECONDS: int = 24 * 60 * 60
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 10 * 60
    SECRET_KEY: SecretStr = Field(
        default=SecretStr(""),
        description="Secret key for JWT. If not provided, a random one will be generated.",
        frozen=False,
    )
    ALGORITHM: str = "HS256"
    REFRESH_SAME_SITE: Literal["lax", "strict", "none"] = "lax"
    """The SameSite attribute of the refresh token cookie."""
    REFRESH_SECURE: bool = True
    """The Secure attribute of the refresh token cookie."""
    REFRESH_HTTPONLY: bool = True
    """The HttpOnly attribute of the refresh token cookie."""

    COOKIE_DOMAIN: str | None = None
    """The domain attribute of the cookies. If None, the domain is not set."""

    pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # Super admin credentials
    SUPER_ADMIN_USERNAME: str = "admin"
    SUPER_ADMIN_PASSWORD: str
    SUPER_ADMIN_EMAIL: str

    model_config = SettingsConfigDict(
        env_file=(Path(".env")),
        env_file_encoding="utf-8",
        populate_by_name=True,
    )


settings = Settings()

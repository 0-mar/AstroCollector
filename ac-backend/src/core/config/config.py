from pathlib import Path

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    PROJECT_NAME: str = "AstroCollector"
    DEBUG: bool = False

    DB_USER: str = Field(..., alias="POSTGRES_USER")
    DB_PASSWORD: str = Field(..., alias="POSTGRES_PASSWORD")
    DB_PORT: int = Field(..., alias="POSTGRES_PORT")
    DB_NAME: str = Field(..., alias="POSTGRES_DB")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@localhost:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(
        env_file=(Path("../podman/.env"), Path(".env")),
        env_file_encoding="utf-8",
        populate_by_name=True,
    )


settings = Settings()

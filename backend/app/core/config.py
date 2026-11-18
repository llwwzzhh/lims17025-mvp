"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Laboratory LIMS API"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://lims:lims@localhost:5432/lims"
    jwt_secret: str = "development-only-change-me"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

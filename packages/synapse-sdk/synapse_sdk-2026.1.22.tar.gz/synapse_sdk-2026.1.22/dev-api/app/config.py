"""Application configuration."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    app_name: str = "Synapse Pipeline Service"
    debug: bool = True

    # Database
    database_url: str = "sqlite:///./data/pipeline.db"

    # API
    api_prefix: str = "/api/v1"

    class Config:
        env_prefix = "PIPELINE_"
        env_file = ".env"


settings = Settings()

# Ensure data directory exists
data_dir = Path("./data")
data_dir.mkdir(exist_ok=True)

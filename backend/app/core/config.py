from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root (backend/app/core/config.py -> parents[3]), so .env is found whatever the working directory.
ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        extra="ignore",
    )

    app_name: str = "DFIP"
    database_url: str = "sqlite:///./dfip.db"

    jwt_secret_key: str = "change-me"
    access_token_expire_minutes: int = 60

    admin_email: str = "admin@dfip.local"
    admin_password: str = "Admin@123"


settings = Settings()
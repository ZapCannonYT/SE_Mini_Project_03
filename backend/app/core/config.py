from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "DFIP"
    database_url: str = "sqlite:///./dfip.db"
    secret_key: str = "change-me"


settings = Settings()

from app.core.config import ROOT_DIR, Settings


def test_settings_are_read_from_the_environment(monkeypatch):
    monkeypatch.setenv("APP_NAME", "DFIP-Test")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./other.db")

    settings = Settings()

    assert settings.app_name == "DFIP-Test"
    assert settings.database_url == "sqlite:///./other.db"


def test_env_file_is_looked_up_at_the_repo_root():
    assert (ROOT_DIR / "backend" / "app" / "main.py").exists()
    assert Settings.model_config["env_file"] == ROOT_DIR / ".env"

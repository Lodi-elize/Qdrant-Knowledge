from pathlib import Path

from app.core.config import Settings


def test_settings_reads_utf8_bom_env_file(tmp_path: Path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("APP_ADMIN_SECRET=bom-secret\n", encoding="utf-8-sig")
    monkeypatch.delenv("APP_ADMIN_SECRET", raising=False)

    settings = Settings(_env_file=env_file)

    assert settings.admin_secret == "bom-secret"


def test_default_cors_allows_frontend_dev_server():
    settings = Settings(_env_file=None)

    assert "http://localhost:8080" in settings.cors_origins
    assert "http://127.0.0.1:8080" in settings.cors_origins

from app.core.config import Settings


def test_default_cors_allows_frontend_dev_server():
    settings = Settings(_env_file=None)

    assert "http://localhost:8080" in settings.cors_origins
    assert "http://127.0.0.1:8080" in settings.cors_origins

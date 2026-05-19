from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    app_name: str = "AI Knowledge Assistant"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:8080", "http://127.0.0.1:8080"]
    )

    admin_secret: str = "dev-admin-secret"
    admin_cookie_name: str = "admin_session"
    admin_session_ttl_seconds: int = 8 * 60 * 60
    admin_cookie_secure: bool = False

    vector_backend: Literal["qdrant", "memory"] = "qdrant"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "product_docs"
    embedding_dimensions: int = 64

    model_provider: Literal["local", "openai-compatible"] = "local"
    embedding_provider: Literal["local", "openai-compatible"] = "local"
    openai_api_base: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_chat_api_base: str | None = None
    openai_chat_api_key: str | None = None
    openai_embedding_api_base: str | None = None
    openai_embedding_api_key: str | None = None
    chat_model: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-small"

    chunk_size: int = 900
    chunk_overlap: int = 120
    default_top_k: int = 4
    max_upload_bytes: int = 10 * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()

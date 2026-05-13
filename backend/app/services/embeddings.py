import hashlib
import math

import httpx

from app.core.config import Settings


class EmbeddingService:
    def embed(self, text: str) -> list[float]:
        raise NotImplementedError


class HashEmbeddingService(EmbeddingService):
    """Deterministic local embedding used for tests and offline development."""

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = [token.lower() for token in text.split() if token.strip()]
        for token in tokens or [text.lower()]:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class OpenAICompatibleEmbeddingService(EmbeddingService):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def embed(self, text: str) -> list[float]:
        api_key = self.settings.openai_embedding_api_key or self.settings.openai_api_key
        api_base = self.settings.openai_embedding_api_base or self.settings.openai_api_base
        if not api_key:
            raise RuntimeError("APP_OPENAI_API_KEY is required for openai-compatible embeddings.")
        response = httpx.post(
            f"{api_base.rstrip('/')}/embeddings",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": self.settings.embedding_model, "input": text},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]

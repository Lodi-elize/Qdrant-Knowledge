import hashlib
import math
import re

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
        tokens = tokenize_for_embedding(text)
        for token in tokens or [text.lower()]:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


def tokenize_for_embedding(text: str) -> list[str]:
    normalized = text.lower()
    tokens = re.findall(r"[a-z0-9]+", normalized)
    cjk_chars = re.findall(r"[\u4e00-\u9fff]", normalized)
    tokens.extend(cjk_chars)
    tokens.extend("".join(cjk_chars[index : index + 2]) for index in range(max(len(cjk_chars) - 1, 0)))
    tokens.extend("".join(cjk_chars[index : index + 3]) for index in range(max(len(cjk_chars) - 2, 0)))
    return [token for token in tokens if token.strip()]


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


class HuggingFaceBgeEmbeddingService(EmbeddingService):
    def __init__(self, settings: Settings) -> None:
        from langchain_huggingface import HuggingFaceEmbeddings

        self.model = HuggingFaceEmbeddings(
            model_name=settings.huggingface_embedding_model,
            model_kwargs={"device": settings.huggingface_embedding_device},
            encode_kwargs={"normalize_embeddings": True},
        )

    def embed(self, text: str) -> list[float]:
        return list(self.model.embed_query(text))

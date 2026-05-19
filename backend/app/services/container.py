from functools import lru_cache

from app.core.config import Settings, get_settings
from app.services.embeddings import (
    EmbeddingService,
    HashEmbeddingService,
    HuggingFaceBgeEmbeddingService,
    OpenAICompatibleEmbeddingService,
)
from app.services.generation import GenerationService
from app.services.ingestion import IngestionService
from app.services.knowledge_bases import KnowledgeBaseService
from app.services.retrieval import ScopedRetrievalService
from app.services.vector_store import InMemoryVectorRepository, QdrantVectorRepository, VectorRepository


@lru_cache
def get_knowledge_base_service() -> KnowledgeBaseService:
    return KnowledgeBaseService()


@lru_cache
def get_embedding_service() -> EmbeddingService:
    settings = get_settings()
    if settings.embedding_provider == "openai-compatible":
        return OpenAICompatibleEmbeddingService(settings)
    if settings.embedding_provider == "huggingface":
        return HuggingFaceBgeEmbeddingService(settings)
    return HashEmbeddingService(settings.embedding_dimensions)


@lru_cache
def get_vector_repository() -> VectorRepository:
    settings = get_settings()
    if settings.vector_backend == "memory":
        return InMemoryVectorRepository()
    return QdrantVectorRepository(settings)


def get_retrieval_service() -> ScopedRetrievalService:
    return ScopedRetrievalService(
        get_embedding_service(),
        get_vector_repository(),
        min_score=get_settings().min_retrieval_score,
    )


def get_generation_service() -> GenerationService:
    return GenerationService(get_settings())


def get_ingestion_service() -> IngestionService:
    return IngestionService(
        settings=get_settings(),
        embeddings=get_embedding_service(),
        vector_repository=get_vector_repository(),
        knowledge_bases=get_knowledge_base_service(),
    )


def reset_services_for_tests() -> None:
    from app.core.security import clear_admin_sessions_for_tests

    get_settings.cache_clear()
    get_knowledge_base_service.cache_clear()
    get_embedding_service.cache_clear()
    get_vector_repository.cache_clear()
    clear_admin_sessions_for_tests()

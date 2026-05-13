from app.models.schemas import KnowledgeBaseScope, Source
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorRepository


class ScopedRetrievalService:
    """The only application service allowed to perform query-time vector search."""

    def __init__(self, embeddings: EmbeddingService, vector_repository: VectorRepository) -> None:
        self.embeddings = embeddings
        self.vector_repository = vector_repository

    def retrieve(self, scope: KnowledgeBaseScope, question: str, limit: int) -> list[Source]:
        query_vector = self.embeddings.embed(question)
        return self.vector_repository.search(scope=scope, query_vector=query_vector, limit=limit)


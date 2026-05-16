import math
from typing import Protocol

from app.core.config import Settings
from app.models.schemas import DocumentChunk, KnowledgeBase, KnowledgeBaseScope, Source


class VectorRepository(Protocol):
    def upsert_chunks(self, chunks: list[DocumentChunk], vectors: list[list[float]]) -> None:
        ...

    def search(self, scope: KnowledgeBaseScope, query_vector: list[float], limit: int) -> list[Source]:
        ...

    def list_knowledge_bases(self) -> list[KnowledgeBase]:
        ...


class InMemoryVectorRepository:
    def __init__(self) -> None:
        self._items: list[tuple[DocumentChunk, list[float]]] = []

    def upsert_chunks(self, chunks: list[DocumentChunk], vectors: list[list[float]]) -> None:
        existing_ids = {chunk.id for chunk in chunks}
        self._items = [(chunk, vector) for chunk, vector in self._items if chunk.id not in existing_ids]
        self._items.extend(zip(chunks, vectors, strict=True))

    def search(self, scope: KnowledgeBaseScope, query_vector: list[float], limit: int) -> list[Source]:
        scoped = [
            (chunk, vector)
            for chunk, vector in self._items
            if chunk.product_line == scope.product_line and chunk.product_version == scope.product_version
        ]
        scored = sorted(
            ((chunk, _cosine(query_vector, vector)) for chunk, vector in scoped),
            key=lambda item: item[1],
            reverse=True,
        )
        return [_source_from_chunk(chunk, score) for chunk, score in scored[:limit]]

    def list_knowledge_bases(self) -> list[KnowledgeBase]:
        scopes = {
            (chunk.product_line, chunk.product_version)
            for chunk, _vector in self._items
        }
        return [
            KnowledgeBase(product_line=product_line, product_version=product_version)
            for product_line, product_version in sorted(scopes)
        ]


class QdrantVectorRepository:
    def __init__(self, settings: Settings) -> None:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams

        self.settings = settings
        if settings.qdrant_url == ":memory:":
            self.client = QdrantClient(location=":memory:")
        else:
            self.client = QdrantClient(url=settings.qdrant_url)
        collections = {collection.name for collection in self.client.get_collections().collections}
        if settings.qdrant_collection not in collections:
            self.client.create_collection(
                collection_name=settings.qdrant_collection,
                vectors_config=VectorParams(size=settings.embedding_dimensions, distance=Distance.COSINE),
            )

    def upsert_chunks(self, chunks: list[DocumentChunk], vectors: list[list[float]]) -> None:
        from qdrant_client.models import PointStruct

        points = [
            PointStruct(
                id=chunk.id,
                vector=vector,
                payload=chunk.model_dump(),
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        self.client.upsert(collection_name=self.settings.qdrant_collection, points=points)

    def search(self, scope: KnowledgeBaseScope, query_vector: list[float], limit: int) -> list[Source]:
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        query_filter = Filter(
            must=[
                FieldCondition(key="product_line", match=MatchValue(value=scope.product_line)),
                FieldCondition(key="product_version", match=MatchValue(value=scope.product_version)),
            ]
        )
        try:
            results = self.client.query_points(
                collection_name=self.settings.qdrant_collection,
                query=query_vector,
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
            ).points
        except AttributeError:
            results = self.client.search(
                collection_name=self.settings.qdrant_collection,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
            )
        return [
            Source(
                document_id=result.payload["document_id"],
                file_name=result.payload["file_name"],
                product_line=result.payload["product_line"],
                product_version=result.payload["product_version"],
                chunk_index=result.payload["chunk_index"],
                score=float(result.score),
                text=result.payload["text"],
            )
            for result in results
        ]

    def list_knowledge_bases(self) -> list[KnowledgeBase]:
        scopes: set[tuple[str, str]] = set()
        offset = None
        while True:
            points, offset = self.client.scroll(
                collection_name=self.settings.qdrant_collection,
                limit=256,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for point in points:
                payload = point.payload or {}
                product_line = payload.get("product_line")
                product_version = payload.get("product_version")
                if isinstance(product_line, str) and isinstance(product_version, str):
                    scopes.add((product_line, product_version))
            if offset is None:
                break
        return [
            KnowledgeBase(product_line=product_line, product_version=product_version)
            for product_line, product_version in sorted(scopes)
        ]


def _cosine(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right, strict=False))
    left_norm = math.sqrt(sum(a * a for a in left)) or 1.0
    right_norm = math.sqrt(sum(b * b for b in right)) or 1.0
    return dot / (left_norm * right_norm)


def _source_from_chunk(chunk: DocumentChunk, score: float) -> Source:
    return Source(
        document_id=chunk.document_id,
        file_name=chunk.file_name,
        product_line=chunk.product_line,
        product_version=chunk.product_version,
        chunk_index=chunk.chunk_index,
        score=score,
        text=chunk.text,
    )
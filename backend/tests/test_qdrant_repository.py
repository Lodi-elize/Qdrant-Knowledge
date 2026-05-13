from uuid import uuid4

from app.core.config import Settings
from app.models.schemas import DocumentChunk, KnowledgeBaseScope
from app.services.embeddings import HashEmbeddingService
from app.services.vector_store import QdrantVectorRepository


def test_qdrant_repository_filters_product_version_scope():
    settings = Settings(
        vector_backend="qdrant",
        qdrant_url=":memory:",
        qdrant_collection=f"test_product_docs_{uuid4().hex}",
        embedding_dimensions=32,
    )
    embeddings = HashEmbeddingService(dimensions=settings.embedding_dimensions)
    repository = QdrantVectorRepository(settings)

    alpha_v1 = DocumentChunk(
        id=str(uuid4()),
        document_id="doc-v1",
        file_name="alpha-v1.txt",
        product_line="Alpha",
        product_version="v1",
        chunk_index=0,
        text="Alpha v1 reset code is BLUE-111.",
    )
    alpha_v2 = DocumentChunk(
        id=str(uuid4()),
        document_id="doc-v2",
        file_name="alpha-v2.txt",
        product_line="Alpha",
        product_version="v2",
        chunk_index=0,
        text="Alpha v2 reset code is GREEN-222.",
    )
    repository.upsert_chunks(
        [alpha_v1, alpha_v2],
        [embeddings.embed(alpha_v1.text), embeddings.embed(alpha_v2.text)],
    )

    v1_results = repository.search(
        KnowledgeBaseScope(product_line="Alpha", product_version="v1"),
        embeddings.embed("reset code"),
        limit=10,
    )
    v2_results = repository.search(
        KnowledgeBaseScope(product_line="Alpha", product_version="v2"),
        embeddings.embed("reset code"),
        limit=10,
    )

    assert v1_results
    assert v2_results
    assert all(result.product_version == "v1" for result in v1_results)
    assert all(result.product_version == "v2" for result in v2_results)
    assert "GREEN-222" not in " ".join(result.text for result in v1_results)
    assert "BLUE-111" not in " ".join(result.text for result in v2_results)

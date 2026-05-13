from app.models.schemas import DocumentChunk, KnowledgeBaseScope
from app.services.embeddings import HashEmbeddingService
from app.services.retrieval import ScopedRetrievalService
from app.services.vector_store import InMemoryVectorRepository


def test_scoped_retrieval_requires_scope_and_filters_results():
    embeddings = HashEmbeddingService(dimensions=32)
    repository = InMemoryVectorRepository()
    alpha_scope = KnowledgeBaseScope(product_line="Alpha", product_version="v1")
    beta_scope = KnowledgeBaseScope(product_line="Beta", product_version="v1")
    alpha = DocumentChunk(
        id="alpha-1",
        document_id="doc-alpha",
        file_name="alpha.txt",
        product_line="Alpha",
        product_version="v1",
        chunk_index=0,
        text="Alpha install token is ALPHA-ONLY.",
    )
    beta = DocumentChunk(
        id="beta-1",
        document_id="doc-beta",
        file_name="beta.txt",
        product_line="Beta",
        product_version="v1",
        chunk_index=0,
        text="Beta install token is BETA-ONLY.",
    )
    repository.upsert_chunks([alpha, beta], [embeddings.embed(alpha.text), embeddings.embed(beta.text)])

    service = ScopedRetrievalService(embeddings, repository)
    results = service.retrieve(alpha_scope, "install token", limit=10)

    assert results
    assert all(result.product_line == "Alpha" for result in results)
    assert all("BETA-ONLY" not in result.text for result in results)
    assert service.retrieve(beta_scope, "install token", limit=10)[0].product_line == "Beta"


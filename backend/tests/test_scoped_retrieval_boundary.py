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


def test_scoped_retrieval_discards_low_score_noise():
    class FixedEmbeddingService:
        def embed(self, text: str) -> list[float]:
            return [1.0, 0.0]

    class FixedRepository:
        def search(self, scope: KnowledgeBaseScope, query_vector: list[float], limit: int):
            from app.models.schemas import Source

            return [
                Source(
                    document_id="doc-noise",
                    file_name="guide.txt",
                    product_line=scope.product_line,
                    product_version=scope.product_version,
                    chunk_index=0,
                    score=0.05,
                    text="This should not be treated as a matched document.",
                )
            ]

    service = ScopedRetrievalService(FixedEmbeddingService(), FixedRepository(), min_score=0.2)

    assert service.retrieve(KnowledgeBaseScope(product_line="Alpha", product_version="v1"), "asdf qwer", limit=4) == []


def test_scoped_retrieval_reranks_lexical_matches_ahead_of_vector_score():
    class FixedEmbeddingService:
        def embed(self, text: str) -> list[float]:
            return [1.0, 0.0]

    class FixedRepository:
        def search(self, scope: KnowledgeBaseScope, query_vector: list[float], limit: int):
            from app.models.schemas import Source

            return [
                Source(
                    document_id="doc-general",
                    file_name="general.txt",
                    product_line=scope.product_line,
                    product_version=scope.product_version,
                    chunk_index=0,
                    score=0.3,
                    text="这里介绍产品合同签署流程。",
                ),
                Source(
                    document_id="doc-refund",
                    file_name="refund.txt",
                    product_line=scope.product_line,
                    product_version=scope.product_version,
                    chunk_index=0,
                    score=0.22,
                    text="退款规则：客户可在14天内申请退款。",
                ),
            ]

    service = ScopedRetrievalService(FixedEmbeddingService(), FixedRepository(), min_score=0.2)

    results = service.retrieve(KnowledgeBaseScope(product_line="Alpha", product_version="v1"), "退款规则是什么", limit=2)

    assert results[0].file_name == "refund.txt"


def test_scoped_retrieval_rejects_chinese_query_without_enough_evidence():
    class FixedEmbeddingService:
        def embed(self, text: str) -> list[float]:
            return [1.0, 0.0]

    class FixedRepository:
        def search(self, scope: KnowledgeBaseScope, query_vector: list[float], limit: int):
            from app.models.schemas import Source

            return [
                Source(
                    document_id="doc-finance",
                    file_name="finance.txt",
                    product_line=scope.product_line,
                    product_version=scope.product_version,
                    chunk_index=0,
                    score=0.32,
                    text="\u79c1\u52df\u4ea7\u54c1\u9700\u8981\u914d\u7f6e\u9884\u7ea6\u548c\u56de\u8bbf\u6d41\u7a0b\u3002",
                )
            ]

    service = ScopedRetrievalService(FixedEmbeddingService(), FixedRepository(), min_score=0.2)

    assert (
        service.retrieve(
            KnowledgeBaseScope(product_line="Delta", product_version="v1"),
            "\u5b89\u88c5\u9700\u8981\u54ea\u4e2a\u7aef\u53e3\uff1f",
            limit=4,
        )
        == []
    )


def test_scoped_retrieval_matches_chinese_synonyms():
    class FixedEmbeddingService:
        def embed(self, text: str) -> list[float]:
            return [1.0, 0.0]

    class FixedRepository:
        def search(self, scope: KnowledgeBaseScope, query_vector: list[float], limit: int):
            from app.models.schemas import Source

            return [
                Source(
                    document_id="doc-refund",
                    file_name="refund.txt",
                    product_line=scope.product_line,
                    product_version=scope.product_version,
                    chunk_index=0,
                    score=0.21,
                    text="\u56de\u8bbf\u672a\u786e\u8ba4\u65f6\u4f1a\u53d6\u6d88\u8d2d\u4e70\uff0c\u8d44\u91d1\u539f\u8def\u9000\u56de\u3002",
                )
            ]

    service = ScopedRetrievalService(FixedEmbeddingService(), FixedRepository(), min_score=0.2)

    results = service.retrieve(
        KnowledgeBaseScope(product_line="Delta", product_version="v1"),
        "\u9000\u6b3e\u89c4\u5219\u662f\u4ec0\u4e48\uff1f",
        limit=4,
    )

    assert results
    assert results[0].file_name == "refund.txt"


def test_scoped_retrieval_keeps_mixed_language_terms_specific():
    class FixedEmbeddingService:
        def embed(self, text: str) -> list[float]:
            return [1.0, 0.0]

    class FixedRepository:
        def search(self, scope: KnowledgeBaseScope, query_vector: list[float], limit: int):
            from app.models.schemas import Source

            return [
                Source(
                    document_id="doc-appointment",
                    file_name="appointment.txt",
                    product_line=scope.product_line,
                    product_version=scope.product_version,
                    chunk_index=0,
                    score=0.35,
                    text="\u9884\u7ea6\u767b\u8bb0\u671f\u4e3aT-10\u65e5\u81f3T-1\u65e512\u70b9\u524d\u3002",
                ),
                Source(
                    document_id="doc-trade-day",
                    file_name="trade-day.txt",
                    product_line=scope.product_line,
                    product_version=scope.product_version,
                    chunk_index=0,
                    score=0.22,
                    text="T\u65e5\u662f\u57fa\u91d1\u4ea4\u6613\u4e2d\u7684\u4ea4\u6613\u65e5\u3002",
                ),
            ]

    service = ScopedRetrievalService(FixedEmbeddingService(), FixedRepository(), min_score=0.2)

    results = service.retrieve(
        KnowledgeBaseScope(product_line="Delta", product_version="v1"),
        "T\u65e5\u662f\u4ec0\u4e48\uff1f",
        limit=4,
    )

    assert [result.file_name for result in results] == ["trade-day.txt"]


def test_scoped_retrieval_uses_lexical_fallback_for_named_entities():
    class FixedEmbeddingService:
        def embed(self, text: str) -> list[float]:
            return [1.0, 0.0]

    class FixedRepository:
        def search(self, scope: KnowledgeBaseScope, query_vector: list[float], limit: int):
            from app.models.schemas import Source

            return [
                Source(
                    document_id="doc-general",
                    file_name="general.txt",
                    product_line=scope.product_line,
                    product_version=scope.product_version,
                    chunk_index=0,
                    score=0.4,
                    text="\u8fd9\u91cc\u4ecb\u7ecd\u57fa\u91d1\u884c\u4e1a\u6587\u5316\u5efa\u8bbe\u3002",
                )
            ]

        def lexical_search(self, scope: KnowledgeBaseScope, terms: list[str], limit: int):
            from app.models.schemas import Source

            if scope.product_line != "Alpha":
                return []
            return [
                Source(
                    document_id="doc-tonghua",
                    file_name="\u901a\u534e.md",
                    product_line=scope.product_line,
                    product_version=scope.product_version,
                    chunk_index=0,
                    score=0.2,
                    text="\u901a\u534e\u8d22\u5bcc\u662f\u4e00\u5bb6\u7b2c\u4e09\u65b9\u57fa\u91d1\u9500\u552e\u673a\u6784\u3002",
                )
            ]

    service = ScopedRetrievalService(FixedEmbeddingService(), FixedRepository(), min_score=0.2)

    alpha_results = service.retrieve(
        KnowledgeBaseScope(product_line="Alpha", product_version="v1"),
        "\u901a\u534e\u8d22\u5bcc\u662f\u4ec0\u4e48\uff1f",
        limit=4,
    )
    delta_results = service.retrieve(
        KnowledgeBaseScope(product_line="Delta", product_version="v1"),
        "\u901a\u534e\u8d22\u5bcc\u662f\u4ec0\u4e48\uff1f",
        limit=4,
    )

    assert alpha_results
    assert alpha_results[0].file_name == "\u901a\u534e.md"
    assert delta_results == []


def test_scoped_retrieval_prioritizes_exact_article_references():
    class FixedEmbeddingService:
        def embed(self, text: str) -> list[float]:
            return [1.0, 0.0]

    class FixedRepository:
        def search(self, scope: KnowledgeBaseScope, query_vector: list[float], limit: int):
            from app.models.schemas import Source

            return [
                Source(
                    document_id="doc-constitution",
                    file_name="\u5baa\u6cd5.pdf",
                    product_line=scope.product_line,
                    product_version=scope.product_version,
                    chunk_index=8,
                    score=0.42,
                    text="\u7b2c\u4e09\u5341\u4e09\u6761 \u51e1\u5177\u6709\u4e2d\u534e\u4eba\u6c11\u5171\u548c\u56fd\u56fd\u7c4d\u7684\u4eba\u90fd\u662f\u516c\u6c11\u3002",
                )
            ]

        def lexical_search(self, scope: KnowledgeBaseScope, terms: list[str], limit: int):
            from app.models.schemas import Source

            return [
                Source(
                    document_id="doc-constitution",
                    file_name="\u5baa\u6cd5.pdf",
                    product_line=scope.product_line,
                    product_version=scope.product_version,
                    chunk_index=7,
                    score=0.2,
                    text=(
                        "\u7b2c\u4e8c\u5341\u516b\u6761 \u56fd\u5bb6\u7ef4\u62a4\u793e\u4f1a\u79e9\u5e8f\u3002"
                        "\u7b2c\u4e8c\u5341\u4e5d\u6761 \u4e2d\u534e\u4eba\u6c11\u5171\u548c\u56fd\u7684\u6b66\u88c5\u529b\u91cf\u5c5e\u4e8e\u4eba\u6c11\u3002"
                    ),
                )
            ]

    service = ScopedRetrievalService(FixedEmbeddingService(), FixedRepository(), min_score=0.2)

    results = service.retrieve(
        KnowledgeBaseScope(product_line="Beta", product_version="v1"),
        "\u7b2c29\u6761\u662f\u4ec0\u4e48\uff1f",
        limit=4,
    )

    assert results
    assert results[0].chunk_index == 7
    assert "\u7b2c\u4e8c\u5341\u4e5d\u6761" in results[0].text
    assert results[0].text.startswith("\u7b2c\u4e8c\u5341\u4e5d\u6761")
    assert "\u7b2c\u4e8c\u5341\u516b\u6761" not in results[0].text


def test_scoped_retrieval_extracts_only_requested_article_text():
    class FixedEmbeddingService:
        def embed(self, text: str) -> list[float]:
            return [1.0, 0.0]

    class FixedRepository:
        def search(self, scope: KnowledgeBaseScope, query_vector: list[float], limit: int):
            return []

        def lexical_search(self, scope: KnowledgeBaseScope, terms: list[str], limit: int):
            from app.models.schemas import Source

            return [
                Source(
                    document_id="doc-rules",
                    file_name="\u6761\u6b3e.md",
                    product_line=scope.product_line,
                    product_version=scope.product_version,
                    chunk_index=3,
                    score=0.2,
                    text=(
                        "\u7b2c\u4e03\u5341\u4e5d\u6761 \u4e0a\u4e00\u6761\u5185\u5bb9\u3002\n"
                        "\u7b2c\u516b\u5341\u6761 \u5ba2\u6237\u5e94\u5f53\u6309\u7ea6\u5b9a\u63d0\u4ea4\u8d44\u6599\u3002\n"
                        "\u7b2c\u516b\u5341\u4e00\u6761 \u4e0b\u4e00\u6761\u5185\u5bb9\u3002"
                    ),
                )
            ]

    service = ScopedRetrievalService(FixedEmbeddingService(), FixedRepository(), min_score=0.2)

    results = service.retrieve(
        KnowledgeBaseScope(product_line="Beta", product_version="v1"),
        "\u7b2c\u516b\u5341\u6761",
        limit=4,
    )

    assert results
    assert results[0].text == "\u7b2c\u516b\u5341\u6761 \u5ba2\u6237\u5e94\u5f53\u6309\u7ea6\u5b9a\u63d0\u4ea4\u8d44\u6599\u3002"


def test_scoped_retrieval_extracts_requested_interface_code_section():
    class FixedEmbeddingService:
        def embed(self, text: str) -> list[float]:
            return [1.0, 0.0]

    class FixedRepository:
        def search(self, scope: KnowledgeBaseScope, query_vector: list[float], limit: int):
            return []

        def lexical_search(self, scope: KnowledgeBaseScope, terms: list[str], limit: int):
            from app.models.schemas import Source

            return [
                Source(
                    document_id="doc-api",
                    file_name="api.md",
                    product_line=scope.product_line,
                    product_version=scope.product_version,
                    chunk_index=16,
                    score=0.2,
                    text=(
                        "### \u57fa\u91d1\u6298\u6263\u8d39\u7387\u67e5\u8be2 (F30015)\n"
                        "URL\uff1a/fundTrans/fundDiscountFeeRateQuery\n\n"
                        "### \u5ba2\u6237\u98ce\u9669\u7b49\u7ea7\u4e0e\u4ea7\u54c1\u662f\u5426\u5339\u914d\u67e5\u8be2 (F30016)\n"
                        "URL\uff1a/fundTrans/custRiskIsMatchedQuery\n"
                        "\u8bf7\u6c42\uff1aregist_custno, fund_code\n"
                        "\u5e94\u7b54\uff1ais_matched, is_all_matched, mismatchItems\n\n"
                        "### \u9996\u9875\u57fa\u91d1\u540d\u79f0\u67e5\u8be2 (F30017)\n"
                        "URL\uff1a/fundTrans/hpFundNameQuery"
                    ),
                )
            ]

    service = ScopedRetrievalService(FixedEmbeddingService(), FixedRepository(), min_score=0.2)

    results = service.retrieve(
        KnowledgeBaseScope(product_line="Gamma", product_version="v1"),
        "F30016\u7684\u5185\u5bb9\u662f\u4ec0\u4e48",
        limit=4,
    )

    assert results
    assert results[0].text.startswith("### \u5ba2\u6237\u98ce\u9669\u7b49\u7ea7")
    assert "F30016" in results[0].text
    assert "custRiskIsMatchedQuery" in results[0].text
    assert "F30015" not in results[0].text
    assert "F30017" not in results[0].text

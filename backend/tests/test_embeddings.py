from app.services.embeddings import HashEmbeddingService
from app.services.vector_store import _cosine


def test_hash_embedding_uses_chinese_character_ngrams():
    embeddings = HashEmbeddingService(dimensions=128)

    related = _cosine(embeddings.embed("退款规则是什么"), embeddings.embed("客户可以在14天内申请退款。"))
    unrelated = _cosine(embeddings.embed("退款规则是什么"), embeddings.embed("安装端口是9443。"))

    assert related > unrelated


def test_huggingface_embedding_service_wraps_langchain_model(monkeypatch):
    from app.core.config import Settings
    from app.services.embeddings import HuggingFaceBgeEmbeddingService

    captured: dict[str, object] = {}

    class FakeHuggingFaceEmbeddings:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def embed_query(self, text: str):
            return [0.1, 0.2, 0.3]

    import langchain_huggingface

    monkeypatch.setattr(langchain_huggingface, "HuggingFaceEmbeddings", FakeHuggingFaceEmbeddings)

    service = HuggingFaceBgeEmbeddingService(
        Settings(
            embedding_provider="huggingface",
            huggingface_embedding_model="BAAI/bge-small-zh-v1.5",
            huggingface_embedding_device="cpu",
        )
    )

    assert service.embed("测试") == [0.1, 0.2, 0.3]
    assert captured["model_name"] == "BAAI/bge-small-zh-v1.5"
    assert captured["model_kwargs"] == {"device": "cpu"}
    assert captured["encode_kwargs"] == {"normalize_embeddings": True}

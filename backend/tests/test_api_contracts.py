from io import BytesIO

from app.core.config import Settings
from app.models.schemas import Source
from app.services.generation import GenerationService


def test_query_requires_scope_and_question(client):
    response = client.post("/api/query", json={"question": "hello"})
    assert response.status_code == 422


def test_admin_upload_requires_admin_credentials(client):
    response = client.post(
        "/api/admin/upload",
        params={"product_line": "Alpha", "product_version": "v1"},
        files={"file": ("guide.txt", BytesIO(b"Alpha v1 setup guide"), "text/plain")},
    )
    assert response.status_code == 401


def test_admin_secret_stays_server_side_and_allows_upload(client):
    login = client.post("/api/admin/login", json={"admin_secret": "test-secret"})
    assert login.status_code == 200
    assert client.cookies.get("admin_session") != "test-secret"

    response = client.post(
        "/api/admin/upload",
        params={"product_line": "Alpha", "product_version": "v1"},
        files={"file": ("guide.txt", BytesIO(b"Alpha v1 setup guide"), "text/plain")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["product_line"] == "Alpha"
    assert payload["product_version"] == "v1"
    assert payload["chunks_indexed"] >= 1


def test_query_response_shape(client):
    client.post(
        "/api/admin/upload",
        params={"product_line": "Alpha", "product_version": "v1"},
        headers={"X-Admin-Secret": "test-secret"},
        files={"file": ("guide.txt", BytesIO(b"Alpha v1 reset password steps"), "text/plain")},
    )
    response = client.post(
        "/api/query",
        json={"product_line": "Alpha", "product_version": "v1", "question": "How do I reset password?"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "answer",
        "grounded_summary",
        "sources",
        "used_supplemental_knowledge",
        "generated_by_ai",
        "generation_notice",
        "supplemental_note",
    }
    assert isinstance(payload["generated_by_ai"], bool)
    assert payload["generation_notice"]
    assert payload["sources"]
    assert payload["sources"][0]["product_line"] == "Alpha"
    assert payload["sources"][0]["product_version"] == "v1"


def test_remote_generation_failure_falls_back_to_knowledge_base(monkeypatch):
    def fail_agent(*args, **kwargs):
        return None

    monkeypatch.setattr(GenerationService, "_langchain_agent_answer", fail_agent)
    service = GenerationService(
        Settings(
            model_provider="openai-compatible",
            openai_chat_api_key="test-key",
        )
    )

    response = service.answer(
        "How do I reset password?",
        [
            Source(
                document_id="doc-1",
                file_name="guide.txt",
                product_line="Alpha",
                product_version="v1",
                chunk_index=0,
                score=1.0,
                text="Reset password with code BLUE-111.",
            )
        ],
    )

    assert response.generated_by_ai is False
    assert response.generation_notice == "Extracted from knowledge base"
    assert "BLUE-111" in response.answer

    no_source_response = service.answer("Unknown question", [])

    assert no_source_response.generated_by_ai is False
    assert no_source_response.answer == "\u6211\u8fd8\u6ca1\u6709\u52a0\u8f7d\u5f53\u524d\u77e5\u8bc6"
    assert no_source_response.generation_notice == "No matched knowledge-base content"


def test_no_retrieved_sources_returns_missing_knowledge_without_agent(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("LangChain agent should not be called without retrieved sources")

    monkeypatch.setattr(GenerationService, "_langchain_agent_answer", fail_if_called)
    service = GenerationService(
        Settings(
            model_provider="openai-compatible",
            enable_ai_generation=True,
            openai_chat_api_key="test-key",
        )
    )

    response = service.answer("\u672a\u77e5\u95ee\u9898", [])

    assert response.answer == "\u6211\u8fd8\u6ca1\u6709\u52a0\u8f7d\u5f53\u524d\u77e5\u8bc6"
    assert response.grounded_summary == "\u6211\u8fd8\u6ca1\u6709\u52a0\u8f7d\u5f53\u524d\u77e5\u8bc6"
    assert response.sources == []
    assert response.generated_by_ai is False
    assert response.used_supplemental_knowledge is False
    assert response.generation_notice == "No matched knowledge-base content"


def test_article_question_sends_focused_article_to_remote_generation(monkeypatch):
    captured: dict[str, object] = {}

    def fake_agent(self, question, sources, exact_extraction=False):
        captured["question"] = question
        captured["source_text"] = sources[0].text
        captured["exact_extraction"] = exact_extraction
        return "\u7b2c\u516b\u5341\u6761 \u7cbe\u51c6\u6790\u51fa\u7684\u7b54\u6848\u3002"

    monkeypatch.setattr(GenerationService, "_langchain_agent_answer", fake_agent)
    service = GenerationService(
        Settings(
            model_provider="openai-compatible",
            enable_ai_generation=True,
            openai_chat_api_key="test-key",
        )
    )

    response = service.answer(
        "\u7b2c\u516b\u5341\u6761\u662f\u4ec0\u4e48\uff1f",
        [
            Source(
                document_id="doc-rules",
                file_name="\u6761\u6b3e.md",
                product_line="Beta",
                product_version="v1",
                chunk_index=3,
                score=1.0,
                text=(
                    "\u7b2c\u4e03\u5341\u4e5d\u6761 \u4e0a\u4e00\u6761\u5185\u5bb9\u3002"
                    "\u7b2c\u516b\u5341\u6761 \u5ba2\u6237\u5e94\u5f53\u6309\u7ea6\u5b9a\u63d0\u4ea4\u8d44\u6599\u3002"
                    "\u7b2c\u516b\u5341\u4e00\u6761 \u4e0b\u4e00\u6761\u5185\u5bb9\u3002"
                ),
            )
        ],
    )

    assert captured["question"] == "\u7b2c\u516b\u5341\u6761\u662f\u4ec0\u4e48\uff1f"
    assert "\u7b2c\u4e03\u5341\u4e5d\u6761" not in captured["source_text"]
    assert captured["source_text"] == "\u7b2c\u516b\u5341\u6761 \u5ba2\u6237\u5e94\u5f53\u6309\u7ea6\u5b9a\u63d0\u4ea4\u8d44\u6599\u3002"
    assert "\u7b2c\u516b\u5341\u4e00\u6761" not in captured["source_text"]
    assert captured["exact_extraction"] is True
    assert response.answer == "\u7b2c\u516b\u5341\u6761 \u7cbe\u51c6\u6790\u51fa\u7684\u7b54\u6848\u3002"
    assert response.sources[0].text == "\u7b2c\u516b\u5341\u6761 \u5ba2\u6237\u5e94\u5f53\u6309\u7ea6\u5b9a\u63d0\u4ea4\u8d44\u6599\u3002"
    assert response.generated_by_ai is True
    assert response.generation_notice == "AI extracted answer from matched knowledge-base context"


def test_interface_code_question_sends_focused_section_to_remote_generation(monkeypatch):
    captured: dict[str, object] = {}

    def fake_agent(self, question, sources, exact_extraction=False):
        captured["question"] = question
        captured["source_text"] = sources[0].text
        captured["exact_extraction"] = exact_extraction
        return "F30016 \u7cbe\u51c6\u63d0\u53d6\u7684\u63a5\u53e3\u5185\u5bb9\u3002"

    monkeypatch.setattr(GenerationService, "_langchain_agent_answer", fake_agent)
    service = GenerationService(
        Settings(
            model_provider="openai-compatible",
            enable_ai_generation=True,
            openai_chat_api_key="test-key",
        )
    )

    response = service.answer(
        "F30016\u7684\u5185\u5bb9\u662f\u4ec0\u4e48\uff1f",
        [
            Source(
                document_id="doc-api",
                file_name="api.md",
                product_line="Gamma",
                product_version="v1",
                chunk_index=16,
                score=1.0,
                text=(
                    "### \u57fa\u91d1\u6298\u6263\u8d39\u7387\u67e5\u8be2 (F30015)\n"
                    "URL\uff1a/fundTrans/fundDiscountFeeRateQuery\n"
                    "### \u5ba2\u6237\u98ce\u9669\u7b49\u7ea7\u4e0e\u4ea7\u54c1\u662f\u5426\u5339\u914d\u67e5\u8be2 (F30016)\n"
                    "URL\uff1a/fundTrans/custRiskIsMatchedQuery\n"
                    "\u8bf7\u6c42\uff1aregist_custno, fund_code\n"
                    "### \u9996\u9875\u57fa\u91d1\u540d\u79f0\u67e5\u8be2 (F30017)\n"
                    "URL\uff1a/fundTrans/hpFundNameQuery"
                ),
            )
        ],
    )

    assert captured["question"] == "F30016\u7684\u5185\u5bb9\u662f\u4ec0\u4e48\uff1f"
    assert captured["source_text"].startswith("### \u5ba2\u6237\u98ce\u9669\u7b49\u7ea7")
    assert "F30016" in captured["source_text"]
    assert "F30015" not in captured["source_text"]
    assert "F30017" not in captured["source_text"]
    assert captured["exact_extraction"] is True
    assert response.answer == "F30016 \u7cbe\u51c6\u63d0\u53d6\u7684\u63a5\u53e3\u5185\u5bb9\u3002"
    assert response.generation_notice == "AI extracted answer from matched knowledge-base context"


def test_article_question_falls_back_to_exact_article_when_remote_fails(monkeypatch):
    def fail_agent(*args, **kwargs):
        return None

    monkeypatch.setattr(GenerationService, "_langchain_agent_answer", fail_agent)
    service = GenerationService(
        Settings(
            model_provider="openai-compatible",
            enable_ai_generation=True,
            openai_chat_api_key="test-key",
        )
    )

    response = service.answer(
        "\u7b2c\u516b\u5341\u6761\u662f\u4ec0\u4e48\uff1f",
        [
            Source(
                document_id="doc-rules",
                file_name="\u6761\u6b3e.md",
                product_line="Beta",
                product_version="v1",
                chunk_index=3,
                score=1.0,
                text=(
                    "\u7b2c\u4e03\u5341\u4e5d\u6761 \u4e0a\u4e00\u6761\u5185\u5bb9\u3002"
                    "\u7b2c\u516b\u5341\u6761 \u5ba2\u6237\u5e94\u5f53\u6309\u7ea6\u5b9a\u63d0\u4ea4\u8d44\u6599\u3002"
                    "\u7b2c\u516b\u5341\u4e00\u6761 \u4e0b\u4e00\u6761\u5185\u5bb9\u3002"
                ),
            )
        ],
    )

    assert response.answer == "\u7b2c\u516b\u5341\u6761 \u5ba2\u6237\u5e94\u5f53\u6309\u7ea6\u5b9a\u63d0\u4ea4\u8d44\u6599\u3002"
    assert response.sources[0].text == response.answer
    assert response.generated_by_ai is False
    assert response.generation_notice == "Extracted exact article from knowledge base"


def test_ai_generation_disabled_does_not_call_remote_model(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("LangChain agent should not be called when AI generation is disabled")

    monkeypatch.setattr(GenerationService, "_langchain_agent_answer", fail_if_called)
    service = GenerationService(
        Settings(
            model_provider="openai-compatible",
            enable_ai_generation=False,
            openai_chat_api_key="test-key",
        )
    )

    response = service.answer("What is not in the knowledge base?", [])

    assert response.generated_by_ai is False
    assert response.used_supplemental_knowledge is False
    assert response.answer == "\u6211\u8fd8\u6ca1\u6709\u52a0\u8f7d\u5f53\u524d\u77e5\u8bc6"
    assert response.generation_notice == "No matched knowledge-base content"
    assert response.sources == []

from app.core.config import Settings
from app.models.schemas import QueryResponse, Source


class GenerationService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def answer(self, question: str, sources: list[Source]) -> QueryResponse:
        if self.settings.model_provider == "openai-compatible":
            return self._remote_answer(question, sources)
        return self._local_answer(question, sources)

    def _local_answer(self, question: str, sources: list[Source]) -> QueryResponse:
        if sources:
            top = sources[0]
            grounded = top.text[:500]
            return QueryResponse(
                answer=grounded,
                grounded_summary=grounded,
                sources=sources,
                used_supplemental_knowledge=False,
                supplemental_note=None,
            )
        supplemental = (
            "当前知识库没有检索到相关内容。以下回答基于通用产品支持常识，建议补充对应产品线和版本的资料后再确认。"
        )
        return QueryResponse(
            answer=f"{supplemental}\n\n问题：{question}",
            grounded_summary="未检索到可引用的内容。",
            sources=[],
            used_supplemental_knowledge=True,
            supplemental_note=supplemental,
        )

    def _remote_answer(self, question: str, sources: list[Source]) -> QueryResponse:
        import httpx

        api_key = self.settings.openai_chat_api_key or self.settings.openai_api_key
        api_base = self.settings.openai_chat_api_base or self.settings.openai_api_base
        if not api_key:
            raise RuntimeError("APP_OPENAI_API_KEY or APP_OPENAI_CHAT_API_KEY is required for openai-compatible chat.")

        context = "\n\n".join(f"[{idx + 1}] {source.text}" for idx, source in enumerate(sources))
        if sources:
            prompt = (
                "You are a customer-facing product assistant. Answer directly and naturally in the user's language.\n"
                "Rules:\n"
                "- Do not say 'according to official documentation', 'based on retrieved official documentation', '根据官方文档', or similar source-preface phrases.\n"
                "- Do not tell the user to refer to document entries for detailed explanations.\n"
                "- If you use both retrieved content and general model knowledge, blend them into one coherent answer. Do not label any section as 'Model supplemental note'.\n"
                "- Keep the answer concise and useful.\n\n"
                f"User question: {question}\n\nRetrieved content:\n{context}"
            )
        else:
            prompt = (
                "You are a customer-facing product assistant. Answer in the user's language.\n"
                "No retrieved knowledge-base content is available. You may answer from general knowledge, but briefly state that no matching knowledge-base content was found.\n"
                "Do not use the label 'Model supplemental note'.\n\n"
                f"User question: {question}"
            )
        response = httpx.post(
            f"{api_base.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": self.settings.chat_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            },
            timeout=60,
        )
        response.raise_for_status()
        answer = response.json()["choices"][0]["message"]["content"]
        used_supplemental = not sources
        grounded = "已检索到相关内容。" if sources else "未检索到可引用的内容。"
        return QueryResponse(
            answer=answer,
            grounded_summary=grounded,
            sources=sources,
            used_supplemental_knowledge=used_supplemental,
            supplemental_note="当前知识库没有检索到相关内容，回答基于通用模型知识。" if used_supplemental else None,
        )

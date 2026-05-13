from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


NonEmpty = Annotated[str, Field(min_length=1, max_length=120)]


def normalize_key(value: str) -> str:
    return " ".join(value.strip().split())


class KnowledgeBaseScope(BaseModel):
    product_line: NonEmpty
    product_version: NonEmpty

    @field_validator("product_line", "product_version")
    @classmethod
    def normalize(cls, value: str) -> str:
        return normalize_key(value)

    @property
    def key(self) -> str:
        return f"{self.product_line}::{self.product_version}"


class KnowledgeBase(BaseModel):
    product_line: str
    product_version: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def key(self) -> str:
        return f"{self.product_line}::{self.product_version}"


class KnowledgeBaseCreate(KnowledgeBaseScope):
    pass


class QueryRequest(KnowledgeBaseScope):
    question: Annotated[str, Field(min_length=1, max_length=4000)]
    top_k: Annotated[int, Field(ge=1, le=12)] = 4

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        return normalize_key(value)


class Source(BaseModel):
    document_id: str
    file_name: str
    product_line: str
    product_version: str
    chunk_index: int
    score: float
    text: str


class QueryResponse(BaseModel):
    answer: str
    grounded_summary: str
    sources: list[Source]
    used_supplemental_knowledge: bool
    supplemental_note: str | None = None


class UploadResponse(BaseModel):
    document_id: str
    file_name: str
    product_line: str
    product_version: str
    chunks_indexed: int


class AdminLoginRequest(BaseModel):
    admin_secret: str


class DocumentChunk(BaseModel):
    id: str
    document_id: str
    file_name: str
    product_line: str
    product_version: str
    chunk_index: int
    text: str


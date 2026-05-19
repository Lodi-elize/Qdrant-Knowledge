from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import Settings
from app.models.schemas import DocumentChunk, KnowledgeBaseScope, UploadResponse
from app.services.embeddings import EmbeddingService
from app.services.knowledge_bases import KnowledgeBaseService
from app.services.vector_store import VectorRepository


SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


class UnsupportedFileType(ValueError):
    pass


class IngestionService:
    def __init__(
        self,
        settings: Settings,
        embeddings: EmbeddingService,
        vector_repository: VectorRepository,
        knowledge_bases: KnowledgeBaseService,
    ) -> None:
        self.settings = settings
        self.embeddings = embeddings
        self.vector_repository = vector_repository
        self.knowledge_bases = knowledge_bases

    async def ingest_upload(self, scope: KnowledgeBaseScope, upload: UploadFile) -> UploadResponse:
        file_name = Path(upload.filename or "document").name
        raw = await upload.read()
        if len(raw) > self.settings.max_upload_bytes:
            raise ValueError(
                "File exceeds configured upload size limit: "
                f"{_format_bytes(len(raw))} uploaded, {_format_bytes(self.settings.max_upload_bytes)} allowed."
            )

        text = extract_text(file_name, raw)
        chunks = self.build_chunks(scope, file_name, text)
        vectors = [self.embeddings.embed(chunk.text) for chunk in chunks]
        self.knowledge_bases.ensure(scope)
        self.vector_repository.upsert_chunks(chunks, vectors)
        return UploadResponse(
            document_id=chunks[0].document_id if chunks else str(uuid4()),
            file_name=file_name,
            product_line=scope.product_line,
            product_version=scope.product_version,
            chunks_indexed=len(chunks),
        )

    def build_chunks(self, scope: KnowledgeBaseScope, file_name: str, text: str) -> list[DocumentChunk]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
        )
        parts = [part.strip() for part in splitter.split_text(text) if part.strip()]
        document_id = str(uuid4())
        return [
            DocumentChunk(
                id=str(uuid4()),
                document_id=document_id,
                file_name=file_name,
                product_line=scope.product_line,
                product_version=scope.product_version,
                chunk_index=index,
                text=part,
            )
            for index, part in enumerate(parts)
        ]


def extract_text(file_name: str, raw: bytes) -> str:
    suffix = Path(file_name).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileType(f"Unsupported file type: {suffix or '<none>'}")
    if suffix == ".pdf":
        return _extract_pdf(raw)
    return raw.decode("utf-8", errors="ignore")


def _format_bytes(value: int) -> str:
    if value >= 1024 * 1024:
        return f"{value / (1024 * 1024):.1f} MB"
    if value >= 1024:
        return f"{value / 1024:.1f} KB"
    return f"{value} bytes"


def _extract_pdf(raw: bytes) -> str:
    from io import BytesIO

    from pypdf import PdfReader

    reader = PdfReader(BytesIO(raw))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()

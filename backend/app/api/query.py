from fastapi import APIRouter, Depends

from app.core.config import get_settings
from app.models.schemas import KnowledgeBaseScope, QueryRequest, QueryResponse
from app.services.container import get_generation_service, get_retrieval_service
from app.services.generation import GenerationService
from app.services.retrieval import ScopedRetrievalService

router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query", response_model=QueryResponse)
def query(
    request: QueryRequest,
    retrieval: ScopedRetrievalService = Depends(get_retrieval_service),
    generation: GenerationService = Depends(get_generation_service),
) -> QueryResponse:
    settings = get_settings()
    scope = KnowledgeBaseScope(product_line=request.product_line, product_version=request.product_version)
    sources = retrieval.retrieve(scope=scope, question=request.question, limit=request.top_k or settings.default_top_k)
    return generation.answer(question=request.question, sources=sources)


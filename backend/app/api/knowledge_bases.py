from fastapi import APIRouter, Depends

from app.core.security import require_admin
from app.models.schemas import KnowledgeBase, KnowledgeBaseCreate
from app.services.container import get_knowledge_base_service, get_vector_repository
from app.services.knowledge_bases import KnowledgeBaseService
from app.services.vector_store import VectorRepository

router = APIRouter(prefix="/api/knowledge-bases", tags=["knowledge-bases"])


@router.get("", response_model=list[KnowledgeBase])
def list_knowledge_bases(
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
    vector_repository: VectorRepository = Depends(get_vector_repository),
) -> list[KnowledgeBase]:
    items = {item.key: item for item in vector_repository.list_knowledge_bases()}
    items.update({item.key: item for item in service.list()})
    return sorted(items.values(), key=lambda item: (item.product_line, item.product_version))


@router.post("", response_model=KnowledgeBase, dependencies=[Depends(require_admin)])
def create_knowledge_base(
    request: KnowledgeBaseCreate,
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> KnowledgeBase:
    return service.create(request)

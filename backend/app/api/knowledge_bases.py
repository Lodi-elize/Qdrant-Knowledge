from fastapi import APIRouter, Depends

from app.core.security import require_admin
from app.models.schemas import KnowledgeBase, KnowledgeBaseCreate
from app.services.container import get_knowledge_base_service
from app.services.knowledge_bases import KnowledgeBaseService

router = APIRouter(prefix="/api/knowledge-bases", tags=["knowledge-bases"])


@router.get("", response_model=list[KnowledgeBase])
def list_knowledge_bases(
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> list[KnowledgeBase]:
    return service.list()


@router.post("", response_model=KnowledgeBase, dependencies=[Depends(require_admin)])
def create_knowledge_base(
    request: KnowledgeBaseCreate,
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> KnowledgeBase:
    return service.create(request)


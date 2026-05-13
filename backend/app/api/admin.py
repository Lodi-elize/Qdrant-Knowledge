from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status

from app.core.config import get_settings
from app.core.security import create_admin_session, is_valid_admin_secret, require_admin
from app.models.schemas import AdminLoginRequest, KnowledgeBaseScope, UploadResponse
from app.services.container import get_ingestion_service
from app.services.ingestion import IngestionService, UnsupportedFileType

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/login")
def login(request: AdminLoginRequest, response: Response) -> dict[str, str]:
    settings = get_settings()
    if not is_valid_admin_secret(request.admin_secret, settings):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin secret.")
    session_token = create_admin_session(settings)
    response.set_cookie(
        settings.admin_cookie_name,
        session_token,
        httponly=True,
        samesite="lax",
        secure=settings.admin_cookie_secure,
        max_age=settings.admin_session_ttl_seconds,
    )
    return {"status": "ok"}


@router.post("/upload", response_model=UploadResponse, dependencies=[Depends(require_admin)])
async def upload_document(
    product_line: str,
    product_version: str,
    file: UploadFile = File(...),
    ingestion: IngestionService = Depends(get_ingestion_service),
) -> UploadResponse:
    scope = KnowledgeBaseScope(product_line=product_line, product_version=product_version)
    try:
        return await ingestion.ingest_upload(scope, file)
    except UnsupportedFileType as exc:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

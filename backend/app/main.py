from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, knowledge_bases, query
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(query.router)
    app.include_router(admin.router)
    app.include_router(knowledge_bases.router)

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()


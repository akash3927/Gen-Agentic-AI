from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import get_document_service, router
from app.config import Settings, get_settings
from app.services.document_service import DocumentService
from app.services.embeddings import OpenAIEmbeddingProvider
from app.services.registry import DocumentRegistry
from app.services.vector_store import ChromaVectorStore


def build_document_service(settings: Settings) -> DocumentService:
    return DocumentService(
        embedder=OpenAIEmbeddingProvider(
            api_key=settings.openai_api_key,
            model=settings.embedding_model,
            batch_size=settings.embedding_batch_size,
        ),
        vector_store=ChromaVectorStore(path=str(settings.chroma_path)),
        registry=DocumentRegistry(settings.registry_path),
        upload_path=settings.upload_path,
    )


def create_app(service: DocumentService | None = None, settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.document_service = service or build_document_service(settings)
        yield

    app = FastAPI(title="PDF Knowledge Assistant API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    app.dependency_overrides[get_document_service] = lambda: app.state.document_service
    return app


app = create_app()

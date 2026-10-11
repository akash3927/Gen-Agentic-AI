from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

from app.api import get_document_service, get_rag_service, router
from app.config import Settings, get_settings
from app.services.document_service import DocumentService
from app.services.openai_client import OpenAIEmbeddingProvider, OpenAILanguageModel
from app.services.rag_service import RagService
from app.services.registry import DocumentRegistry
from app.services.vector_store import ChromaVectorStore


def build_services(settings: Settings) -> tuple[DocumentService, RagService]:
    if not settings.openai_api_key:
        raise ValueError(
            "OPENAI_API_KEY is required for embeddings and grounded answers."
        )
    client = OpenAI(api_key=settings.openai_api_key)
    embedder = OpenAIEmbeddingProvider(
        client, settings.embedding_model, settings.embedding_batch_size
    )
    vector_store = ChromaVectorStore(path=str(settings.chroma_path))
    documents = DocumentService(
        embedder,
        vector_store,
        DocumentRegistry(settings.registry_path),
        settings.upload_path,
    )
    rag = RagService(
        embedder,
        OpenAILanguageModel(client, settings.llm_model),
        vector_store,
        settings.max_context_characters,
    )
    return documents, rag


def create_app(
    document_service: DocumentService | None = None,
    rag_service: RagService | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if document_service is None or rag_service is None:
            app.state.document_service, app.state.rag_service = build_services(settings)
        else:
            app.state.document_service = document_service
            app.state.rag_service = rag_service
        yield

    app = FastAPI(
        title="Production RAG Assistant API", version="1.0.0", lifespan=lifespan
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    app.dependency_overrides[get_document_service] = lambda: app.state.document_service
    app.dependency_overrides[get_rag_service] = lambda: app.state.rag_service
    return app


app = create_app()

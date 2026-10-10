from hashlib import sha256
from io import BytesIO

import chromadb
import pytest
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from app.main import create_app
from app.services.document_service import DocumentService
from app.services.rag_service import RagService
from app.services.registry import DocumentRegistry
from app.services.vector_store import ChromaVectorStore


class FakeEmbeddingProvider:
    vocabulary = ("python", "database", "ocean", "search", "vector", "music", "policy")

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            lowered = text.lower()
            semantic = [float(lowered.count(word)) for word in self.vocabulary]
            digest = sha256(text.encode()).digest()
            vectors.append(semantic + [byte / 255 for byte in digest[:2]])
        return vectors


class FakeLanguageModel:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def generate(self, instructions: str, prompt: str) -> str:
        self.calls.append((instructions, prompt))
        return "Python uses vector search for retrieval. [Source 1]"


def make_pdf(*page_texts: str) -> bytes:
    stream = BytesIO()
    pdf = canvas.Canvas(stream)
    for text in page_texts:
        pdf.drawString(72, 750, text)
        pdf.showPage()
    pdf.save()
    return stream.getvalue()


@pytest.fixture
def pdf_factory():
    return make_pdf


@pytest.fixture
def services(tmp_path):
    embedder = FakeEmbeddingProvider()
    model = FakeLanguageModel()
    store = ChromaVectorStore(client=chromadb.EphemeralClient())
    documents = DocumentService(
        embedder, store, DocumentRegistry(tmp_path / "documents.json"), tmp_path / "uploads"
    )
    rag = RagService(embedder, model, store, max_context_characters=2_000)
    return documents, rag, model


@pytest.fixture
def client(services):
    documents, rag, _ = services
    with TestClient(create_app(document_service=documents, rag_service=rag)) as test_client:
        yield test_client

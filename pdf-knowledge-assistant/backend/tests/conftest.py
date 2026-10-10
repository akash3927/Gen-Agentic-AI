from hashlib import sha256
from io import BytesIO

import chromadb
import pytest
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from app.main import create_app
from app.services.document_service import DocumentService
from app.services.registry import DocumentRegistry
from app.services.vector_store import ChromaVectorStore


class FakeEmbeddingProvider:
    """Deterministic semantic-ish vectors for tests, without network calls."""

    vocabulary = ("python", "database", "ocean", "search", "vector", "music")

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            lowered = text.lower()
            semantic = [float(lowered.count(word)) for word in self.vocabulary]
            digest = sha256(text.encode()).digest()
            fallback = [byte / 255 for byte in digest[:2]]
            vectors.append(semantic + fallback)
        return vectors


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
def service(tmp_path):
    return DocumentService(
        embedder=FakeEmbeddingProvider(),
        vector_store=ChromaVectorStore(client=chromadb.EphemeralClient()),
        registry=DocumentRegistry(tmp_path / "documents.json"),
        upload_path=tmp_path / "uploads",
    )


@pytest.fixture
def client(service):
    with TestClient(create_app(service=service)) as test_client:
        yield test_client

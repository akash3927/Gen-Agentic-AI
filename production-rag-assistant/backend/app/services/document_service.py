from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.services.chunker import chunk_pages
from app.services.openai_client import EmbeddingProvider
from app.services.pdf_extractor import extract_pdf_pages
from app.services.registry import DocumentRegistry
from app.services.vector_store import ChromaVectorStore


class DocumentNotFoundError(LookupError):
    pass


class DocumentService:
    def __init__(
        self,
        embedder: EmbeddingProvider,
        vector_store: ChromaVectorStore,
        registry: DocumentRegistry,
        upload_path: Path,
    ) -> None:
        self.embedder = embedder
        self.vector_store = vector_store
        self.registry = registry
        self.upload_path = upload_path
        self.upload_path.mkdir(parents=True, exist_ok=True)

    def index(
        self, filename: str, data: bytes, chunk_size: int, chunk_overlap: int
    ) -> dict:
        return self._index(uuid4().hex, filename, data, chunk_size, chunk_overlap, True)

    def _index(
        self,
        document_id: str,
        filename: str,
        data: bytes,
        chunk_size: int,
        chunk_overlap: int,
        save_file: bool,
    ) -> dict:
        pages = extract_pdf_pages(data)
        chunks = chunk_pages(pages, chunk_size, chunk_overlap)
        vectors = self.embedder.embed([chunk.text for chunk in chunks])
        self.vector_store.replace_document(document_id, filename, chunks, vectors)
        path = self.upload_path / f"{document_id}.pdf"
        if save_file:
            path.write_bytes(data)
        record = {
            "id": document_id,
            "filename": filename,
            "page_count": len(pages),
            "chunk_count": len(chunks),
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "indexed_at": datetime.now(timezone.utc).isoformat(),
            "stored_path": str(path),
        }
        self.registry.put(record)
        return record

    def list_documents(self) -> list[dict]:
        return sorted(
            self.registry.list(), key=lambda item: item["indexed_at"], reverse=True
        )

    def delete(self, document_id: str) -> None:
        record = self.registry.get(document_id)
        if not record:
            raise DocumentNotFoundError(document_id)
        self.vector_store.delete_document(document_id)
        self.registry.delete(document_id)
        Path(record["stored_path"]).unlink(missing_ok=True)

    def reindex(
        self, document_id: str, chunk_size: int | None, chunk_overlap: int | None
    ) -> dict:
        record = self.registry.get(document_id)
        if not record:
            raise DocumentNotFoundError(document_id)
        return self._index(
            document_id,
            record["filename"],
            Path(record["stored_path"]).read_bytes(),
            chunk_size if chunk_size is not None else record["chunk_size"],
            chunk_overlap if chunk_overlap is not None else record["chunk_overlap"],
            False,
        )

from typing import Any

import chromadb

from app.services.chunker import TextChunk


class ChromaVectorStore:
    """Direct Chroma operations: add vectors, query by vector, and delete by metadata."""

    def __init__(self, path: str | None = None, client: Any | None = None) -> None:
        self.client = client or chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(
            name="pdf_chunks", metadata={"hnsw:space": "cosine"}
        )

    def replace_document(
        self,
        document_id: str,
        filename: str,
        chunks: list[TextChunk],
        embeddings: list[list[float]],
    ) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("Each chunk must have exactly one embedding.")
        self.delete_document(document_id)
        self.collection.add(
            ids=[f"{document_id}:{chunk.chunk_index}" for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            embeddings=embeddings,
            metadatas=[
                {
                    "document_id": document_id,
                    "pdf_name": filename,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                }
                for chunk in chunks
            ],
        )

    def delete_document(self, document_id: str) -> None:
        self.collection.delete(where={"document_id": document_id})

    def search(self, query_embedding: list[float], top_k: int) -> list[dict]:
        available = self.collection.count()
        if available == 0:
            return []
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, available),
            include=["documents", "metadatas", "distances"],
        )
        rows = []
        for text, metadata, distance in zip(
            result["documents"][0], result["metadatas"][0], result["distances"][0]
        ):
            rows.append(
                {
                    "text": text,
                    "score": round(max(-1.0, min(1.0, 1.0 - float(distance))), 6),
                    **metadata,
                }
            )
        return rows

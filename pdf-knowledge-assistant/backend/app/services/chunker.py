import re
from dataclasses import dataclass

from app.services.pdf_extractor import PageText


@dataclass(frozen=True)
class TextChunk:
    text: str
    page_number: int
    chunk_index: int


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def chunk_pages(
    pages: list[PageText], chunk_size: int = 1_000, chunk_overlap: int = 200
) -> list[TextChunk]:
    """Create overlapping character chunks without crossing page boundaries."""
    if chunk_size < 50:
        raise ValueError("chunk_size must be at least 50 characters.")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be non-negative and smaller than chunk_size."
        )

    chunks: list[TextChunk] = []
    # Overlap keeps nearby context when a sentence falls across two chunks.
    step = chunk_size - chunk_overlap
    for page in pages:
        text = _clean_text(page.text)
        for start in range(0, len(text), step):
            value = text[start : start + chunk_size].strip()
            if value:
                chunks.append(
                    TextChunk(
                        text=value,
                        page_number=page.page_number,
                        chunk_index=len(chunks),
                    )
                )
            if start + chunk_size >= len(text):
                break
    return chunks

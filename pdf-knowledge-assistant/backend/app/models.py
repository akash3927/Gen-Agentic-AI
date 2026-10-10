from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class DocumentResponse(BaseModel):
    id: str
    filename: str
    page_count: int
    chunk_count: int
    chunk_size: int
    chunk_overlap: int
    indexed_at: datetime


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2_000)
    top_k: int = Field(default=5, ge=1, le=50)

    @field_validator("query")
    @classmethod
    def query_must_contain_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Query must contain text.")
        return value


class SearchResult(BaseModel):
    text: str
    score: float
    document_id: str
    pdf_name: str
    page_number: int
    chunk_index: int


class SearchResponse(BaseModel):
    results: list[SearchResult]


class MessageResponse(BaseModel):
    message: str

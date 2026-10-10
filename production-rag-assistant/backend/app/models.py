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


class SourceResponse(BaseModel):
    text: str
    score: float
    document_id: str
    pdf_name: str
    page_number: int
    chunk_index: int


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4_000)
    top_k: int = Field(default=5, ge=1, le=50)
    similarity_threshold: float = Field(default=0.3, ge=-1.0, le=1.0)
    document_ids: list[str] | None = Field(default=None, max_length=100)
    use_query_rewrite: bool = True

    @field_validator("question")
    @classmethod
    def question_must_contain_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Question must contain text.")
        return value


class AnswerResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]
    retrieval_query: str
    insufficient_context: bool


class MessageResponse(BaseModel):
    message: str

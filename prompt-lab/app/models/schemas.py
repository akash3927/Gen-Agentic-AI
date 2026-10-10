from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class PromptCreate(BaseModel):
    prompt_name: str = Field(min_length=1, max_length=80)
    template: str = Field(min_length=1)
    system_instructions: str = ""
    description: str = ""


class PromptTemplate(PromptCreate):
    prompt_id: str
    version: int
    created_at: datetime


class RunRequest(BaseModel):
    prompt_id: Optional[str] = None
    template: Optional[str] = None
    system_instructions: str = ""
    variables: dict[str, Any] = Field(default_factory=dict)
    model: str = "gpt-4o-mini"
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    output_format: Literal["text", "json"] = "text"


class UsageMetrics(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class RunResult(BaseModel):
    experiment_id: str
    prompt_id: Optional[str]
    prompt_version: Optional[int]
    final_prompt: str
    output: str
    model: str
    latency_ms: float
    usage: UsageMetrics
    status: Literal["success", "failed"]
    format_compliant: bool
    evaluation_notes: list[str] = Field(default_factory=list)
    created_at: datetime


class CompareRequest(BaseModel):
    prompt_a_id: str
    prompt_b_id: str
    variables: dict[str, Any] = Field(default_factory=dict)
    model: str = "gpt-4o-mini"
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    output_format: Literal["text", "json"] = "text"


class CompareResult(BaseModel):
    prompt_a: RunResult
    prompt_b: RunResult


class DatasetCase(BaseModel):
    id: str
    input: str
    expected_behavior: str
    expected_keywords: list[str] = Field(default_factory=list)
    max_words: Optional[int] = None


class BatchRequest(BaseModel):
    prompt_id: str
    model: str = "gpt-4o-mini"
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    output_format: Literal["text", "json"] = "text"


class BatchItem(BaseModel):
    case: DatasetCase
    result: RunResult


class BatchResult(BaseModel):
    prompt_id: str
    passed: int
    failed: int
    results: list[BatchItem]


class CandidateAnalysis(BaseModel):
    name: str
    skills: list[str]
    experience_years: int = Field(ge=0)
    recommendation: str


class StructuredRequest(BaseModel):
    candidate_text: str = Field(min_length=1)
    model: str = "gpt-4o-mini"


class StructuredResult(BaseModel):
    parsed: Optional[CandidateAnalysis]
    raw_output: str
    valid: bool
    validation_error: Optional[str] = None

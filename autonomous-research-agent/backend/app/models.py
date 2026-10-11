from __future__ import annotations
from typing import Literal, Optional
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field


class Task(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    status: Literal['pending', 'in_progress', 'done']


class Decision(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: Literal['tool', 'finish']
    summary: str = Field(max_length=1000)
    plan: list[Task] = Field(min_length=1, max_length=12)
    tool: Optional[Literal['web_search', 'read_page', 'calculator', 'save_notes']]
    arguments_json: str
    report: str = Field(max_length=20000)


class Start(BaseModel):
    goal: str = Field(min_length=5, max_length=2000)
    max_steps: int = Field(default=12, ge=1, le=30)
    token_budget: int = Field(default=24000, ge=2000, le=100000)
    demo: bool = False


class State(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    goal: str
    max_steps: int
    token_budget: int
    demo: bool = False
    status: Literal['running', 'awaiting_approval', 'completed', 'stopped', 'failed'] = 'running'
    plan: list[Task] = Field(default_factory=list)
    steps: list[dict] = Field(default_factory=list)
    sources: list[dict] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    report: str = ''
    reason: str = ''
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: Optional[float] = None
    pending: Optional[dict] = None

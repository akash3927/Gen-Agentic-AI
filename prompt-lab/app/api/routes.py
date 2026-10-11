from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.models.schemas import (
    BatchItem,
    BatchRequest,
    BatchResult,
    CompareRequest,
    CompareResult,
    DatasetCase,
    PromptCreate,
    PromptTemplate,
    RunRequest,
    RunResult,
    StructuredRequest,
    StructuredResult,
)
from app.services.evaluation_service import evaluate_output
from app.services.history_service import HistoryService
from app.services.llm_service import LLMService
from app.services.prompt_service import PromptService


router = APIRouter(prefix="/api")
prompts = PromptService()
history = HistoryService()


def llm() -> LLMService:
    try:
        return LLMService()
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"OpenAI client setup failed: {exc}"
        ) from exc


def execute(request: RunRequest, case: DatasetCase | None = None) -> RunResult:
    prompt_version = None
    system = request.system_instructions
    if request.prompt_id:
        try:
            saved = prompts.get(request.prompt_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        template = saved.template
        prompt_version = saved.version
        system = system or saved.system_instructions
    elif request.template:
        template = request.template
    else:
        raise HTTPException(status_code=422, detail="Provide prompt_id or template")

    try:
        final_prompt = prompts.render(template, request.variables)
        output, latency, usage = llm().run(
            prompt=final_prompt,
            system_instructions=system,
            model=request.model,
            temperature=request.temperature,
            output_format=request.output_format,
        )
        compliant, notes = evaluate_output(output, request.output_format, case)
        result = RunResult(
            experiment_id=uuid4().hex,
            prompt_id=request.prompt_id,
            prompt_version=prompt_version,
            final_prompt=final_prompt,
            output=output,
            model=request.model,
            latency_ms=latency,
            usage=usage,
            status="success",
            format_compliant=compliant,
            evaluation_notes=notes,
            created_at=datetime.now(timezone.utc),
        )
        history.add(result)
        return result
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"OpenAI request failed: {exc}"
        ) from exc


@router.get("/prompts", response_model=list[PromptTemplate])
def list_prompts() -> list[PromptTemplate]:
    return prompts.list_prompts()


@router.post("/prompts", response_model=PromptTemplate, status_code=201)
def create_prompt(request: PromptCreate) -> PromptTemplate:
    return prompts.create(request)


@router.post("/run", response_model=RunResult)
def run_prompt(request: RunRequest) -> RunResult:
    return execute(request)


@router.post("/compare", response_model=CompareResult)
def compare(request: CompareRequest) -> CompareResult:
    common = request.model_dump(exclude={"prompt_a_id", "prompt_b_id"})
    return CompareResult(
        prompt_a=execute(RunRequest(prompt_id=request.prompt_a_id, **common)),
        prompt_b=execute(RunRequest(prompt_id=request.prompt_b_id, **common)),
    )


@router.get("/dataset", response_model=list[DatasetCase])
def dataset() -> list[DatasetCase]:
    return [
        DatasetCase.model_validate(item)
        for item in json.loads(settings.dataset_file.read_text())
    ]


@router.post("/batch", response_model=BatchResult)
def batch(request: BatchRequest) -> BatchResult:
    items: list[BatchItem] = []
    for case in dataset():
        variables = {
            "input": case.input,
            "task": case.expected_behavior,
            "context": case.input,
        }
        result = execute(RunRequest(**request.model_dump(), variables=variables), case)
        items.append(BatchItem(case=case, result=result))
    passed = sum(item.result.format_compliant for item in items)
    return BatchResult(
        prompt_id=request.prompt_id,
        passed=passed,
        failed=len(items) - passed,
        results=items,
    )


@router.post("/structured", response_model=StructuredResult)
def structured(request: StructuredRequest) -> StructuredResult:
    try:
        parsed, raw = llm().analyze_candidate(request.candidate_text, request.model)
        return StructuredResult(parsed=parsed, raw_output=raw, valid=True)
    except Exception as exc:
        return StructuredResult(
            parsed=None, raw_output="", valid=False, validation_error=str(exc)
        )


@router.get("/history", response_model=list[RunResult])
def experiment_history(
    limit: int = Query(default=100, ge=1, le=500)
) -> list[RunResult]:
    return history.list(limit)

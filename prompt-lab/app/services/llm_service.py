from __future__ import annotations

import json
from time import perf_counter
from typing import Any

from openai import OpenAI

from app.config import settings
from app.models.schemas import CandidateAnalysis, UsageMetrics


class LLMService:
    def __init__(self, client: OpenAI | None = None) -> None:
        self.client = client or OpenAI(api_key=settings.openai_api_key)

    def run(
        self,
        *,
        prompt: str,
        system_instructions: str,
        model: str,
        temperature: float | None,
        output_format: str,
    ) -> tuple[str, float, UsageMetrics]:
        input_messages: list[dict[str, str]] = []
        if system_instructions:
            input_messages.append({"role": "system", "content": system_instructions})
        input_messages.append({"role": "user", "content": prompt})

        kwargs: dict[str, Any] = {"model": model, "input": input_messages}
        if temperature is not None:
            kwargs["temperature"] = temperature
        if output_format == "json":
            kwargs["text"] = {"format": {"type": "json_object"}}

        started = perf_counter()
        response = self.client.responses.create(**kwargs)
        latency_ms = round((perf_counter() - started) * 1000, 2)
        usage = response.usage
        metrics = UsageMetrics(
            input_tokens=getattr(usage, "input_tokens", 0) or 0,
            output_tokens=getattr(usage, "output_tokens", 0) or 0,
            total_tokens=getattr(usage, "total_tokens", 0) or 0,
        )
        return response.output_text, latency_ms, metrics

    def analyze_candidate(
        self, candidate_text: str, model: str
    ) -> tuple[CandidateAnalysis, str]:
        response = self.client.responses.parse(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": "Extract candidate information accurately.",
                },
                {"role": "user", "content": candidate_text},
            ],
            text_format=CandidateAnalysis,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise ValueError("The model did not return a parsed CandidateAnalysis")
        return parsed, response.output_text or json.dumps(parsed.model_dump())

from __future__ import annotations

import json

from app.models.schemas import DatasetCase


def evaluate_output(
    output: str,
    output_format: str = "text",
    case: DatasetCase | None = None,
) -> tuple[bool, list[str]]:
    notes: list[str] = []
    passed = bool(output.strip())
    if not passed:
        notes.append("Output is empty")

    if output_format == "json" and output:
        try:
            json.loads(output)
        except json.JSONDecodeError:
            passed = False
            notes.append("Output is not valid JSON")

    if case:
        lowered = output.lower()
        missing = [
            word for word in case.expected_keywords if word.lower() not in lowered
        ]
        if missing:
            passed = False
            notes.append(f"Missing expected keywords: {', '.join(missing)}")
        if case.max_words is not None and len(output.split()) > case.max_words:
            passed = False
            notes.append(f"Output exceeds {case.max_words} words")

    if passed:
        notes.append("Basic checks passed")
    return passed, notes

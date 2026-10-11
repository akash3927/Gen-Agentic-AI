from __future__ import annotations

import re
from datetime import datetime, timezone
from string import Formatter
from uuid import uuid4

from app.config import settings
from app.models.schemas import PromptCreate, PromptTemplate
from app.storage.json_store import JsonStore


class PromptService:
    def __init__(self) -> None:
        self.store = JsonStore(settings.prompts_file)

    def list_prompts(self) -> list[PromptTemplate]:
        return [PromptTemplate.model_validate(item) for item in self.store.read_all()]

    def get(self, prompt_id: str) -> PromptTemplate:
        for prompt in self.list_prompts():
            if prompt.prompt_id == prompt_id:
                return prompt
        raise KeyError(f"Prompt '{prompt_id}' was not found")

    def create(self, data: PromptCreate) -> PromptTemplate:
        existing = self.list_prompts()
        versions = [p.version for p in existing if p.prompt_name == data.prompt_name]
        # Keep old versions so experiments can be traced back to the exact prompt used.
        version = max(versions, default=0) + 1
        slug = (
            re.sub(r"[^a-z0-9]+", "_", data.prompt_name.lower()).strip("_") or "prompt"
        )
        prompt = PromptTemplate(
            **data.model_dump(),
            prompt_id=f"{slug}_v{version}_{uuid4().hex[:6]}",
            version=version,
            created_at=datetime.now(timezone.utc),
        )
        self.store.append(prompt.model_dump(mode="json"))
        return prompt

    @staticmethod
    def render(template: str, variables: dict[str, object]) -> str:
        required = {name for _, name, _, _ in Formatter().parse(template) if name}
        # Catch missing inputs before spending an API call on an incomplete prompt.
        missing = sorted(required - variables.keys())
        if missing:
            raise ValueError(f"Missing template variables: {', '.join(missing)}")
        try:
            return template.format(**variables)
        except (KeyError, ValueError, IndexError) as exc:
            raise ValueError(f"Could not render prompt: {exc}") from exc

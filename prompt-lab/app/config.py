from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


class Settings:
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    default_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    prompts_file: Path = BASE_DIR / "prompts" / "prompts.json"
    history_file: Path = BASE_DIR / "storage" / "experiments.json"
    dataset_file: Path = BASE_DIR / "datasets" / "evaluation.json"


settings = Settings()

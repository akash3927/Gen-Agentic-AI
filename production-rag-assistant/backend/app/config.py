from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-5.4-mini"
    chroma_path: Path = Path("data/chroma")
    upload_path: Path = Path("data/uploads")
    registry_path: Path = Path("data/documents.json")
    frontend_origin: str = "http://localhost:5173"
    embedding_batch_size: int = 100
    max_context_characters: int = 16_000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

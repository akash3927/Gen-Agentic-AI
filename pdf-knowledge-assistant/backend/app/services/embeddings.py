from typing import Protocol

from openai import OpenAI


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class OpenAIEmbeddingProvider:
    """Small direct wrapper around the OpenAI Embeddings API."""

    def __init__(self, api_key: str, model: str, batch_size: int = 100) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required to generate embeddings.")
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.batch_size = batch_size

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start : start + self.batch_size]
            response = self.client.embeddings.create(model=self.model, input=batch)
            vectors.extend(item.embedding for item in response.data)
        return vectors

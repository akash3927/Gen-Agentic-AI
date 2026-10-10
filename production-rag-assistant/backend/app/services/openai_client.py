from typing import Protocol

from openai import OpenAI


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class LanguageModel(Protocol):
    def generate(self, instructions: str, prompt: str) -> str: ...


class OpenAIEmbeddingProvider:
    def __init__(self, client: OpenAI, model: str, batch_size: int = 100) -> None:
        self.client = client
        self.model = model
        self.batch_size = batch_size

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            response = self.client.embeddings.create(
                model=self.model,
                input=texts[start : start + self.batch_size],
                encoding_format="float",
            )
            vectors.extend(item.embedding for item in response.data)
        return vectors


class OpenAILanguageModel:
    """Direct Responses API call; no framework hides the generation step."""

    def __init__(self, client: OpenAI, model: str) -> None:
        self.client = client
        self.model = model

    def generate(self, instructions: str, prompt: str) -> str:
        response = self.client.responses.create(
            model=self.model,
            instructions=instructions,
            input=prompt,
            store=False,
        )
        return response.output_text.strip()

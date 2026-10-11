from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_list_seed_prompts() -> None:
    response = client.get("/api/prompts")
    assert response.status_code == 200
    assert len(response.json()) >= 4


def test_run_with_mocked_openai(monkeypatch) -> None:
    class FakeResponses:
        def create(self, **kwargs):
            usage = SimpleNamespace(input_tokens=10, output_tokens=4, total_tokens=14)
            return SimpleNamespace(
                output_text="A short development summary.", usage=usage
            )

    fake_client = SimpleNamespace(responses=FakeResponses())
    monkeypatch.setattr(
        "app.api.routes.LLMService",
        lambda: __import__(
            "app.services.llm_service", fromlist=["LLMService"]
        ).LLMService(fake_client),
    )
    monkeypatch.setattr("app.api.routes.history.add", lambda result: None)
    response = client.post(
        "/api/run",
        json={
            "template": "Summarize: {input}",
            "variables": {"input": "AI changes development."},
            "model": "test-model",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["usage"]["total_tokens"] == 14
    assert body["final_prompt"] == "Summarize: AI changes development."

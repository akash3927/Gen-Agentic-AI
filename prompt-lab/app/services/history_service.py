from app.config import settings
from app.models.schemas import RunResult
from app.storage.json_store import JsonStore


class HistoryService:
    def __init__(self) -> None:
        self.store = JsonStore(settings.history_file)

    def add(self, result: RunResult) -> None:
        self.store.append(result.model_dump(mode="json"))

    def list(self, limit: int = 100) -> list[RunResult]:
        items = self.store.read_all()
        return [RunResult.model_validate(item) for item in reversed(items[-limit:])]

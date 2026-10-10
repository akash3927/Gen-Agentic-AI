import json
from pathlib import Path
from threading import Lock


class DocumentRegistry:
    """Tiny JSON registry for document-level data not duplicated in every vector."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def _read(self) -> dict[str, dict]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, records: dict[str, dict]) -> None:
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(records, indent=2), encoding="utf-8")
        temporary.replace(self.path)

    def list(self) -> list[dict]:
        with self._lock:
            return list(self._read().values())

    def get(self, document_id: str) -> dict | None:
        with self._lock:
            return self._read().get(document_id)

    def put(self, record: dict) -> None:
        with self._lock:
            records = self._read()
            records[record["id"]] = record
            self._write(records)

    def delete(self, document_id: str) -> dict | None:
        with self._lock:
            records = self._read()
            record = records.pop(document_id, None)
            self._write(records)
            return record

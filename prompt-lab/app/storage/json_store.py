from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any


class JsonStore:
    """Tiny JSON-list store suited to a single-process learning app."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]\n", encoding="utf-8")

    def read_all(self) -> list[dict[str, Any]]:
        with self._lock:
            return json.loads(self.path.read_text(encoding="utf-8"))

    def write_all(self, items: list[dict[str, Any]]) -> None:
        with self._lock:
            self.path.write_text(json.dumps(items, indent=2, default=str) + "\n", encoding="utf-8")

    def append(self, item: dict[str, Any]) -> None:
        with self._lock:
            items = json.loads(self.path.read_text(encoding="utf-8"))
            items.append(item)
            self.path.write_text(json.dumps(items, indent=2, default=str) + "\n", encoding="utf-8")

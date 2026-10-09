import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from config import MEMORY_DIR

logger = logging.getLogger("memory.long_term")


class LongTermMemory:
    """Persistent memory backed by a JSON file on disk.

    Stores historical insights, past advisory summaries, and
    accumulated knowledge that should survive across sessions.
    """

    def __init__(self, store_path: Path | None = None):
        self._path = store_path or (MEMORY_DIR / "long_term.json")
        self._data: dict[str, Any] = self._load()

    def _load(self) -> dict:
        if self._path.exists():
            try:
                return json.loads(self._path.read_text())
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Corrupted long-term memory, starting fresh: %s", exc)
        return {"entries": [], "metadata": {"created": datetime.now().isoformat()}}

    def _persist(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data, indent=2, default=str))

    def store(self, category: str, content: Any, tags: list[str] | None = None) -> None:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "content": content,
            "tags": tags or [],
        }
        self._data["entries"].append(entry)
        self._persist()
        logger.info("Stored long-term memory entry [%s] with %d tags", category, len(entry["tags"]))

    def recall(self, category: str | None = None, limit: int = 10) -> list[dict]:
        entries = self._data["entries"]
        if category:
            entries = [e for e in entries if e["category"] == category]
        return entries[-limit:]

    def search(self, keyword: str) -> list[dict]:
        keyword_lower = keyword.lower()
        return [
            e for e in self._data["entries"]
            if keyword_lower in json.dumps(e["content"], default=str).lower()
        ]

    def entry_count(self) -> int:
        return len(self._data["entries"])

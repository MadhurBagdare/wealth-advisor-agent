from collections import OrderedDict
from typing import Any


class ShortTermMemory:
    """In-session scratchpad for passing context between agents.

    Backed by an ordered dict with an optional size cap so that the
    oldest entries are evicted when the session grows large.
    """

    def __init__(self, max_entries: int = 200):
        self._store: OrderedDict[str, Any] = OrderedDict()
        self._max = max_entries

    def set(self, key: str, value: Any) -> None:
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = value
        if len(self._store) > self._max:
            self._store.popitem(last=False)

    def get(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default)

    def has(self, key: str) -> bool:
        return key in self._store

    def keys(self) -> list[str]:
        return list(self._store.keys())

    def clear(self) -> None:
        self._store.clear()

    def snapshot(self) -> dict:
        """Return a shallow copy of the full session state."""
        return dict(self._store)

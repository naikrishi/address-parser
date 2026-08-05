from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class InMemoryRateLimiter:
    limit: int
    window_seconds: int

    def __post_init__(self) -> None:
        self._hits: dict[str, deque[float]] = {}

    def _now(self) -> float:
        return datetime.now(timezone.utc).timestamp()

    def is_allowed(self, key: str) -> bool:
        now = self._now()
        window_start = now - self.window_seconds

        history = self._hits.setdefault(key, deque())
        while history and history[0] <= window_start:
            history.popleft()

        if len(history) >= self.limit:
            return False

        history.append(now)
        return True

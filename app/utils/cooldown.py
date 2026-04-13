"""Per-user cooldowns for ticket/suggestion creation (anti-spam)."""

from threading import Lock
from time import monotonic


class UserCooldown:
    def __init__(self) -> None:
        self._last: dict[int, float] = {}
        self._lock = Lock()

    def is_throttled(self, user_id: int, seconds: float) -> bool:
        if seconds <= 0:
            return False
        now = monotonic()
        with self._lock:
            last = self._last.get(user_id, 0.0)
            return (now - last) < seconds

    def record(self, user_id: int) -> None:
        with self._lock:
            self._last[user_id] = monotonic()

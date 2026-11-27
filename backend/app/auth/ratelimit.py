"""In-memory sliding-window rate limits for login and registration.

Trade-off (documented in CLAUDE.md): counters live in process memory, so they reset on restart
and are not shared between processes. The app runs a single Uvicorn worker, so this is enough
for 0.1.0. Per-IP keys rely on Uvicorn's proxy-header handling (FORWARDED_ALLOW_IPS).
"""

import math
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field

LOGIN_PER_USERNAME = (5, 15 * 60)  # failed attempts, window seconds
LOGIN_PER_IP = (20, 15 * 60)
REGISTER_PER_IP = (5, 60 * 60)  # all attempts

_MAX_KEYS = 10_000  # prune idle keys beyond this many


class SlidingWindowLimiter:
    def __init__(
        self, limit: int, window_seconds: float, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self.limit = limit
        self.window = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> deque[float] | None:
        hits = self._hits.get(key)
        if hits is None:
            return None
        while hits and hits[0] <= now - self.window:
            hits.popleft()
        if not hits:
            del self._hits[key]
            return None
        return hits

    def retry_after(self, key: str) -> int | None:
        """Seconds until another attempt is allowed, or None if allowed now."""
        with self._lock:
            now = self._clock()
            hits = self._prune(key, now)
            if hits is None or len(hits) < self.limit:
                return None
            return max(1, math.ceil(hits[0] + self.window - now))

    def hit(self, key: str) -> None:
        with self._lock:
            now = self._clock()
            hits = self._prune(key, now)
            if hits is None:
                if len(self._hits) >= _MAX_KEYS:
                    for stale in list(self._hits):
                        self._prune(stale, now)
                hits = self._hits[key] = deque()
            hits.append(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._hits.pop(key, None)


@dataclass
class RateLimits:
    login_username: SlidingWindowLimiter = field(
        default_factory=lambda: SlidingWindowLimiter(*LOGIN_PER_USERNAME)
    )
    login_ip: SlidingWindowLimiter = field(
        default_factory=lambda: SlidingWindowLimiter(*LOGIN_PER_IP)
    )
    register_ip: SlidingWindowLimiter = field(
        default_factory=lambda: SlidingWindowLimiter(*REGISTER_PER_IP)
    )

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional, Protocol

from .exceptions import WSXThrottled


@dataclass(slots=True)
class ThrottleDecision:
    allowed: bool
    wait: Optional[float] = None


class ThrottleStore(Protocol):
    def get(self, key: str) -> tuple[float, float] | None: ...
    def set(self, key: str, value: tuple[float, float], ttl_seconds: int) -> None: ...


class MemoryThrottleStore:
    _data: dict[str, tuple[float, float, float]] = {}  # key -> (tokens, last, expires_at)

    def get(self, key: str):
        row = self._data.get(key)
        if not row:
            return None
        tokens, last, exp = row
        if time.time() > exp:
            self._data.pop(key, None)
            return None
        return (tokens, last)

    def set(self, key: str, value: tuple[float, float], ttl_seconds: int):
        tokens, last = value
        self._data[key] = (tokens, last, time.time() + ttl_seconds)


class BaseThrottle:
    rate: str = "60/min"
    store: ThrottleStore = MemoryThrottleStore()

    def parse_rate(self, rate: str) -> tuple[int, int]:
        n, per = rate.split("/")
        n = int(n)
        per = per.lower()
        if per.startswith("sec"):
            return n, 1
        if per.startswith("min"):
            return n, 60
        if per.startswith("hour"):
            return n, 3600
        raise ValueError("Invalid throttle rate")

    def cache_key(self, request) -> str:
        uid = getattr(getattr(request, "user", None), "pk", None) or "anon"
        return f"wsx:{self.__class__.__name__}:{uid}:{request.action}"

    def allow(self, request, view) -> ThrottleDecision:
        raise NotImplementedError


class UserActionThrottle(BaseThrottle):
    rate = "60/min"

    def allow(self, request, view) -> ThrottleDecision:
        num, window = self.parse_rate(self.rate)
        key = self.cache_key(request)

        now = time.time()
        rec = self.store.get(key)
        if rec is None:
            tokens, last = float(num), now
        else:
            tokens, last = rec

        elapsed = max(0.0, now - last)
        refill = (elapsed / window) * num
        tokens = min(float(num), tokens + refill)

        if tokens < 1.0:
            missing = 1.0 - tokens
            wait = (missing / num) * window
            self.store.set(key, (tokens, now), ttl_seconds=window)
            return ThrottleDecision(False, wait)

        tokens -= 1.0
        self.store.set(key, (tokens, now), ttl_seconds=window)
        return ThrottleDecision(True, None)
# wsx/throttles_redis.py
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from django.core.cache import caches

from .throttles import BaseThrottle, ThrottleDecision


@dataclass(slots=True)
class RedisThrottleConfig:
    cache_alias: str = "default"     # set to "throttle" if you want separate cache
    prefix: str = "wsx:throttle"
    clock_skew_seconds: int = 2      # small cushion


class RedisTokenBucketThrottle(BaseThrottle):
    """
    Token bucket stored in Redis via Django cache.

    Stored value: "tokens|last_ts"
    TTL: window seconds
    """

    rate = "60/min"  # override per class or per route
    config = RedisThrottleConfig()

    def __init__(self):
        self.cache = caches[self.config.cache_alias]
        self.num, self.window = self.parse_rate(self.rate)

    def cache_key(self, request) -> str:
        uid = getattr(getattr(request, "user", None), "pk", None) or "anon"
        return f"{self.config.prefix}:{self.__class__.__name__}:{uid}:{request.action}"

    def allow(self, request, view) -> ThrottleDecision:
        key = self.cache_key(request)
        now = time.time()

        raw = self.cache.get(key)  # e.g. "58.2|1700000000.1"
        if raw:
            try:
                tokens_str, last_str = raw.split("|", 1)
                tokens = float(tokens_str)
                last = float(last_str)
            except Exception:
                tokens, last = float(self.num), now
        else:
            tokens, last = float(self.num), now

        elapsed = max(0.0, now - last)
        refill = (elapsed / self.window) * self.num
        tokens = min(float(self.num), tokens + refill)

        if tokens < 1.0:
            missing = 1.0 - tokens
            wait = (missing / self.num) * self.window
            # keep state updated
            ttl = int(self.window + self.config.clock_skew_seconds)
            self.cache.set(key, f"{tokens}|{now}", timeout=ttl)
            return ThrottleDecision(False, wait)

        tokens -= 1.0
        ttl = int(self.window + self.config.clock_skew_seconds)
        self.cache.set(key, f"{tokens}|{now}", timeout=ttl)
        return ThrottleDecision(True, None)
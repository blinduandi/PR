from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Dict


@dataclass
class _Bucket:
    tokens: float
    last_refill: float


class RateLimiter:
    """
    Thread-safe token bucket rate limiter keyed by IP address.

    - rps: refill rate tokens/second
    - burst: bucket capacity
    """

    def __init__(self, rps: float = 5.0, burst: int = 10):
        if rps <= 0:
            raise ValueError("rps must be positive")
        if burst <= 0:
            raise ValueError("burst must be positive")
        self._rps = float(rps)
        self._burst = float(burst)
        self._buckets: Dict[str, _Bucket] = {}
        self._lock = threading.RLock()

    def allow(self, ip: str) -> bool:
        now = time.monotonic()
        with self._lock:
            bucket = self._buckets.get(ip)
            if bucket is None:
                bucket = _Bucket(tokens=self._burst, last_refill=now)
                self._buckets[ip] = bucket
            # Refill tokens based on elapsed time
            elapsed = now - bucket.last_refill
            if elapsed > 0:
                bucket.tokens = min(self._burst, bucket.tokens + elapsed * self._rps)
                bucket.last_refill = now
            if bucket.tokens >= 1.0:
                bucket.tokens -= 1.0
                return True
            return False

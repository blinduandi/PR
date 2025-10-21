from __future__ import annotations

import time
from app.rate_limiter import RateLimiter


def test_token_bucket_allows_rate():
    rl = RateLimiter(rps=5.0, burst=5)
    ip = '1.2.3.4'
    # initially, burst allows immediate tokens
    allowed = sum(1 for _ in range(5) if rl.allow(ip))
    assert allowed == 5
    # next one should be blocked
    assert not rl.allow(ip)
    # wait for 1 second to refill ~5 tokens
    time.sleep(1.05)
    allowed = sum(1 for _ in range(5) if rl.allow(ip))
    assert allowed >= 4  # allow some timing jitter

from __future__ import annotations

import concurrent.futures

from app.counter import NaiveCounter, LockedCounter


def test_locked_counter_thread_safety():
    c = LockedCounter()
    key = "/foo"
    def worker():
        for _ in range(1000):
            c.inc(key)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futures = [ex.submit(worker) for _ in range(8)]
        for f in futures:
            f.result()
    assert c.snapshot()[key] == 8000


def test_naive_counter_race_likely():
    c = NaiveCounter()
    key = "/foo"
    def worker():
        for _ in range(1000):
            c.inc(key)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futures = [ex.submit(worker) for _ in range(8)]
        for f in futures:
            f.result()
    # Race is likely; assert it's not equal to 8000 to demonstrate
    assert c.snapshot().get(key, 0) != 8000

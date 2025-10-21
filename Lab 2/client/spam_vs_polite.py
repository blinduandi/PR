from __future__ import annotations

import argparse
import concurrent.futures
import time
import urllib.request
from typing import Tuple


def fetch(url: str, count: int, label: str) -> Tuple[str, int, int, float]:
    ok = 0
    blocked = 0
    start = time.perf_counter()
    for _ in range(count):
        try:
            with urllib.request.urlopen(url) as resp:
                if resp.status == 200:
                    ok += 1
                elif resp.status == 429:
                    blocked += 1
        except Exception:
            pass
    return label, ok, blocked, time.perf_counter() - start


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("url")
    p.add_argument("--seconds", type=int, default=5)
    p.add_argument("--rate", type=int, default=10, help="Requests per second for spammer")
    args = p.parse_args()

    # spammer: fires as fast as possible ~rate rps per worker
    # polite: sleeps to stay just under 5 rps
    duration = args.seconds
    target_rps = args.rate
    url = args.url

    def spammer():
        end = time.time() + duration
        sent = 0
        ok = 0
        blocked = 0
        while time.time() < end:
            try:
                with urllib.request.urlopen(url) as resp:
                    if resp.status == 200:
                        ok += 1
                    elif resp.status == 429:
                        blocked += 1
            except Exception:
                pass
            sent += 1
            # Short sleep to roughly control rate
            time.sleep(max(0, 1.0 / target_rps))
        return ("spammer", ok, blocked, duration)

    def polite():
        end = time.time() + duration
        ok = 0
        blocked = 0
        while time.time() < end:
            try:
                with urllib.request.urlopen(url) as resp:
                    if resp.status == 200:
                        ok += 1
                    elif resp.status == 429:
                        blocked += 1
            except Exception:
                pass
            time.sleep(0.22)  # ~4.5 rps
        return ("polite", ok, blocked, duration)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        futs = [ex.submit(spammer), ex.submit(polite)]
        for fut in concurrent.futures.as_completed(futs):
            label, ok, blocked, dt = fut.result()
            rps = ok / dt
            print(f"{label}: ok={ok}, 429={blocked}, throughput={rps:.2f} req/s")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

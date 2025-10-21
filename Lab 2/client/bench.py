from __future__ import annotations

import argparse
import concurrent.futures
import time
import urllib.request
from typing import Tuple


def fetch(url: str) -> Tuple[int, float]:
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(url) as resp:
            status = resp.status
            resp.read(64 * 1024)  # read a bit to ensure body consumed
    except Exception:
        status = -1
    return status, time.perf_counter() - start


def run_concurrent(url: str, n: int) -> Tuple[float, list[Tuple[int, float]]]:
    t0 = time.perf_counter()
    results: list[Tuple[int, float]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=n) as ex:
        futs = [ex.submit(fetch, url) for _ in range(n)]
        for fut in concurrent.futures.as_completed(futs):
            results.append(fut.result())
    total = time.perf_counter() - t0
    return total, results


def run_sequential(url: str, n: int) -> Tuple[float, list[Tuple[int, float]]]:
    t0 = time.perf_counter()
    results: list[Tuple[int, float]] = []
    for _ in range(n):
        results.append(fetch(url))
    total = time.perf_counter() - t0
    return total, results


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("url", help="Target URL, e.g. http://localhost:8000/")
    p.add_argument("-n", "--num", type=int, default=10)
    p.add_argument("--mode", choices=["concurrent", "sequential"], default="concurrent")
    args = p.parse_args()

    if args.mode == "concurrent":
        total, results = run_concurrent(args.url, args.num)
    else:
        total, results = run_sequential(args.url, args.num)

    oks = sum(1 for s, _ in results if s == 200)
    too_many = sum(1 for s, _ in results if s == 429)
    print(f"Mode={args.mode}, N={args.num}, total_time={total:.3f}s, ok={oks}, 429={too_many}")
    if results:
        avg = sum(d for _, d in results) / len(results)
        print(f"Average per-request latency: {avg:.3f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

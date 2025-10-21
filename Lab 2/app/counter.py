from __future__ import annotations

import threading
import time
from typing import Dict


class NaiveCounter:
    """
    Intentionally non-thread-safe counter to demonstrate race conditions.
    Adds a small delay between read and write to amplify interleavings.
    """

    def __init__(self) -> None:
        self._counts: Dict[str, int] = {}

    def inc(self, key: str) -> None:
        # read-modify-write without lock
        current = self._counts.get(key, 0)
        # Artificial delay to increase race probability
        time.sleep(0.002)
        self._counts[key] = current + 1

    def snapshot(self) -> Dict[str, int]:
        # Not thread-safe but good enough for listing demonstration
        return dict(self._counts)

    def reset(self) -> None:
        self._counts.clear()


class LockedCounter:
    """Thread-safe counter using a global lock for simplicity."""

    def __init__(self) -> None:
        self._counts: Dict[str, int] = {}
        self._lock = threading.Lock()

    def inc(self, key: str) -> None:
        with self._lock:
            self._counts[key] = self._counts.get(key, 0) + 1

    def snapshot(self) -> Dict[str, int]:
        with self._lock:
            return dict(self._counts)

    def reset(self) -> None:
        with self._lock:
            self._counts.clear()

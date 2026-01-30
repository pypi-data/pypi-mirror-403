"""Timing utilities used by pipeline instrumentation."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncIterator


def monotonic_ms() -> int:
    """Return the current monotonic time in milliseconds."""
    return int(time.perf_counter() * 1000)


class LatencyTracker:
    """Helper for recording elapsed time across async boundaries."""

    __slots__ = ("_start", "_end")

    def __init__(self) -> None:
        self._start = time.perf_counter()
        self._end: float | None = None

    def stop(self) -> int:
        """Freeze the tracker and return the elapsed time in milliseconds."""
        if self._end is None:
            self._end = time.perf_counter()
        return int((self._end - self._start) * 1000)

    @property
    def elapsed_ms(self) -> int:
        """Return the elapsed time since creation or last stop call."""
        end = self._end if self._end is not None else time.perf_counter()
        return int((end - self._start) * 1000)


@asynccontextmanager
async def measure_latency() -> AsyncIterator[LatencyTracker]:
    """Async context manager that measures latency of an operation."""
    tracker = LatencyTracker()
    try:
        yield tracker
    finally:
        tracker.stop()

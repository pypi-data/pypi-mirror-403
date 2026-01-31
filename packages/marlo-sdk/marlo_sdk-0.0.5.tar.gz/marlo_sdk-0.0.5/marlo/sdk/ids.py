"""Thread-safe snowflake ID generator for distributed systems."""

from __future__ import annotations

import os
import threading
import time

_ID_EPOCH_MS = 1700000000000
_WORKER_ID_BITS = 10
_SEQUENCE_BITS = 12
_MAX_WORKER_ID = (1 << _WORKER_ID_BITS) - 1
_MAX_SEQUENCE = (1 << _SEQUENCE_BITS) - 1
_WORKER_ID_SHIFT = _SEQUENCE_BITS
_TIMESTAMP_SHIFT = _SEQUENCE_BITS + _WORKER_ID_BITS


def _parse_worker_id() -> int:
    raw = (os.getenv("MARLO_WORKER_ID") or "0").strip()
    if not raw:
        return 0
    try:
        worker_id = int(raw)
    except ValueError:
        return 0
    if worker_id < 0 or worker_id > _MAX_WORKER_ID:
        return 0
    return worker_id


_WORKER_ID = _parse_worker_id()


class IdGenerator:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._last_ts = 0
        self._sequence = 0

    def next_id(self) -> int:
        with self._lock:
            ts = int(time.time() * 1000)
            if ts < self._last_ts:
                ts = self._wait_until(self._last_ts)
            if ts == self._last_ts:
                self._sequence = (self._sequence + 1) & _MAX_SEQUENCE
                if self._sequence == 0:
                    ts = self._wait_until(self._last_ts + 1)
            else:
                self._sequence = 0
            self._last_ts = ts
            return ((ts - _ID_EPOCH_MS) << _TIMESTAMP_SHIFT) | (_WORKER_ID << _WORKER_ID_SHIFT) | self._sequence

    def _wait_until(self, target_ms: int) -> int:
        ts = int(time.time() * 1000)
        while ts < target_ms:
            time.sleep(0.001)
            ts = int(time.time() * 1000)
        return ts


_ID_GENERATOR = IdGenerator()


def generate_id() -> int:
    """Generate a unique snowflake ID."""
    return _ID_GENERATOR.next_id()


__all__ = ["IdGenerator", "generate_id"]

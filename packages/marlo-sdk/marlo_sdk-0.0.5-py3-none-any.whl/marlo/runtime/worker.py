"""Reward worker loop for processing queued reward jobs."""

from __future__ import annotations

import asyncio
import logging
import os

from marlo.core.config.models import StorageConfig
from marlo.storage.postgres.database import process_reward_jobs

logger = logging.getLogger(__name__)

_DEFAULT_POLL_SECONDS = 5.0
_DEFAULT_BATCH_SIZE = 10


def _parse_positive_int(value: str, *, name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if parsed <= 0:
        raise ValueError(f"{name} must be greater than 0")
    return parsed


def _parse_positive_float(value: str, *, name: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a number") from exc
    if parsed <= 0:
        raise ValueError(f"{name} must be greater than 0")
    return parsed


def _env_or_default_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return _parse_positive_int(raw, name=name)


def _env_or_default_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return _parse_positive_float(raw, name=name)


def load_worker_settings(database_url: str | None = None) -> tuple[StorageConfig, float, int]:
    db_url = database_url or os.getenv("MARLO_DATABASE_URL")
    if not db_url:
        raise RuntimeError("MARLO_DATABASE_URL is required to start the reward worker.")
    poll_seconds = _env_or_default_float("MARLO_REWARD_WORKER_POLL_SECONDS", _DEFAULT_POLL_SECONDS)
    batch_size = _env_or_default_int("MARLO_REWARD_WORKER_BATCH", _DEFAULT_BATCH_SIZE)
    config = StorageConfig(database_url=db_url, apply_schema_on_connect=False)
    return config, poll_seconds, batch_size


async def run_worker(
    config: StorageConfig,
    *,
    poll_seconds: float,
    batch_size: int,
    stop_event: asyncio.Event | None = None,
) -> None:
    poll_seconds = _parse_positive_float(str(poll_seconds), name="poll_seconds")
    batch_size = _parse_positive_int(str(batch_size), name="batch_size")
    while True:
        if stop_event is not None and stop_event.is_set():
            return
        try:
            processed = await process_reward_jobs(config, limit=batch_size)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("Reward worker cycle failed: %s", exc, exc_info=True)
            processed = 0
        if stop_event is not None and stop_event.is_set():
            return
        if processed == 0:
            await asyncio.sleep(poll_seconds)


def run() -> None:
    config, poll_seconds, batch_size = load_worker_settings()
    asyncio.run(run_worker(config, poll_seconds=poll_seconds, batch_size=batch_size))


def main() -> None:
    run()


__all__ = ["load_worker_settings", "run_worker", "run", "main"]

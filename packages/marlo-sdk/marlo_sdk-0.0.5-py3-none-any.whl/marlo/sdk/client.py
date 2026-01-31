"""Marlo SDK client with async-compatible buffered event sending."""

from __future__ import annotations

import logging
import queue
import sys
import threading
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_DEFAULT_BATCH_SIZE = 50
_DEFAULT_FLUSH_INTERVAL = 1.0
_DEFAULT_RETRIES = 3
_DEFAULT_RETRY_BACKOFF = 0.5
_DEFAULT_TIMEOUT = 5.0

_client: MarloClient | None = None
_enabled: bool = False


class BufferedEventSender:
    """Background threaded event sender with batching and retries.

    Uses a separate thread to avoid blocking async event loops.
    All blocking operations happen in the background thread.
    """

    def __init__(
        self,
        *,
        events_url: str,
        api_key: str,
        batch_size: int = _DEFAULT_BATCH_SIZE,
        flush_interval: float = _DEFAULT_FLUSH_INTERVAL,
        max_retries: int = _DEFAULT_RETRIES,
        retry_backoff: float = _DEFAULT_RETRY_BACKOFF,
    ) -> None:
        self._events_url = events_url
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self._batch_size = max(1, int(batch_size))
        self._flush_interval = max(0.1, float(flush_interval))
        self._max_retries = max(1, int(max_retries))
        self._retry_backoff = max(0.1, float(retry_backoff))

        self._queue: queue.Queue[dict[str, Any] | None] = queue.Queue()
        self._shutdown_event = threading.Event()
        self._flush_event = threading.Event()
        self._flush_complete = threading.Event()
        self._flush_lock = threading.Lock()

        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()

    def enqueue(self, events: list[dict[str, Any]]) -> None:
        """Add events to the queue. Non-blocking."""
        if not events:
            return
        for event in events:
            self._queue.put(event)

    def flush(self) -> None:
        """Request a flush and wait for completion. Safe to call from any context."""
        if self._shutdown_event.is_set():
            return
        with self._flush_lock:
            self._flush_complete.clear()
            self._flush_event.set()
            self._flush_complete.wait(timeout=10.0)

    def shutdown(self) -> None:
        """Shutdown the sender, flushing remaining events."""
        self._shutdown_event.set()
        self._flush_event.set()
        self._worker.join(timeout=5.0)

    def _run(self) -> None:
        """Background worker that batches and sends events."""
        pending: list[dict[str, Any]] = []

        while True:
            # Check for shutdown
            if self._shutdown_event.is_set():
                # Drain remaining events
                while True:
                    try:
                        event = self._queue.get_nowait()
                        if event is not None:
                            pending.append(event)
                    except queue.Empty:
                        break
                # Send final batch
                if pending:
                    self._send_with_retry(pending)
                return

            # Check for flush request
            if self._flush_event.is_set():
                self._flush_event.clear()
                # Drain queue
                while True:
                    try:
                        event = self._queue.get_nowait()
                        if event is not None:
                            pending.append(event)
                    except queue.Empty:
                        break
                # Send all pending
                while pending:
                    batch = pending[:self._batch_size]
                    if self._send_with_retry(batch):
                        pending = pending[self._batch_size:]
                    else:
                        break
                self._flush_complete.set()
                continue

            # Normal operation: collect events
            try:
                event = self._queue.get(timeout=self._flush_interval)
                if event is not None:
                    pending.append(event)
                    # Send immediately if we have enough
                    if len(pending) >= self._batch_size:
                        batch = pending[:self._batch_size]
                        if self._send_with_retry(batch):
                            pending = pending[self._batch_size:]
            except queue.Empty:
                # Timeout reached - send whatever we have
                if pending:
                    batch = pending[:self._batch_size]
                    if self._send_with_retry(batch):
                        pending = pending[self._batch_size:]

    def _send_with_retry(self, batch: list[dict[str, Any]]) -> bool:
        """Send batch with retries. Runs in background thread."""
        import time

        for attempt in range(self._max_retries):
            if self._send_batch(batch):
                return True
            if attempt < self._max_retries - 1:
                time.sleep(self._retry_backoff * (2 ** attempt))
        return False

    def _send_batch(self, batch: list[dict[str, Any]]) -> bool:
        """Send a single batch. Runs in background thread."""
        try:
            with httpx.Client(timeout=_DEFAULT_TIMEOUT) as client:
                response = client.post(
                    self._events_url,
                    json=batch,
                    headers=self._headers,
                )
                # Read response body while connection is still open
                if 200 <= response.status_code < 300:
                    return True
                # Log detailed error information
                logger.warning("Event send returned %d", response.status_code)
                error_body = None
                try:
                    error_body = response.text
                    logger.warning("Error response body: %s", error_body[:500])  # First 500 chars
                    # Also print to stdout and stderr for visibility
                    msg = f"🚨 Backend Error ({response.status_code}): {error_body[:200]}"
                    print(msg, file=sys.stderr, flush=True)
                except Exception as e:
                    logger.warning("Could not read error body: %s", e)
                    print(f"⚠️ Failed to read error body: {e}", file=sys.stderr, flush=True)
                return False
        except httpx.TimeoutException:
            logger.warning("Event send timed out")
            return False
        except httpx.ConnectError:
            logger.warning("Event send connection error")
            return False
        except Exception as exc:
            logger.warning("Event send failed: %s", exc)
            return False


class MarloClient:
    def __init__(self, api_key: str, endpoint: str, scope: dict[str, str]) -> None:
        self._api_key = api_key
        self._endpoint = endpoint.rstrip("/")
        self._scope = scope
        self._sender = BufferedEventSender(
            events_url=f"{self._endpoint}/events",
            api_key=api_key,
        )

    @property
    def scope(self) -> dict[str, str]:
        return self._scope

    def send_events(self, events: list[dict]) -> None:
        """Queue events for sending. Non-blocking."""
        self._sender.enqueue(events)

    def flush(self) -> None:
        """Flush pending events. Safe to call from async context."""
        self._sender.flush()

    def shutdown(self) -> None:
        """Shutdown the client."""
        self._sender.shutdown()

    def fetch_learnings(self, learning_key: str) -> dict | None:
        """Fetch learnings synchronously."""
        try:
            with httpx.Client(timeout=_DEFAULT_TIMEOUT) as client:
                response = client.post(
                    f"{self._endpoint}/learnings",
                    json={"learning_key": learning_key},
                    headers={"Authorization": f"Bearer {self._api_key}"},
                )
            if not (200 <= response.status_code < 300):
                return None
            data = response.json()
            return data.get("learning_state")
        except Exception as exc:
            logger.warning("Fetch learnings failed: %s", exc)
            return None

    async def fetch_learnings_async(self, learning_key: str) -> dict | None:
        """Fetch learnings asynchronously."""
        try:
            async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
                response = await client.post(
                    f"{self._endpoint}/learnings",
                    json={"learning_key": learning_key},
                    headers={"Authorization": f"Bearer {self._api_key}"},
                )
            if not (200 <= response.status_code < 300):
                return None
            data = response.json()
            return data.get("learning_state")
        except Exception as exc:
            logger.warning("Fetch learnings failed: %s", exc)
            return None


def _do_init_sync(api_key: str, endpoint: str) -> tuple[dict[str, str] | None, str | None]:
    """Perform synchronous scope fetch. Returns (scope, error_message)."""
    scope_url = f"{endpoint}/scope"
    try:
        with httpx.Client(timeout=_DEFAULT_TIMEOUT) as client:
            response = client.get(
                scope_url,
                headers={"Authorization": f"Bearer {api_key}"},
            )
        if response.status_code != 200:
            return None, f"scope request returned {response.status_code}"
        payload = response.json()
        scope_data = payload.get("scope", {})
        project_id = scope_data.get("project_id")
        org_id = scope_data.get("org_id")
        user_id = scope_data.get("user_id")
        if not all(isinstance(v, str) and v.strip() for v in [project_id, org_id, user_id]):
            return None, "invalid scope response"
        return {
            "project_id": project_id.strip(),
            "org_id": org_id.strip(),
            "user_id": user_id.strip(),
        }, None
    except httpx.TimeoutException:
        return None, "timeout"
    except httpx.ConnectError:
        return None, "connection error"
    except Exception as exc:
        return None, str(exc)


async def _do_init_async(api_key: str, endpoint: str) -> tuple[dict[str, str] | None, str | None]:
    """Perform async scope fetch. Returns (scope, error_message)."""
    scope_url = f"{endpoint}/scope"
    try:
        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
            response = await client.get(
                scope_url,
                headers={"Authorization": f"Bearer {api_key}"},
            )
        if response.status_code != 200:
            return None, f"scope request returned {response.status_code}"
        payload = response.json()
        scope_data = payload.get("scope", {})
        project_id = scope_data.get("project_id")
        org_id = scope_data.get("org_id")
        user_id = scope_data.get("user_id")
        if not all(isinstance(v, str) and v.strip() for v in [project_id, org_id, user_id]):
            return None, "invalid scope response"
        return {
            "project_id": project_id.strip(),
            "org_id": org_id.strip(),
            "user_id": user_id.strip(),
        }, None
    except httpx.TimeoutException:
        return None, "timeout"
    except httpx.ConnectError:
        return None, "connection error"
    except Exception as exc:
        return None, str(exc)


def _finalize_init(api_key: str, endpoint: str, scope: dict[str, str] | None, error: str | None) -> None:
    """Finalize initialization with scope result."""
    global _client, _enabled
    if scope is None:
        logger.warning("Marlo init failed: %s", error or "unknown error")
        _enabled = False
        return
    _client = MarloClient(api_key, endpoint, scope)
    _enabled = True
    logger.info("Marlo SDK initialized for project %s", scope.get("project_id"))


def init(api_key: str, endpoint: str = "https://marlo.marshmallo.ai") -> None:
    """Initialize the Marlo SDK synchronously.

    Note: If called from an async context, use init_async() instead to avoid
    blocking the event loop.
    """
    global _client, _enabled
    endpoint = endpoint.rstrip("/")
    scope, error = _do_init_sync(api_key, endpoint)
    _finalize_init(api_key, endpoint, scope, error)


async def init_async(api_key: str, endpoint: str = "https://marlo.marshmallo.ai") -> None:
    """Initialize the Marlo SDK asynchronously.

    Use this when running in an async context (e.g., LangGraph, FastAPI).
    """
    global _client, _enabled
    endpoint = endpoint.rstrip("/")
    scope, error = await _do_init_async(api_key, endpoint)
    _finalize_init(api_key, endpoint, scope, error)


def init_in_thread(api_key: str, endpoint: str = "https://marlo.marshmallo.ai") -> None:
    """Initialize the Marlo SDK in a background thread.

    Safe to call from async context without blocking the event loop.
    Initialization happens asynchronously in the background.
    """
    import concurrent.futures

    def _init_worker() -> None:
        init(api_key, endpoint)

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    executor.submit(_init_worker)
    executor.shutdown(wait=False)


def get_client() -> MarloClient | None:
    return _client


def is_enabled() -> bool:
    return _enabled


def shutdown() -> None:
    global _client, _enabled
    if _client is not None:
        _client.shutdown()
        _client = None
    _enabled = False


__all__ = ["MarloClient", "get_client", "init", "init_async", "init_in_thread", "is_enabled", "shutdown"]

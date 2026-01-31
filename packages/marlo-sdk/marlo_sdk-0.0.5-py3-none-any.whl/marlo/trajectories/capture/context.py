"""Lightweight execution context for the trace-based runtime."""

from __future__ import annotations

import threading
import contextvars
from typing import Any, Callable, Iterable


_context_var: contextvars.ContextVar["ExecutionContext | None"] = contextvars.ContextVar(
    "marlo_execution_context",
    default=None,
)
_run_id_var: contextvars.ContextVar[int | None] = contextvars.ContextVar("marlo_run_id", default=None)
_agent_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("marlo_agent_id", default=None)
_parent_agent_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("marlo_parent_agent_id", default=None)
_invocation_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("marlo_invocation_id", default=None)


def _require_session_id() -> int:
    session_id = ExecutionContext.get().metadata.get("session_id")
    if session_id is None:
        raise RuntimeError("ExecutionContext.metadata['session_id'] is required for trajectory capture.")
    if isinstance(session_id, bool) or not isinstance(session_id, int):
        raise RuntimeError("ExecutionContext.metadata['session_id'] must be an int.")
    return session_id


def ensure_run_id() -> tuple[int, contextvars.Token | None]:
    run_id = _run_id_var.get()
    if run_id is not None:
        return run_id, None
    run_id = _require_session_id()
    return run_id, _run_id_var.set(run_id)


def reset_run_id(token: contextvars.Token | None) -> None:
    if token is not None:
        try:
            _run_id_var.reset(token)
        except ValueError:
            old_value = getattr(token, "old_value", None)
            if old_value is contextvars.Token.MISSING:
                old_value = None
            _run_id_var.set(old_value)


def get_run_id() -> int:
    return ensure_run_id()[0]


def set_agent_context(
    *,
    agent_id: str,
    parent_agent_id: str | None,
    invocation_id: str,
) -> tuple[contextvars.Token, contextvars.Token, contextvars.Token]:
    return (
        _agent_id_var.set(agent_id),
        _parent_agent_id_var.set(parent_agent_id),
        _invocation_id_var.set(invocation_id),
    )


def reset_agent_context(tokens: tuple[contextvars.Token, contextvars.Token, contextvars.Token]) -> None:
    agent_token, parent_token, invocation_token = tokens
    try:
        _invocation_id_var.reset(invocation_token)
    except ValueError:
        old_value = getattr(invocation_token, "old_value", None)
        if old_value is contextvars.Token.MISSING:
            old_value = None
        _invocation_id_var.set(old_value)
    try:
        _parent_agent_id_var.reset(parent_token)
    except ValueError:
        old_value = getattr(parent_token, "old_value", None)
        if old_value is contextvars.Token.MISSING:
            old_value = None
        _parent_agent_id_var.set(old_value)
    try:
        _agent_id_var.reset(agent_token)
    except ValueError:
        old_value = getattr(agent_token, "old_value", None)
        if old_value is contextvars.Token.MISSING:
            old_value = None
        _agent_id_var.set(old_value)


def get_current_agent_id() -> str | None:
    return _agent_id_var.get()


def require_agent_context() -> tuple[int, str, str | None, str]:
    run_id = get_run_id()
    agent_id = _agent_id_var.get()
    invocation_id = _invocation_id_var.get()
    if agent_id is None or invocation_id is None:
        metadata = ExecutionContext.get().metadata
        if isinstance(metadata, dict):
            if agent_id is None:
                agent_id = metadata.get("agent_id")
            if invocation_id is None:
                invocation_id = metadata.get("invocation_id")
    if agent_id is None or invocation_id is None:
        raise RuntimeError("trace_agent context is required for trajectory capture.")
    parent_agent_id = _parent_agent_id_var.get()
    if parent_agent_id is None:
        metadata = ExecutionContext.get().metadata
        if isinstance(metadata, dict):
            parent_agent_id = metadata.get("parent_agent_id")
    return run_id, agent_id, parent_agent_id, invocation_id


class _Subscription:
    def __init__(self, manager: "EventStream", callback: Callable[[Any], None]) -> None:
        self._manager = manager
        self._callback = callback
        self._unsubscribed = False

    def unsubscribe(self) -> None:
        if not self._unsubscribed:
            self._manager._unsubscribe(self._callback)
            self._unsubscribed = True


class EventStream:
    """Minimal pub/sub stream for emitting trace events."""

    def __init__(self) -> None:
        self._callbacks: list[Callable[[Any], None]] = []
        self._lock = threading.Lock()

    def subscribe(self, callback: Callable[[Any], None]) -> _Subscription:
        with self._lock:
            self._callbacks.append(callback)
        return _Subscription(self, callback)

    def emit(self, event: Any) -> None:
        callbacks: Iterable[Callable[[Any], None]]
        with self._lock:
            callbacks = list(self._callbacks)
        for callback in callbacks:
            try:
                callback(event)
            except Exception:
                # Telemetry should never break execution; swallow errors.
                continue

    def _unsubscribe(self, callback: Callable[[Any], None]) -> None:
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)


class ExecutionContext:
    """Singleton execution context carrying session metadata and telemetry streams."""

    _instance: "ExecutionContext | None" = None

    def __init__(self) -> None:
        self.metadata: dict[str, Any] = {}
        self.event_stream = EventStream()
        # Alias to preserve compatibility with legacy publishers.
        self.intermediate_step_manager = self.event_stream

    @classmethod
    def get(cls) -> "ExecutionContext":
        current = _context_var.get()
        if current is not None:
            return current
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def set_current(cls, context: "ExecutionContext") -> contextvars.Token:
        return _context_var.set(context)

    @classmethod
    def reset_current(cls, token: contextvars.Token) -> None:
        try:
            _context_var.reset(token)
        except ValueError:
            pass

    def emit(self, event: Any) -> None:
        """Emit an event to all subscribers."""
        self.event_stream.emit(event)

    def reset(self) -> None:
        """Clear runtime state between runs."""
        self.metadata = {}
        self.event_stream = EventStream()
        self.intermediate_step_manager = self.event_stream


__all__ = [
    "ExecutionContext",
    "EventStream",
    "ensure_run_id",
    "reset_run_id",
    "get_run_id",
    "set_agent_context",
    "reset_agent_context",
    "get_current_agent_id",
    "require_agent_context",
]

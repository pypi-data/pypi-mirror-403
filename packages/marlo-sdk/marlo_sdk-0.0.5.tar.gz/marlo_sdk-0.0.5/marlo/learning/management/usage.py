"""Runtime usage instrumentation for learning objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from marlo.trajectories.capture.context import ExecutionContext


@dataclass(slots=True)
class _TrackerConfig:
    enabled: bool


class LearningUsageTracker:
    """Lightweight helper that records token usage and failure flags."""

    def __init__(self, context: ExecutionContext) -> None:
        self._context = context
        metadata = context.metadata
        raw_config = metadata.get("learning_usage_config") or {}
        self._config = _TrackerConfig(
            enabled=bool(raw_config.get("enabled", True)),
        )
        usage_store = metadata.setdefault("learning_usage", {})
        usage_store.setdefault("roles", {})
        task_block = usage_store.setdefault("task", {})
        task_block.setdefault("token_usage", {})
        task_block.setdefault("failure_flag", False)
        self._usage_store = usage_store

    @property
    def enabled(self) -> bool:
        return self._config.enabled

    def register_entries(self, role: str, entries: Iterable[Dict[str, Any]]) -> None:
        if not self.enabled:
            return
        role_store = self._usage_store["roles"].setdefault(role, {})
        for entry_payload in entries or []:
            learning_id = entry_payload.get("learning_id")
            if not learning_id:
                continue
            role_store.setdefault(learning_id, {})

    def detect_and_record(
        self,
        role: str,
        text: str,
        *,
        step_id: int | None = None,
        context_hint: str | None = None,
    ) -> List[Dict[str, Any]]:
        return []

    def record_cue_hit(
        self,
        role: str,
        learning_id: str,
        *,
        step_id: int | None,
        snippet: str | None = None,
    ) -> None:
        return

    def record_action_adoption(
        self,
        role: str,
        runtime_handle: str | None,
        *,
        success: bool,
    ) -> None:
        return

    def record_task_outcome(
        self,
        *,
        token_usage: Optional[Dict[str, Any]] = None,
        failure_flag: bool | None = None,
    ) -> None:
        if not self.enabled:
            return
        task_block = self._usage_store["task"]
        if isinstance(token_usage, dict):
            tracked = task_block.setdefault("token_usage", {})
            prompt_tokens = token_usage.get("prompt_tokens")
            completion_tokens = token_usage.get("completion_tokens")
            total_tokens = token_usage.get("total_tokens")
            calls = token_usage.get("calls")
            if prompt_tokens is not None:
                numeric = _as_number(prompt_tokens)
                if numeric is not None:
                    tracked["prompt_tokens"] = numeric
            if completion_tokens is not None:
                numeric = _as_number(completion_tokens)
                if numeric is not None:
                    tracked["completion_tokens"] = numeric
            if total_tokens is not None:
                numeric = _as_number(total_tokens)
                if numeric is not None:
                    tracked["total_tokens"] = numeric
            if calls is not None:
                numeric = _as_number(calls)
                if numeric is not None:
                    tracked["calls"] = numeric
        if failure_flag is not None:
            task_block["failure_flag"] = bool(failure_flag)

    def snapshot(self) -> Dict[str, Any]:
        """Return the current usage store (already JSON-serialisable)."""
        roles: dict[str, Any] = {}
        raw_roles = self._usage_store.get("roles")
        if isinstance(raw_roles, dict):
            for role, entries in raw_roles.items():
                if not isinstance(entries, dict):
                    continue
                role_entries: dict[str, Any] = {}
                for learning_id, entry in entries.items():
                    if not isinstance(entry, dict) or not learning_id:
                        continue
                    role_entries[learning_id] = {}
                if role_entries:
                    roles[str(role)] = role_entries
        task_block = self._usage_store.get("task") if isinstance(self._usage_store.get("task"), dict) else {}
        task_snapshot = {
            "token_usage": dict(task_block.get("token_usage") or {}),
            "failure_flag": bool(task_block.get("failure_flag")),
        }
        return {"roles": roles, "task": task_snapshot}


def get_tracker(context: ExecutionContext | None = None) -> LearningUsageTracker:
    """Helper to fetch the tracker for the active execution context."""

    context = context or ExecutionContext.get()
    return LearningUsageTracker(context)


def _as_number(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


__all__ = ["LearningUsageTracker", "get_tracker"]

"""Shared helpers for the dashboard API."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


DEFAULT_LIMIT = 50


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    if value.endswith("Z"):
        value = f"{value[:-1]}+00:00"
    return datetime.fromisoformat(value)


def _to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


def _coerce_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _reward_score(payload: Any) -> float | None:
    if isinstance(payload, dict):
        return _coerce_float(payload.get("score"))
    return None


def _agent_task_clause(agent_id: str, params: list[Any]) -> str:
    params.append(agent_id)
    agent_idx = len(params)
    return (
        "EXISTS ("
        "SELECT 1 FROM trajectory_events te"
        " WHERE te.session_id = st.session_id"
        " AND (te.event->>'task_id')::bigint = st.id"
        f" AND te.event->>'agent_id' = ${agent_idx}"
        ")"
    )


def _extract_token_total(metadata: Any) -> float | None:
    if not isinstance(metadata, dict):
        return None
    usage = metadata.get("learning_usage")
    if not isinstance(usage, dict):
        return None
    task_block = usage.get("task")
    if not isinstance(task_block, dict):
        return None
    token_usage = task_block.get("token_usage")
    if not isinstance(token_usage, dict):
        return None
    return _coerce_float(token_usage.get("total_tokens"))


def _extract_uncertainty(reward: Any) -> float | None:
    if not isinstance(reward, dict):
        return None
    return _coerce_float(reward.get("uncertainty"))


def _extract_variance_alert(reward_audit: Any) -> bool:
    if not isinstance(reward_audit, list):
        return False
    for entry in reward_audit:
        if not isinstance(entry, dict):
            continue
        if entry.get("escalated") is True:
            return True
    return False

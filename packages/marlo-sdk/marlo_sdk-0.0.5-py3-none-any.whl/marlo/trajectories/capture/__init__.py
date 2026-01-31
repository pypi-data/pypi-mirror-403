"""Trajectory capture utilities (decorators + context propagation)."""

from __future__ import annotations

from marlo.trajectories.capture.decorators import (
    capture_llm_call,
    emit_llm_call,
    emit_log,
    emit_task_end,
    emit_task_start,
    emit_tool_call,
    extract_reasoning,
    extract_usage,
    get_learnings,
    log,
    register_agent_definition,
    trace,
    trace_agent,
    wrap_agent,
)

__all__ = [
    "capture_llm_call",
    "emit_llm_call",
    "emit_log",
    "emit_task_end",
    "emit_task_start",
    "emit_tool_call",
    "extract_reasoning",
    "extract_usage",
    "get_learnings",
    "log",
    "register_agent_definition",
    "trace",
    "trace_agent",
    "wrap_agent",
]

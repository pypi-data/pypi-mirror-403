"""Marlo SDK - simplified agent wrapping and telemetry."""

from __future__ import annotations

from marlo.sdk.client import MarloClient, get_client, init, init_async, init_in_thread, is_enabled, shutdown
from marlo.sdk.context import TaskContext, task
from marlo.sdk.ids import IdGenerator, generate_id
from marlo.sdk.registry import (
    AgentDefinition,
    get_agent,
    mark_agent_sent,
    needs_resend,
    register_agent,
)

__all__ = [
    "init",
    "init_async",
    "init_in_thread",
    "shutdown",
    "register_agent",
    "task",
    "TaskContext",
    "AgentDefinition",
    "MarloClient",
    "get_client",
    "is_enabled",
    "get_agent",
    "mark_agent_sent",
    "needs_resend",
    "IdGenerator",
    "generate_id",
]

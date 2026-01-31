"""Trace event structures for Marlo runtimes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


class TrajectoryEventType(str, Enum):
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    AGENT_DEFINITION = "agent_definition"
    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    LOG = "log"
    TASK_START = "task_start"
    TASK_END = "task_end"


@dataclass
class TrajectoryEvent:
    run_id: int
    agent_id: str
    parent_agent_id: str | None
    invocation_id: str
    event_type: TrajectoryEventType | str
    task_id: int | None = None
    payload: Dict[str, Any] | None = None

    def to_dict(self) -> Dict[str, Any]:
        event_type = self.event_type.value if isinstance(self.event_type, TrajectoryEventType) else str(self.event_type)
        data: Dict[str, Any] = {
            "run_id": self.run_id,
            "agent_id": self.agent_id,
            "parent_agent_id": self.parent_agent_id,
            "invocation_id": self.invocation_id,
            "task_id": self.task_id,
            "event_type": event_type,
            "payload": self.payload,
        }
        return data


__all__ = [
    "TrajectoryEvent",
    "TrajectoryEventType",
]

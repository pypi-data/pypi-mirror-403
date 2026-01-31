"""Agent definition schemas for multi-agent trajectory capture."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict


@dataclass
class AgentDefinition:
    agent_id: str
    parent_agent_id: str | None
    name: str
    system_prompt: str
    tool_definitions: Any
    mcp_definitions: Any
    model_config: Dict[str, Any]
    created_at: datetime | None = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "agent_id": self.agent_id,
            "parent_agent_id": self.parent_agent_id,
            "name": self.name,
            "system_prompt": self.system_prompt,
            "tool_definitions": self.tool_definitions,
            "mcp_definitions": self.mcp_definitions,
            "model_config": self.model_config,
        }
        if self.created_at is not None:
            payload["created_at"] = self.created_at.isoformat()
        return payload


__all__ = ["AgentDefinition"]

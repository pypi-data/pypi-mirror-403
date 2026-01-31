from __future__ import annotations

import logging
from dataclasses import dataclass

from marlo.core.digest import json_digest

logger = logging.getLogger(__name__)


@dataclass
class AgentDefinition:
    name: str
    system_prompt: str
    tools: list[dict]
    mcp: list[dict] | None
    model_config: dict | None
    definition_hash: str
    sent: bool = False


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, AgentDefinition] = {}

    def register(self, definition: AgentDefinition) -> None:
        existing = self._agents.get(definition.name)
        if existing is None:
            self._agents[definition.name] = definition
        elif existing.definition_hash != definition.definition_hash:
            definition.sent = False
            self._agents[definition.name] = definition
            logger.debug(
                "Agent '%s' definition changed, hash updated from %s to %s",
                definition.name,
                existing.definition_hash,
                definition.definition_hash,
            )
        else:
            definition.sent = existing.sent
            self._agents[definition.name] = definition

    def get(self, name: str) -> AgentDefinition | None:
        return self._agents.get(name)

    def mark_sent(self, name: str) -> None:
        agent = self._agents.get(name)
        if agent is not None:
            agent.sent = True

    def needs_resend(self, name: str) -> bool:
        agent = self._agents.get(name)
        return agent is not None and not agent.sent


_registry: AgentRegistry | None = None


def get_registry() -> AgentRegistry:
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry


def register_agent(
    name: str,
    system_prompt: str,
    tools: list[dict],
    mcp: list[dict] | None = None,
    model_config: dict | None = None,
) -> str:
    definition_hash = json_digest(
        {
            "name": name,
            "system_prompt": system_prompt,
            "tool_definitions": tools,
            "mcp_definitions": mcp,
            "model_config": model_config,
        }
    )
    definition = AgentDefinition(
        name=name,
        system_prompt=system_prompt,
        tools=tools,
        mcp=mcp,
        model_config=model_config,
        definition_hash=definition_hash,
    )
    registry = get_registry()
    registry.register(definition)
    return definition_hash


def get_agent(name: str) -> AgentDefinition | None:
    return get_registry().get(name)


def mark_agent_sent(name: str) -> None:
    get_registry().mark_sent(name)


def needs_resend(name: str) -> bool:
    return get_registry().needs_resend(name)


__all__ = [
    "AgentDefinition",
    "register_agent",
    "get_agent",
    "mark_agent_sent",
    "needs_resend",
]

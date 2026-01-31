"""Helpers for upserting agent definitions in Postgres."""

from __future__ import annotations

from typing import Any

import asyncpg

from marlo.core.digest import json_digest


def _serialize_json(value: Any) -> str | None:
    if value is None:
        return None
    try:
        import json

        return json.dumps(value)
    except (TypeError, ValueError):
        return None


async def upsert_agent_definition(
    connection: asyncpg.Connection,
    session_id: int,
    event_payload: dict[str, Any],
) -> None:
    payload = event_payload.get("payload")
    if not isinstance(payload, dict):
        return
    agent_id = payload.get("agent_id") or event_payload.get("agent_id")
    if not isinstance(agent_id, str) or not agent_id:
        return
    parent_agent_id = payload.get("parent_agent_id") or event_payload.get("parent_agent_id")
    invocation_id = payload.get("invocation_id") or event_payload.get("invocation_id")
    name = payload.get("name")
    system_prompt = payload.get("system_prompt")
    tool_definitions = payload.get("tool_definitions")
    mcp_definitions = payload.get("mcp_definitions")
    model_config = payload.get("model_config")
    if not isinstance(name, str) or not name:
        return
    if not isinstance(system_prompt, str) or not system_prompt:
        return
    if tool_definitions is None or model_config is None:
        return
    definition_hash = payload.get("definition_hash")
    if not isinstance(definition_hash, str) or not definition_hash:
        definition_hash = json_digest(
            {
                "name": name,
                "system_prompt": system_prompt,
                "tool_definitions": tool_definitions,
                "mcp_definitions": mcp_definitions,
                "model_config": model_config,
            }
        )
    await connection.execute(
        "INSERT INTO agent_registry("
        "definition_hash, name, system_prompt, tool_definitions, mcp_definitions, model_config"
        ") VALUES ($1, $2, $3, $4, $5, $6)"
        " ON CONFLICT (definition_hash) DO UPDATE SET"
        " name = EXCLUDED.name,"
        " system_prompt = EXCLUDED.system_prompt,"
        " tool_definitions = EXCLUDED.tool_definitions,"
        " mcp_definitions = EXCLUDED.mcp_definitions,"
        " model_config = EXCLUDED.model_config",
        definition_hash,
        name,
        system_prompt,
        _serialize_json(tool_definitions) or "{}",
        _serialize_json(mcp_definitions) if mcp_definitions is not None else None,
        _serialize_json(model_config) or "{}",
    )
    await connection.execute(
        "INSERT INTO session_agents("
        "session_id, agent_id, parent_agent_id, invocation_id, definition_hash"
        ") VALUES ($1, $2, $3, $4, $5)"
        " ON CONFLICT (session_id, agent_id) DO UPDATE SET"
        " parent_agent_id = EXCLUDED.parent_agent_id,"
        " invocation_id = EXCLUDED.invocation_id,"
        " definition_hash = EXCLUDED.definition_hash",
        session_id,
        agent_id,
        parent_agent_id,
        invocation_id,
        definition_hash,
    )

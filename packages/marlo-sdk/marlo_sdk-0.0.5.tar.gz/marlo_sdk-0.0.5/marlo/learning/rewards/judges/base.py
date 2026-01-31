"""Utilities for building reward judge contexts from stored trajectories."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable


def normalize_events(
    rows: list[dict[str, Any]],
    *,
    deserialize: Callable[[Any], Any],
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for row in reversed(rows):
        payload = deserialize(row.get("event"))
        if isinstance(payload, dict):
            event = dict(payload)
        else:
            event = {"payload": payload}
        if "event_id" not in event:
            event["event_id"] = row.get("id")
        if "created_at" not in event:
            created_at = row.get("created_at")
            if hasattr(created_at, "isoformat"):
                event["created_at"] = created_at.isoformat()
            else:
                event["created_at"] = created_at
        events.append(event)
    return events


def resolve_agent_tree(
    agent_ids_ordered: list[str],
    agents_by_id: dict[str, dict[str, Any]],
    events: list[dict[str, Any]],
) -> tuple[str | None, dict[str, str | None], dict[str, list[str]]]:
    if not agent_ids_ordered:
        return None, {}, {}
    if len(agent_ids_ordered) == 1:
        root_id = agent_ids_ordered[0]
        return root_id, {root_id: None}, {}

    root_candidate = _find_first_agent_start(events) or agent_ids_ordered[0]
    parent_map: dict[str, str | None] = {}
    for agent_id in agent_ids_ordered:
        parent_id = agents_by_id.get(agent_id, {}).get("parent_agent_id")
        if isinstance(parent_id, str) and parent_id in agents_by_id:
            parent_map[agent_id] = parent_id
        else:
            parent_map[agent_id] = None

    missing_parent = [agent_id for agent_id, parent_id in parent_map.items() if parent_id is None]
    if missing_parent:
        if root_candidate not in agents_by_id:
            root_candidate = missing_parent[0]
        parent_map[root_candidate] = None
        for agent_id in missing_parent:
            if agent_id != root_candidate:
                parent_map[agent_id] = root_candidate

    roots = [agent_id for agent_id, parent_id in parent_map.items() if parent_id is None]
    if not roots:
        root_id = root_candidate
        parent_map[root_id] = None
    else:
        root_id = root_candidate if root_candidate in roots else roots[0]
        for agent_id in roots:
            if agent_id != root_id:
                parent_map[agent_id] = root_id

    children_map: dict[str, list[str]] = defaultdict(list)
    for agent_id, parent_id in parent_map.items():
        if parent_id:
            children_map[parent_id].append(agent_id)
    return root_id, parent_map, children_map


def filter_events_by_agents(
    events: list[dict[str, Any]],
    agent_ids: set[str],
) -> list[dict[str, Any]]:
    return [event for event in events if event.get("agent_id") in agent_ids]


def collect_subtree_ids(agent_id: str, children_map: dict[str, list[str]]) -> set[str]:
    subtree: set[str] = set()
    stack = [agent_id]
    while stack:
        current = stack.pop()
        if current in subtree:
            continue
        subtree.add(current)
        stack.extend(children_map.get(current, []))
    return subtree


def build_agent_context(agent: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    tool_calls: list[dict[str, Any]] = []
    llm_usage: list[dict[str, Any]] = []

    for event in events:
        event_type = event.get("event_type")
        payload = event.get("payload")
        payload_dict = payload if isinstance(payload, dict) else {}
        if event_type == "tool_call":
            tool_calls.append(
                {
                    "event_id": event.get("event_id"),
                    "tool_name": payload_dict.get("tool_name"),
                    "input": payload_dict.get("input"),
                    "output": payload_dict.get("output"),
                    "error": payload_dict.get("error"),
                }
            )
        elif event_type == "llm_call":
            llm_usage.append(
                {
                    "event_id": event.get("event_id"),
                    "model_params": payload_dict.get("model_params"),
                    "usage": payload_dict.get("usage"),
                    "reasoning": payload_dict.get("reasoning"),
                    "error": payload_dict.get("error"),
                }
            )

    return {
        "agent_id": agent.get("agent_id"),
        "parent_agent_id": agent.get("parent_agent_id"),
        "invocation_id": agent.get("invocation_id"),
        "definition_hash": agent.get("definition_hash"),
        "name": agent.get("name"),
        "system_prompt": agent.get("system_prompt"),
        "tool_definitions": agent.get("tool_definitions"),
        "mcp_definitions": agent.get("mcp_definitions"),
        "model_config": agent.get("model_config"),
        "tool_calls": tool_calls,
        "llm_usage": llm_usage,
    }


def build_session_trajectory_context(
    root_agent_id: str | None,
    events: list[dict[str, Any]],
    agents_by_id: dict[str, dict[str, Any]],
    parent_map: dict[str, str | None],
    children_map: dict[str, list[str]],
) -> dict[str, Any]:
    agent_subtrees: list[dict[str, Any]] = []
    agent_tree = _build_agent_tree(root_agent_id, children_map, agents_by_id)
    known_agent_ids = set(agents_by_id.keys())

    for agent_id, agent in agents_by_id.items():
        if agent_id == root_agent_id:
            continue
        subtree_ids = collect_subtree_ids(agent_id, children_map)
        subtree_events = filter_events_by_agents(events, subtree_ids)
        agent_subtrees.append(
            {
                "agent_id": agent_id,
                "parent_agent_id": parent_map.get(agent_id),
                "definition": _agent_definition_payload(agent),
                "summary": _summarize_events(subtree_events),
            }
        )

    root_events = filter_events_by_agents(events, {root_agent_id}) if root_agent_id else events
    context: dict[str, Any] = {
        "scope": "session",
        "root_agent_id": root_agent_id,
        "agent_tree": agent_tree,
        "root_events": root_events,
        "agent_subtrees": agent_subtrees,
    }
    if known_agent_ids:
        unassigned_events = [event for event in events if event.get("agent_id") not in known_agent_ids]
        if unassigned_events:
            context["unassigned_events"] = unassigned_events
    return context


def build_task_trajectory_context(
    root_agent_id: str | None,
    events: list[dict[str, Any]],
    agents_by_id: dict[str, dict[str, Any]],
    parent_map: dict[str, str | None],
    children_map: dict[str, list[str]],
    *,
    task_id: int | None = None,
    task: str | None = None,
) -> dict[str, Any]:
    context = build_session_trajectory_context(
        root_agent_id,
        events,
        agents_by_id,
        parent_map,
        children_map,
    )
    context["scope"] = "task"
    if task_id is not None:
        context["task_id"] = task_id
    if task is not None:
        context["task"] = task
    return context


def build_agent_trajectory_context(
    agent_id: str,
    subtree_ids: set[str],
    events: list[dict[str, Any]],
    agents_by_id: dict[str, dict[str, Any]],
    parent_map: dict[str, str | None],
    children_map: dict[str, list[str]],
) -> dict[str, Any]:
    subtree_agents = [
        {
            "agent_id": subtree_id,
            "parent_agent_id": parent_map.get(subtree_id),
            "name": agents_by_id.get(subtree_id, {}).get("name"),
            "definition_hash": agents_by_id.get(subtree_id, {}).get("definition_hash"),
        }
        for subtree_id in subtree_ids
    ]
    subtree_tree = _build_agent_tree(agent_id, children_map, agents_by_id)
    return {
        "scope": "agent",
        "agent_id": agent_id,
        "agent_tree": subtree_tree,
        "subtree_agents": subtree_agents,
        "events": events,
    }


def _find_first_agent_start(events: list[dict[str, Any]]) -> str | None:
    for event in events:
        if event.get("event_type") == "agent_start":
            agent_id = event.get("agent_id")
            if isinstance(agent_id, str) and agent_id:
                return agent_id
    return None


def _agent_definition_payload(agent: dict[str, Any]) -> dict[str, Any]:
    return {
        "agent_id": agent.get("agent_id"),
        "parent_agent_id": agent.get("parent_agent_id"),
        "invocation_id": agent.get("invocation_id"),
        "definition_hash": agent.get("definition_hash"),
        "name": agent.get("name"),
        "system_prompt": agent.get("system_prompt"),
        "tool_definitions": agent.get("tool_definitions"),
        "mcp_definitions": agent.get("mcp_definitions"),
        "model_config": agent.get("model_config"),
    }


def _build_agent_tree(
    root_id: str | None,
    children_map: dict[str, list[str]],
    agents_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    if root_id is None:
        return None

    def build(node_id: str) -> dict[str, Any]:
        node: dict[str, Any] = {"agent_id": node_id}
        agent = agents_by_id.get(node_id)
        if agent:
            node["name"] = agent.get("name")
        children = children_map.get(node_id, [])
        if children:
            node["children"] = [build(child_id) for child_id in children]
        return node

    return build(root_id)


def _summarize_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    event_types: dict[str, int] = defaultdict(int)
    tool_counts: dict[str, int] = defaultdict(int)
    tool_errors: dict[str, int] = defaultdict(int)
    llm_counts: dict[str, int] = defaultdict(int)
    errors: list[dict[str, Any]] = []

    for event in events:
        event_type = event.get("event_type")
        if isinstance(event_type, str):
            event_types[event_type] += 1
        payload = event.get("payload")
        payload_dict = payload if isinstance(payload, dict) else {}
        error = payload_dict.get("error") if isinstance(payload_dict, dict) else None
        if error:
            errors.append(
                {
                    "event_id": event.get("event_id"),
                    "event_type": event_type,
                    "error": error,
                }
            )
        if event_type == "tool_call":
            tool_name = payload_dict.get("tool_name")
            if isinstance(tool_name, str):
                tool_counts[tool_name] += 1
                if payload_dict.get("error"):
                    tool_errors[tool_name] += 1
        if event_type == "llm_call":
            model_params = payload_dict.get("model_params")
            model_name = None
            if isinstance(model_params, dict):
                model_name = model_params.get("model") or model_params.get("model_name")
            if isinstance(model_name, str):
                llm_counts[model_name] += 1

    summary: dict[str, Any] = {
        "event_count": len(events),
        "event_types": dict(event_types),
        "tool_calls": [
            {"tool_name": name, "count": count, "errors": tool_errors.get(name, 0)}
            for name, count in tool_counts.items()
        ],
        "llm_calls": [{"model": name, "count": count} for name, count in llm_counts.items()],
    }
    if errors:
        summary["errors"] = errors
    if events:
        summary["first_event_id"] = events[0].get("event_id")
        summary["last_event_id"] = events[-1].get("event_id")
    return summary


__all__ = [
    "build_agent_context",
    "build_agent_trajectory_context",
    "build_session_trajectory_context",
    "build_task_trajectory_context",
    "collect_subtree_ids",
    "filter_events_by_agents",
    "normalize_events",
    "resolve_agent_tree",
]

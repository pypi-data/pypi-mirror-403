"""ID helpers for project and agent identity."""

from __future__ import annotations

import uuid


def require_project_id(existing: str | None) -> str:
    if isinstance(existing, str) and existing.strip():
        return existing.strip()
    raise ValueError("project_id is required")


def agent_id_for_name(project_id: str, agent_name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"marlo:agent:{project_id}:{agent_name.strip()}"))

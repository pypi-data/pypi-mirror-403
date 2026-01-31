"""Agent-facing dashboard routes."""

from __future__ import annotations

from statistics import fmean, pstdev
from typing import Any

import asyncpg
from fastapi import APIRouter, HTTPException, Query, Request

from marlo.api.dashboard.common import (
    DEFAULT_LIMIT,
    _agent_task_clause,
    _extract_token_total,
    _extract_uncertainty,
    _extract_variance_alert,
    _parse_time,
    _reward_score,
    _to_iso,
)

router = APIRouter()


@router.get("/agents")
async def list_agents(
    request: Request,
    project_id: str = Query(...),
    limit: int = Query(DEFAULT_LIMIT, ge=1),
    offset: int = Query(0, ge=0),
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict[str, Any]:
    pool = request.app.state.pool
    params: list[Any] = [project_id]
    clauses: list[str] = ["s.project_id = $1"]
    start_dt = _parse_time(start_time)
    end_dt = _parse_time(end_time)
    if start_dt:
        params.append(start_dt)
        clauses.append(f"sa.created_at >= ${len(params)}")
    if end_dt:
        params.append(end_dt)
        clauses.append(f"sa.created_at <= ${len(params)}")
    where_clause = " AND ".join(clauses)
    params.append(limit)
    limit_idx = len(params)
    params.append(offset)
    offset_idx = len(params)
    query = f"""
        WITH bounds AS (
            SELECT sa.agent_id, MIN(sa.created_at) AS first_seen_at, MAX(sa.created_at) AS last_seen_at
            FROM session_agents sa
            JOIN sessions s ON s.id = sa.session_id
            WHERE {where_clause}
            GROUP BY sa.agent_id
        ),
        latest AS (
            SELECT DISTINCT ON (sa.agent_id) sa.agent_id, sa.definition_hash, sa.created_at
            FROM session_agents sa
            JOIN sessions s ON s.id = sa.session_id
            WHERE {where_clause}
            ORDER BY sa.agent_id, sa.created_at DESC
        )
        SELECT latest.agent_id,
               latest.definition_hash,
               ar.name,
               ar.model_config,
               CASE
                    WHEN jsonb_typeof(ar.tool_definitions) = 'array'
                        THEN jsonb_array_length(ar.tool_definitions)
                    WHEN jsonb_typeof(ar.tool_definitions->'tools') = 'array'
                        THEN jsonb_array_length(ar.tool_definitions->'tools')
                    WHEN jsonb_typeof(ar.tool_definitions->'definitions') = 'array'
                        THEN jsonb_array_length(ar.tool_definitions->'definitions')
                    ELSE 0
               END AS tool_count,
               CASE WHEN jsonb_typeof(ar.mcp_definitions) = 'array'
                    THEN jsonb_array_length(ar.mcp_definitions)
                    ELSE 0
               END AS mcp_count,
               bounds.first_seen_at,
               bounds.last_seen_at,
               latest.created_at
        FROM latest
        LEFT JOIN bounds ON bounds.agent_id = latest.agent_id
        LEFT JOIN agent_registry ar ON ar.definition_hash = latest.definition_hash
        ORDER BY bounds.last_seen_at DESC NULLS LAST, latest.created_at DESC
        LIMIT ${limit_idx} OFFSET ${offset_idx}
    """
    async with pool.acquire() as connection:
        rows = await connection.fetch(query, *params)
    agents = []
    for row in rows:
        agents.append(
            {
                "agent_id": row["agent_id"],
                "project_id": project_id,
                "definition_hash": row["definition_hash"],
                "name": row["name"],
                "model_config": row["model_config"],
                "tool_count": row["tool_count"],
                "mcp_count": row["mcp_count"],
                "first_seen_at": _to_iso(row["first_seen_at"]),
                "last_seen_at": _to_iso(row["last_seen_at"]),
                "created_at": _to_iso(row["first_seen_at"]),
                "updated_at": _to_iso(row["last_seen_at"]),
            }
        )
    return {"agents": agents}


@router.get("/agents/{agent_id}")
async def get_agent(
    agent_id: str,
    request: Request,
    project_id: str = Query(...),
) -> dict[str, Any]:
    pool = request.app.state.pool
    params: list[Any] = [agent_id, project_id]
    query = """
        WITH latest AS (
            SELECT DISTINCT ON (sa.agent_id) sa.agent_id, sa.definition_hash, sa.created_at
            FROM session_agents sa
            JOIN sessions s ON s.id = sa.session_id
            WHERE sa.agent_id = $1 AND s.project_id = $2
            ORDER BY sa.agent_id, sa.created_at DESC
        ),
        bounds AS (
            SELECT sa.agent_id, MIN(sa.created_at) AS first_seen_at, MAX(sa.created_at) AS last_seen_at
            FROM session_agents sa
            JOIN sessions s ON s.id = sa.session_id
            WHERE sa.agent_id = $1 AND s.project_id = $2
            GROUP BY sa.agent_id
        )
        SELECT latest.agent_id,
               latest.definition_hash,
               ar.name,
               ar.system_prompt,
               ar.tool_definitions,
               ar.mcp_definitions,
               ar.model_config,
               bounds.first_seen_at,
               bounds.last_seen_at
        FROM latest
        LEFT JOIN bounds ON bounds.agent_id = latest.agent_id
        LEFT JOIN agent_registry ar ON ar.definition_hash = latest.definition_hash
    """
    async with pool.acquire() as connection:
        row = await connection.fetchrow(query, *params)
    if row is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {
        "agent_id": agent_id,
        "project_id": project_id,
        "definition_hash": row["definition_hash"],
        "name": row["name"],
        "system_prompt": row["system_prompt"],
        "tool_definitions": row["tool_definitions"],
        "mcp_definitions": row["mcp_definitions"],
        "model_config": row["model_config"],
        "created_at": _to_iso(row["first_seen_at"]),
        "updated_at": _to_iso(row["last_seen_at"]),
    }


@router.get("/agents/{agent_id}/tasks")
async def list_agent_tasks(
    agent_id: str,
    request: Request,
    project_id: str = Query(...),
    limit: int = Query(DEFAULT_LIMIT, ge=1),
    offset: int = Query(0, ge=0),
    status: str | None = None,
    session_id: int | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict[str, Any]:
    pool = request.app.state.pool
    params: list[Any] = [project_id]
    clauses = [_agent_task_clause(agent_id, params), f"s.project_id = $1"]
    if status:
        params.append(status)
        clauses.append(f"st.status = ${len(params)}")
    if session_id is not None:
        params.append(session_id)
        clauses.append(f"st.session_id = ${len(params)}")
    start_dt = _parse_time(start_time)
    end_dt = _parse_time(end_time)
    if start_dt:
        params.append(start_dt)
        clauses.append(f"st.created_at >= ${len(params)}")
    if end_dt:
        params.append(end_dt)
        clauses.append(f"st.created_at <= ${len(params)}")
    params.append(limit)
    limit_idx = len(params)
    params.append(offset)
    offset_idx = len(params)
    where_clause = " AND ".join(clauses)
    query = f"""
        SELECT st.id AS task_id,
               st.session_id,
               st.task,
               st.status,
               st.project_id,
               st.reward_stats,
               st.created_at,
               st.completed_at
        FROM session_tasks st
        JOIN sessions s ON s.id = st.session_id
        WHERE {where_clause}
        ORDER BY st.created_at DESC
        LIMIT ${limit_idx} OFFSET ${offset_idx}
    """
    async with pool.acquire() as connection:
        rows = await connection.fetch(query, *params)
    tasks = []
    for row in rows:
        tasks.append(
            {
                "task_id": row["task_id"],
                "session_id": row["session_id"],
                "task": row["task"],
                "status": row["status"],
                "project_id": row["project_id"],
                "reward_score": _reward_score(row["reward_stats"]),
                "created_at": _to_iso(row["created_at"]),
                "completed_at": _to_iso(row["completed_at"]),
            }
        )
    return {"tasks": tasks}


@router.get("/agents/{agent_id}/learnings")
async def list_agent_learnings(
    agent_id: str,
    request: Request,
    project_id: str = Query(...),
    status: str | None = None,
    task_id: int | None = None,
    limit: int = Query(DEFAULT_LIMIT, ge=1),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """
    List learnings for a specific agent.
    
    Note: org_id and user_id are no longer required for read operations.
    The project_id is sufficient to scope the data.
    """
    pool = request.app.state.pool
    params: list[Any] = [agent_id, project_id]
    clauses = ["agent_id = $1", "project_id = $2"]
    if status:
        params.append(status)
        clauses.append(f"status = ${len(params)}")
    if task_id is not None:
        params.append(task_id)
        clauses.append(
            "learning_id IN (SELECT learning_id FROM learning_evidence"
            f" WHERE task_id = ${len(params)} AND project_id = $2)"
        )
    params.append(limit)
    limit_idx = len(params)
    params.append(offset)
    offset_idx = len(params)
    where_clause = " AND ".join(clauses)
    query = f"""
        SELECT learning_id, version, status, learning, expected_outcome, basis,
               confidence, created_at, updated_at
        FROM learning_objects
        WHERE {where_clause}
        ORDER BY updated_at DESC
        LIMIT ${limit_idx} OFFSET ${offset_idx}
    """
    async with pool.acquire() as connection:
        rows = await connection.fetch(query, *params)
    learnings = []
    for row in rows:
        learnings.append(
            {
                "learning_id": row["learning_id"],
                "version": row["version"],
                "status": row["status"],
                "learning": row["learning"],
                "expected_outcome": row["expected_outcome"],
                "basis": row["basis"],
                "confidence": row["confidence"],
                "created_at": _to_iso(row["created_at"]),
                "updated_at": _to_iso(row["updated_at"]),
            }
        )
    return {"agent_id": agent_id, "project_id": project_id, "learnings": learnings}


async def _fetch_agent_task_rows(
    pool: asyncpg.Pool,
    *,
    agent_id: str,
    window: int,
    project_id: str,
) -> list[asyncpg.Record]:
    """
    Fetch task rows for a specific agent.
    
    Note: org_id and user_id are no longer required for read operations.
    The project_id is sufficient to scope the data.
    """
    params: list[Any] = [agent_id, project_id]
    clauses = ["te.event->>'agent_id' = $1", "s.project_id = $2"]
    params.append(window)
    where_clause = " AND ".join(clauses)
    query = f"""
        SELECT st.id AS task_id,
               st.reward_stats,
               st.reward,
               st.reward_audit,
               st.metadata,
               st.created_at,
               ar.model_config
        FROM session_tasks st
        JOIN sessions s ON s.id = st.session_id
        JOIN trajectory_events te
            ON te.session_id = st.session_id
            AND (te.event->>'task_id')::bigint = st.id
        LEFT JOIN LATERAL (
            SELECT ar.model_config
            FROM trajectory_events te2
            JOIN session_agents sa2 ON sa2.session_id = te2.session_id AND sa2.agent_id = te2.event->>'agent_id'
            JOIN agent_registry ar ON ar.definition_hash = sa2.definition_hash
            WHERE te2.session_id = st.session_id
              AND (te2.event->>'task_id')::bigint = st.id
              AND te2.event->>'agent_id' = te.event->>'agent_id'
            ORDER BY te2.created_at ASC
            LIMIT 1
        ) ar ON true
        WHERE {where_clause}
        ORDER BY st.created_at DESC
        LIMIT ${len(params)}
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query, *params)


@router.get("/agents/{agent_id}/metrics/consistency")
async def agent_consistency_metrics(
    agent_id: str,
    request: Request,
    project_id: str = Query(...),
    window: int = Query(DEFAULT_LIMIT, ge=1),
) -> dict[str, Any]:
    """
    Get consistency metrics for a specific agent.
    
    Note: org_id and user_id are no longer required for read operations.
    The project_id is sufficient to scope the data.
    """
    pool = request.app.state.pool
    rows = await _fetch_agent_task_rows(
        pool,
        agent_id=agent_id,
        window=window,
        project_id=project_id,
    )
    scores: list[float] = []
    uncertainties: list[float] = []
    variance_alert = False
    for row in rows:
        score = _reward_score(row["reward_stats"])
        if score is not None:
            scores.append(score)
        uncertainty = _extract_uncertainty(row["reward"])
        if uncertainty is not None:
            uncertainties.append(uncertainty)
        if _extract_variance_alert(row["reward_audit"]):
            variance_alert = True
    reward_mean = fmean(scores) if scores else None
    reward_stddev = pstdev(scores) if len(scores) > 1 else (0.0 if scores else None)
    uncertainty_mean = fmean(uncertainties) if uncertainties else None
    return {
        "agent_id": agent_id,
        "window": window,
        "reward_mean": reward_mean,
        "reward_stddev": reward_stddev,
        "uncertainty_mean": uncertainty_mean,
        "variance_alert": variance_alert,
    }


@router.get("/agents/{agent_id}/metrics/efficiency")
async def agent_efficiency_metrics(
    agent_id: str,
    request: Request,
    project_id: str = Query(...),
    window: int = Query(DEFAULT_LIMIT, ge=1),
) -> dict[str, Any]:
    """
    Get efficiency metrics for a specific agent.
    
    Note: org_id and user_id are no longer required for read operations.
    The project_id is sufficient to scope the data.
    """
    pool = request.app.state.pool
    rows = await _fetch_agent_task_rows(
        pool,
        agent_id=agent_id,
        window=window,
        project_id=project_id,
    )
    scores: list[float] = []
    tokens: list[float] = []
    for row in rows:
        score = _reward_score(row["reward_stats"])
        if score is not None:
            scores.append(score)
        token_total = _extract_token_total(row["metadata"])
        if token_total is not None:
            tokens.append(token_total)
    avg_reward = fmean(scores) if scores else None
    avg_tokens = fmean(tokens) if tokens else None
    reward_per_token = None
    if avg_reward is not None and avg_tokens and avg_tokens != 0:
        reward_per_token = avg_reward / avg_tokens
    return {
        "agent_id": agent_id,
        "window": window,
        "avg_reward": avg_reward,
        "avg_tokens": avg_tokens,
        "reward_per_token": reward_per_token,
    }


@router.get("/agents/{agent_id}/metrics/usage")
async def agent_usage_metrics(
    agent_id: str,
    request: Request,
    project_id: str = Query(...),
    window: int = Query(DEFAULT_LIMIT, ge=1),
) -> dict[str, Any]:
    """
    Get usage metrics for a specific agent.
    
    Note: org_id and user_id are no longer required for read operations.
    The project_id is sufficient to scope the data.
    """
    pool = request.app.state.pool
    task_rows = await _fetch_agent_task_rows(
        pool,
        agent_id=agent_id,
        window=window,
        project_id=project_id,
    )
    task_ids = [row["task_id"] for row in task_rows]
    exposure_events = 0
    exposure_tasks: set[int] = set()
    if task_ids:
        async with pool.acquire() as connection:
            usage_rows = await connection.fetch(
                """
                SELECT lu.task_id
                FROM learning_usage lu
                JOIN learning_objects lo ON lo.learning_id = lu.learning_id
                WHERE lu.task_id = ANY($1)
                  AND lo.agent_id = $2
                  AND lo.project_id = $3
                """,
                task_ids,
                agent_id,
                project_id,
            )
        for row in usage_rows:
            exposure_events += 1
            exposure_tasks.add(row["task_id"])
    return {
        "agent_id": agent_id,
        "window": window,
        "exposure_events": exposure_events,
        "exposure_tasks": len(exposure_tasks),
    }


@router.get("/agents/{agent_id}/metrics/models")
async def agent_model_metrics(
    agent_id: str,
    request: Request,
    project_id: str = Query(...),
    window: int = Query(DEFAULT_LIMIT, ge=1),
) -> dict[str, Any]:
    """
    Get model metrics for a specific agent.
    
    Note: org_id and user_id are no longer required for read operations.
    The project_id is sufficient to scope the data.
    """
    pool = request.app.state.pool
    rows = await _fetch_agent_task_rows(
        pool,
        agent_id=agent_id,
        window=window,
        project_id=project_id,
    )
    model_map: dict[str, dict[str, Any]] = {}
    for row in rows:
        model_id = None
        model_config = row["model_config"]
        if isinstance(model_config, dict):
            model_id = model_config.get("model")
        if not isinstance(model_id, str) or not model_id:
            continue
        entry = model_map.setdefault(
            model_id,
            {
                "role": "agent",
                "model_id": model_id,
                "task_count": 0,
                "scores": [],
                "latest_score": None,
                "last_seen_at": None,
            },
        )
        entry["task_count"] += 1
        score = _reward_score(row["reward_stats"])
        if score is not None:
            entry["scores"].append(score)
            if entry["latest_score"] is None:
                entry["latest_score"] = score
        if entry["last_seen_at"] is None:
            entry["last_seen_at"] = _to_iso(row["created_at"])
    models = []
    for entry in model_map.values():
        scores = entry.pop("scores")
        reward_mean = fmean(scores) if scores else None
        models.append(
            {
                "role": entry["role"],
                "model_id": entry["model_id"],
                "task_count": entry["task_count"],
                "reward_mean": reward_mean,
                "latest_score": entry["latest_score"],
                "last_seen_at": entry["last_seen_at"],
            }
        )
    return {"agent_id": agent_id, "models": models}

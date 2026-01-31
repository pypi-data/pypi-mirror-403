"""Full-text search routes for Marlo dashboard.

This module provides quick full-text search across sessions, tasks, learnings,
and trajectory events. For conversational AI search with persistence, use the
/copilot endpoints instead.
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Query, Request

from marlo.api.dashboard.common import DEFAULT_LIMIT, _parse_time, _reward_score, _to_iso

router = APIRouter()

SearchType = Literal["all", "sessions", "tasks", "learnings", "events"]


@router.get("/search")
async def deep_search(
    request: Request,
    q: str = Query(..., min_length=1, description="Search query"),
    project_id: str = Query(...),
    search_type: SearchType = Query("all", description="Type of content to search"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=100),
    offset: int = Query(0, ge=0),
    start_time: str | None = None,
    end_time: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    """
    Deep search across sessions, tasks, learnings, and trajectory events.

    Uses PostgreSQL full-text search with weighted ranking:
    - Weight A: task descriptions, learning text (highest relevance)
    - Weight B: final answers, expected outcomes
    - Weight C: learning content, basis text
    """
    pool = request.app.state.pool

    # Convert query to tsquery format
    search_terms = " & ".join(q.strip().split())

    results: dict[str, Any] = {"query": q, "results": {}}

    start_dt = _parse_time(start_time)
    end_dt = _parse_time(end_time)

    if search_type in ("all", "sessions"):
        sessions = await _search_sessions(pool, search_terms, project_id, limit, offset, start_dt, end_dt, status)
        results["results"]["sessions"] = sessions

    if search_type in ("all", "tasks"):
        tasks = await _search_tasks(pool, search_terms, project_id, limit, offset, start_dt, end_dt, status)
        results["results"]["tasks"] = tasks

    if search_type in ("all", "learnings"):
        learnings = await _search_learnings(pool, search_terms, project_id, limit, offset)
        results["results"]["learnings"] = learnings

    if search_type in ("all", "events"):
        events = await _search_events(pool, q, project_id, limit, offset, start_dt, end_dt)
        results["results"]["events"] = events

    return results


async def _search_sessions(
    pool: Any,
    search_terms: str,
    project_id: str,
    limit: int,
    offset: int,
    start_dt: Any,
    end_dt: Any,
    status: str | None,
) -> list[dict[str, Any]]:
    """Search sessions using full-text search."""
    params: list[Any] = [search_terms, project_id]
    clauses = ["search_vector @@ to_tsquery('english', $1)", "project_id = $2"]

    if status:
        params.append(status)
        clauses.append(f"status = ${len(params)}")
    if start_dt:
        params.append(start_dt)
        clauses.append(f"created_at >= ${len(params)}")
    if end_dt:
        params.append(end_dt)
        clauses.append(f"created_at <= ${len(params)}")

    params.extend([limit, offset])
    where_clause = " AND ".join(clauses)

    query = f"""
        SELECT id, task, status, final_answer, reward_stats, created_at, completed_at,
               ts_rank(search_vector, to_tsquery('english', $1)) AS rank,
               ts_headline('english', COALESCE(task, '') || ' ' || COALESCE(final_answer, ''),
                          to_tsquery('english', $1), 'MaxWords=50, MinWords=20') AS headline
        FROM sessions
        WHERE {where_clause}
        ORDER BY rank DESC, created_at DESC
        LIMIT ${len(params) - 1} OFFSET ${len(params)}
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    return [
        {
            "id": str(row["id"]),
            "task": row["task"],
            "status": row["status"],
            "headline": row["headline"],
            "rank": float(row["rank"]),
            "reward_score": _reward_score(row["reward_stats"]),
            "created_at": _to_iso(row["created_at"]),
            "completed_at": _to_iso(row["completed_at"]),
        }
        for row in rows
    ]


async def _search_tasks(
    pool: Any,
    search_terms: str,
    project_id: str,
    limit: int,
    offset: int,
    start_dt: Any,
    end_dt: Any,
    status: str | None,
) -> list[dict[str, Any]]:
    """Search tasks using full-text search."""
    params: list[Any] = [search_terms, project_id]
    clauses = ["search_vector @@ to_tsquery('english', $1)", "project_id = $2"]

    if status:
        params.append(status)
        clauses.append(f"status = ${len(params)}")
    if start_dt:
        params.append(start_dt)
        clauses.append(f"created_at >= ${len(params)}")
    if end_dt:
        params.append(end_dt)
        clauses.append(f"created_at <= ${len(params)}")

    params.extend([limit, offset])
    where_clause = " AND ".join(clauses)

    query = f"""
        SELECT id, session_id, task, status, final_answer, reward_stats, created_at, completed_at,
               ts_rank(search_vector, to_tsquery('english', $1)) AS rank,
               ts_headline('english', COALESCE(task, '') || ' ' || COALESCE(final_answer, ''),
                          to_tsquery('english', $1), 'MaxWords=50, MinWords=20') AS headline
        FROM session_tasks
        WHERE {where_clause}
        ORDER BY rank DESC, created_at DESC
        LIMIT ${len(params) - 1} OFFSET ${len(params)}
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    return [
        {
            "id": str(row["id"]),
            "session_id": str(row["session_id"]),
            "task": row["task"],
            "status": row["status"],
            "headline": row["headline"],
            "rank": float(row["rank"]),
            "reward_score": _reward_score(row["reward_stats"]),
            "created_at": _to_iso(row["created_at"]),
            "completed_at": _to_iso(row["completed_at"]),
        }
        for row in rows
    ]


async def _search_learnings(
    pool: Any,
    search_terms: str,
    project_id: str,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    """Search learning objects using full-text search."""
    query = """
        SELECT learning_id, learning_key, status, agent_id, learning, expected_outcome,
               confidence, created_at, updated_at,
               ts_rank(search_vector, to_tsquery('english', $1)) AS rank,
               ts_headline('english', COALESCE(learning, '') || ' ' || COALESCE(expected_outcome, ''),
                          to_tsquery('english', $1), 'MaxWords=50, MinWords=20') AS headline
        FROM learning_objects
        WHERE search_vector @@ to_tsquery('english', $1) AND project_id = $2
        ORDER BY rank DESC, updated_at DESC
        LIMIT $3 OFFSET $4
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, search_terms, project_id, limit, offset)

    return [
        {
            "learning_id": row["learning_id"],
            "learning_key": row["learning_key"],
            "status": row["status"],
            "agent_id": row["agent_id"],
            "learning": row["learning"],
            "headline": row["headline"],
            "rank": float(row["rank"]),
            "confidence": row["confidence"],
            "created_at": _to_iso(row["created_at"]),
            "updated_at": _to_iso(row["updated_at"]),
        }
        for row in rows
    ]


async def _search_events(
    pool: Any,
    query_text: str,
    project_id: str,
    limit: int,
    offset: int,
    start_dt: Any,
    end_dt: Any,
) -> list[dict[str, Any]]:
    """Search trajectory events using JSONB text search on payload."""
    params: list[Any] = [f"%{query_text}%", project_id]
    clauses = ["event::text ILIKE $1", "project_id = $2"]

    if start_dt:
        params.append(start_dt)
        clauses.append(f"created_at >= ${len(params)}")
    if end_dt:
        params.append(end_dt)
        clauses.append(f"created_at <= ${len(params)}")

    params.extend([limit, offset])
    where_clause = " AND ".join(clauses)

    query = f"""
        SELECT id, session_id, event, created_at
        FROM trajectory_events
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT ${len(params) - 1} OFFSET ${len(params)}
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    results = []
    for row in rows:
        event = row["event"] if isinstance(row["event"], dict) else {}
        results.append({
            "id": str(row["id"]),
            "session_id": str(row["session_id"]),
            "event_type": event.get("event_type"),
            "agent_id": event.get("agent_id"),
            "task_id": event.get("task_id"),
            "created_at": _to_iso(row["created_at"]),
        })
    return results



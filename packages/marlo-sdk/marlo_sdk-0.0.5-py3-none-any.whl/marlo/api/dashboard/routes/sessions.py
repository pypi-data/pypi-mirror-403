"""Session-focused dashboard routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from marlo.api.dashboard.common import DEFAULT_LIMIT, _parse_time, _reward_score, _to_iso

router = APIRouter()


@router.get("/sessions")
async def list_sessions(
    request: Request,
    project_id: str = Query(...),
    limit: int = Query(DEFAULT_LIMIT, ge=1),
    offset: int = Query(0, ge=0),
    status: str | None = None,
    agent_id: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict[str, Any]:
    pool = request.app.state.pool
    params: list[Any] = [project_id]
    clauses: list[str] = ["s.project_id = $1"]
    if status:
        params.append(status)
        clauses.append(f"s.status = ${len(params)}")
    if agent_id:
        params.append(agent_id)
        clauses.append(
            f"EXISTS (SELECT 1 FROM session_agents sa2 WHERE sa2.session_id = s.id AND sa2.agent_id = ${len(params)})"
        )
    start_dt = _parse_time(start_time)
    end_dt = _parse_time(end_time)
    if start_dt:
        params.append(start_dt)
        clauses.append(f"s.created_at >= ${len(params)}")
    if end_dt:
        params.append(end_dt)
        clauses.append(f"s.created_at <= ${len(params)}")
    where_clause = f"WHERE {' AND '.join(clauses)}"
    params.append(limit)
    limit_idx = len(params)
    params.append(offset)
    offset_idx = len(params)
    query = f"""
        SELECT s.id AS session_id,
               s.status,
               s.metadata,
               s.created_at,
               s.completed_at,
               s.project_id,
               s.org_id,
               s.user_id,
               sa.agent_id AS agent_id,
               (SELECT COUNT(*) FROM session_tasks st WHERE st.session_id = s.id) AS task_count,
               ft.task AS first_task_text,
               ar.avg_reward
        FROM sessions s
        LEFT JOIN LATERAL (
            SELECT agent_id
            FROM session_agents sa
            WHERE sa.session_id = s.id
            ORDER BY sa.created_at ASC
            LIMIT 1
        ) sa ON true
        LEFT JOIN LATERAL (
            SELECT task
            FROM session_tasks st
            WHERE st.session_id = s.id
            ORDER BY st.created_at ASC
            LIMIT 1
        ) ft ON true
        LEFT JOIN LATERAL (
            SELECT AVG((reward_stats->>'score')::float) AS avg_reward
            FROM session_tasks st
            WHERE st.session_id = s.id AND reward_stats IS NOT NULL AND reward_stats->>'score' IS NOT NULL
        ) ar ON true
        {where_clause}
        ORDER BY s.created_at DESC
        LIMIT ${limit_idx} OFFSET ${offset_idx}
    """
    async with pool.acquire() as connection:
        rows = await connection.fetch(query, *params)
    sessions = []
    for row in rows:
        metadata = row["metadata"] or {}
        thread_name = metadata.get("thread_name") if isinstance(metadata, dict) else None
        sessions.append(
            {
                "session_id": str(row["session_id"]),
                "status": row["status"],
                "agent_id": row["agent_id"],
                "project_id": row["project_id"],
                "org_id": row["org_id"],
                "user_id": row["user_id"],
                "created_at": _to_iso(row["created_at"]),
                "completed_at": _to_iso(row["completed_at"]),
                "task_count": row["task_count"],
                "first_task_text": row["first_task_text"],
                "thread_name": thread_name,
                "avg_reward": float(row["avg_reward"]) if row["avg_reward"] is not None else None,
            }
        )
    return {"sessions": sessions}


@router.get("/sessions/enriched")
async def list_sessions_enriched(
    request: Request,
    project_id: str = Query(...),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: str | None = None,
    agent_id: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict[str, Any]:
    """
    Enriched sessions endpoint that returns sessions with embedded summary statistics.
    Includes avg_reward, task_count, first_task_preview, and has_learnings for each session.
    Eliminates the need for multiple sequential calls to fetch session details.
    """
    pool = request.app.state.pool
    params: list[Any] = [project_id]
    clauses: list[str] = ["s.project_id = $1"]

    if status:
        params.append(status)
        clauses.append(f"s.status = ${len(params)}")
    if agent_id:
        params.append(agent_id)
        clauses.append(
            f"EXISTS (SELECT 1 FROM session_agents sa2 WHERE sa2.session_id = s.id AND sa2.agent_id = ${len(params)})"
        )
    start_dt = _parse_time(start_time)
    end_dt = _parse_time(end_time)
    if start_dt:
        params.append(start_dt)
        clauses.append(f"s.created_at >= ${len(params)}")
    if end_dt:
        params.append(end_dt)
        clauses.append(f"s.created_at <= ${len(params)}")

    where_clause = f"WHERE {' AND '.join(clauses)}"

    # Get total count for pagination
    count_query = f"""
        SELECT COUNT(*) AS total
        FROM sessions s
        {where_clause}
    """

    params.append(limit)
    limit_idx = len(params)
    params.append(offset)
    offset_idx = len(params)

    # Main query with aggregated statistics
    query = f"""
        SELECT s.id AS session_id,
               s.status,
               s.created_at,
               s.completed_at,
               s.project_id,
               s.org_id,
               s.user_id,
               sa.agent_id AS agent_id,
               COALESCE(task_stats.task_count, 0) AS task_count,
               task_stats.avg_reward,
               task_stats.first_task_preview,
               COALESCE(learning_check.has_learnings, false) AS has_learnings
        FROM sessions s
        LEFT JOIN LATERAL (
            SELECT agent_id
            FROM session_agents sa
            WHERE sa.session_id = s.id
            ORDER BY sa.created_at ASC
            LIMIT 1
        ) sa ON true
        LEFT JOIN LATERAL (
            SELECT 
                COUNT(*) AS task_count,
                AVG((st.reward_stats->>'score')::float) FILTER (WHERE st.reward_stats->>'score' IS NOT NULL) AS avg_reward,
                (
                    SELECT LEFT(st2.task, 100)
                    FROM session_tasks st2
                    WHERE st2.session_id = s.id
                    ORDER BY st2.created_at ASC
                    LIMIT 1
                ) AS first_task_preview
            FROM session_tasks st
            WHERE st.session_id = s.id
        ) task_stats ON true
        LEFT JOIN LATERAL (
            SELECT EXISTS (
                SELECT 1
                FROM learning_evidence le
                JOIN session_tasks st ON st.id = le.task_id
                WHERE st.session_id = s.id
                LIMIT 1
            ) AS has_learnings
        ) learning_check ON true
        {where_clause}
        ORDER BY s.created_at DESC
        LIMIT ${limit_idx} OFFSET ${offset_idx}
    """

    async with pool.acquire() as connection:
        # Execute count query (without limit/offset params)
        count_params = params[:-2]  # Exclude limit and offset
        count_row = await connection.fetchrow(count_query, *count_params)
        total = count_row["total"] if count_row else 0

        # Execute main query
        rows = await connection.fetch(query, *params)

    sessions = []
    for row in rows:
        sessions.append(
            {
                "session_id": str(row["session_id"]),
                "status": row["status"],
                "agent_id": row["agent_id"],
                "project_id": row["project_id"],
                "org_id": row["org_id"],
                "user_id": row["user_id"],
                "created_at": _to_iso(row["created_at"]),
                "completed_at": _to_iso(row["completed_at"]),
                "task_count": row["task_count"],
                "avg_reward": float(row["avg_reward"]) if row["avg_reward"] is not None else None,
                "first_task_preview": row["first_task_preview"],
                "has_learnings": row["has_learnings"],
            }
        )

    return {
        "sessions": sessions,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: int,
    request: Request,
    limit: int = Query(DEFAULT_LIMIT, ge=1),
    offset: int = Query(0, ge=0),
    status: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict[str, Any]:
    pool = request.app.state.pool
    async with pool.acquire() as connection:
        session_row = await connection.fetchrow(
            """
            SELECT s.id AS session_id,
                   s.status,
                   s.metadata,
                   s.created_at,
                   s.completed_at,
                   s.project_id,
                   s.org_id,
                   s.user_id,
                   sa.agent_id AS agent_id
            FROM sessions s
            LEFT JOIN LATERAL (
                SELECT agent_id
                FROM session_agents sa
                WHERE sa.session_id = s.id
                ORDER BY sa.created_at ASC
                LIMIT 1
            ) sa ON true
            WHERE s.id = $1
            """,
            session_id,
        )
    if session_row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    params: list[Any] = [session_id]
    clauses = ["session_id = $1"]
    if status:
        params.append(status)
        clauses.append(f"status = ${len(params)}")
    start_dt = _parse_time(start_time)
    end_dt = _parse_time(end_time)
    if start_dt:
        params.append(start_dt)
        clauses.append(f"created_at >= ${len(params)}")
    if end_dt:
        params.append(end_dt)
        clauses.append(f"created_at <= ${len(params)}")
    params.append(limit)
    limit_idx = len(params)
    params.append(offset)
    offset_idx = len(params)
    where_clause = " AND ".join(clauses)
    tasks_query = f"""
        SELECT id AS task_id,
               task,
               status,
               reward_stats,
               created_at,
               completed_at
        FROM session_tasks
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT ${limit_idx} OFFSET ${offset_idx}
    """
    async with pool.acquire() as connection:
        task_rows = await connection.fetch(tasks_query, *params)
    tasks = []
    for row in task_rows:
        tasks.append(
            {
                "task_id": str(row["task_id"]),
                "task": row["task"],
                "status": row["status"],
                "reward_score": _reward_score(row["reward_stats"]),
                "created_at": _to_iso(row["created_at"]),
                "completed_at": _to_iso(row["completed_at"]),
            }
        )
    return {
        "session_id": str(session_row["session_id"]),
        "status": session_row["status"],
        "agent_id": session_row["agent_id"],
        "project_id": session_row["project_id"],
        "org_id": session_row["org_id"],
        "user_id": session_row["user_id"],
        "created_at": _to_iso(session_row["created_at"]),
        "completed_at": _to_iso(session_row["completed_at"]),
        "tasks": tasks,
    }

"""Dashboard statistics routes."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Query, Request

from marlo.api.dashboard.common import _to_iso

router = APIRouter()


@router.get("/stats/tokens/daily")
async def get_daily_token_stats(
    request: Request,
    project_id: str = Query(...),
    days: int = Query(30, ge=1, le=90),
) -> dict[str, Any]:
    """Get daily token usage statistics for efficiency tracking.

    Returns daily breakdown of tokens and task counts for the last N days.
    Used to calculate tokens per task trend (efficiency metric).
    """
    pool = request.app.state.pool

    query = """
        SELECT
            DATE(st.created_at) AS date,
            COALESCE(SUM(
                COALESCE((st.metadata->'learning_usage'->'task'->'token_usage'->>'prompt_tokens')::bigint, 0)
            ), 0) AS input_tokens,
            COALESCE(SUM(
                COALESCE((st.metadata->'learning_usage'->'task'->'token_usage'->>'completion_tokens')::bigint, 0)
            ), 0) AS output_tokens,
            COALESCE(SUM(
                COALESCE(
                    (st.metadata->'learning_usage'->'task'->'token_usage'->>'thinking_tokens')::bigint,
                    (st.metadata->'learning_usage'->'task'->'token_usage'->>'reasoning_tokens')::bigint,
                    0
                )
            ), 0) AS reasoning_tokens,
            COUNT(*) AS task_count
        FROM session_tasks st
        JOIN sessions s ON s.id = st.session_id
        WHERE s.project_id = $1
          AND st.created_at >= NOW() - INTERVAL '1 day' * $2
          AND st.metadata->'learning_usage'->'task'->'token_usage' IS NOT NULL
        GROUP BY DATE(st.created_at)
        ORDER BY date ASC
    """

    async with pool.acquire() as connection:
        rows = await connection.fetch(query, project_id, days)

    daily_stats = []
    for row in rows:
        input_t = int(row["input_tokens"]) if row["input_tokens"] else 0
        output_t = int(row["output_tokens"]) if row["output_tokens"] else 0
        reasoning_t = int(row["reasoning_tokens"]) if row["reasoning_tokens"] else 0
        total = input_t + output_t + reasoning_t
        task_count = int(row["task_count"]) if row["task_count"] else 0

        daily_stats.append({
            "date": row["date"].isoformat(),
            "total_tokens": total,
            "input_tokens": input_t,
            "output_tokens": output_t,
            "reasoning_tokens": reasoning_t,
            "task_count": task_count,
            "tokens_per_task": round(total / task_count, 2) if task_count > 0 else 0,
        })

    return {"daily": daily_stats}


@router.get("/stats/tokens")
async def get_token_stats(
    request: Request,
    project_id: str = Query(...),
) -> dict[str, Any]:
    """Get total token usage statistics for a project.

    Returns aggregated token counts from all tasks in the project.
    Tokens are extracted from task metadata at learning_usage.task.token_usage.
    """
    pool = request.app.state.pool

    query = """
        SELECT
            COALESCE(SUM(
                COALESCE((st.metadata->'learning_usage'->'task'->'token_usage'->>'prompt_tokens')::bigint, 0)
            ), 0) AS input_tokens,
            COALESCE(SUM(
                COALESCE((st.metadata->'learning_usage'->'task'->'token_usage'->>'completion_tokens')::bigint, 0)
            ), 0) AS output_tokens,
            COALESCE(SUM(
                COALESCE(
                    (st.metadata->'learning_usage'->'task'->'token_usage'->>'thinking_tokens')::bigint,
                    (st.metadata->'learning_usage'->'task'->'token_usage'->>'reasoning_tokens')::bigint,
                    0
                )
            ), 0) AS reasoning_tokens,
            COUNT(*) AS task_count
        FROM session_tasks st
        JOIN sessions s ON s.id = st.session_id
        WHERE s.project_id = $1
          AND st.metadata->'learning_usage'->'task'->'token_usage' IS NOT NULL
    """

    async with pool.acquire() as connection:
        row = await connection.fetchrow(query, project_id)

    input_tokens = int(row["input_tokens"]) if row["input_tokens"] else 0
    output_tokens = int(row["output_tokens"]) if row["output_tokens"] else 0
    reasoning_tokens = int(row["reasoning_tokens"]) if row["reasoning_tokens"] else 0
    task_count = int(row["task_count"]) if row["task_count"] else 0

    # Total = input + output + reasoning
    total = input_tokens + output_tokens + reasoning_tokens

    return {
        "total_tokens": total,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,
        "task_count": task_count,
        "avg_tokens_per_task": round(total / task_count, 2) if task_count > 0 else 0,
    }


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    request: Request,
    project_id: str = Query(...),
    days: int = Query(30, ge=1, le=90),
) -> dict[str, Any]:
    """
    Aggregated dashboard summary endpoint that returns all homepage KPIs
    and metrics in a single call. Replaces multiple sequential calls to
    /sessions, /sessions/:id, /tasks/:id/reward, and /tasks/:id/learnings.
    
    Note: org_id and user_id are no longer required for read operations.
    The project_id is sufficient to scope the data.
    
    Returns:
        - kpis: total_sessions, total_tasks, total_tokens, avg_tokens_per_task, 
                avg_reward, avg_reward_change_7d
        - tasks_per_day: daily task counts
        - avg_reward_per_day: daily average rewards
        - tokens_per_day: daily token usage
        - recent_activity: recent tasks and pending learnings
        - pending_learnings_count: count of pending learnings
    """
    pool = request.app.state.pool
    
    async with pool.acquire() as connection:
        # Calculate the date range
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=days)
        seven_days_ago = now - timedelta(days=7)
        
        # Query 1: Get KPIs - total sessions, tasks, and rewards within the time window
        kpi_query = """
            SELECT 
                COUNT(DISTINCT s.id) AS total_sessions,
                COUNT(st.id) AS total_tasks,
                COALESCE(SUM(
                    CASE 
                        WHEN st.metadata IS NOT NULL 
                             AND st.metadata->'learning_usage'->'task'->'token_usage'->>'total_tokens' IS NOT NULL
                        THEN (st.metadata->'learning_usage'->'task'->'token_usage'->>'total_tokens')::float
                        ELSE 0
                    END
                ), 0) AS total_tokens,
                AVG((st.reward_stats->>'score')::float) FILTER (WHERE st.reward_stats->>'score' IS NOT NULL) AS avg_reward
            FROM sessions s
            LEFT JOIN session_tasks st ON st.session_id = s.id
            WHERE s.project_id = $1 AND s.created_at >= $2
        """
        kpi_row = await connection.fetchrow(kpi_query, project_id, start_date)
        
        total_sessions = kpi_row["total_sessions"] if kpi_row else 0
        total_tasks = kpi_row["total_tasks"] if kpi_row else 0
        total_tokens = float(kpi_row["total_tokens"]) if kpi_row and kpi_row["total_tokens"] else 0
        avg_reward = float(kpi_row["avg_reward"]) if kpi_row and kpi_row["avg_reward"] is not None else None
        avg_tokens_per_task = total_tokens / total_tasks if total_tasks > 0 else 0
        
        # Query 2: Get average reward for the last 7 days to calculate change
        recent_reward_query = """
            SELECT AVG((st.reward_stats->>'score')::float) AS avg_reward_recent
            FROM sessions s
            JOIN session_tasks st ON st.session_id = s.id
            WHERE s.project_id = $1 
              AND st.created_at >= $2
              AND st.reward_stats->>'score' IS NOT NULL
        """
        recent_row = await connection.fetchrow(recent_reward_query, project_id, seven_days_ago)
        
        # Calculate reward change (difference between last 7 days and prior 7 days)
        prior_reward_query = """
            SELECT AVG((st.reward_stats->>'score')::float) AS avg_reward_prior
            FROM sessions s
            JOIN session_tasks st ON st.session_id = s.id
            WHERE s.project_id = $1 
              AND st.created_at >= $2
              AND st.created_at < $3
              AND st.reward_stats->>'score' IS NOT NULL
        """
        fourteen_days_ago = now - timedelta(days=14)
        prior_row = await connection.fetchrow(prior_reward_query, project_id, fourteen_days_ago, seven_days_ago)
        
        avg_reward_recent = float(recent_row["avg_reward_recent"]) if recent_row and recent_row["avg_reward_recent"] is not None else None
        avg_reward_prior = float(prior_row["avg_reward_prior"]) if prior_row and prior_row["avg_reward_prior"] is not None else None
        
        avg_reward_change_7d = None
        if avg_reward_recent is not None and avg_reward_prior is not None:
            avg_reward_change_7d = avg_reward_recent - avg_reward_prior
        
        # Query 3: Tasks per day
        tasks_per_day_query = """
            SELECT DATE(st.created_at) AS date, COUNT(*) AS count
            FROM sessions s
            JOIN session_tasks st ON st.session_id = s.id
            WHERE s.project_id = $1 AND st.created_at >= $2
            GROUP BY DATE(st.created_at)
            ORDER BY date ASC
        """
        tasks_per_day_rows = await connection.fetch(tasks_per_day_query, project_id, start_date)
        tasks_per_day = [
            {"date": str(row["date"]), "count": row["count"]}
            for row in tasks_per_day_rows
        ]
        
        # Query 4: Average reward per day
        avg_reward_per_day_query = """
            SELECT DATE(st.created_at) AS date, 
                   AVG((st.reward_stats->>'score')::float) AS avg_reward
            FROM sessions s
            JOIN session_tasks st ON st.session_id = s.id
            WHERE s.project_id = $1 
              AND st.created_at >= $2
              AND st.reward_stats->>'score' IS NOT NULL
            GROUP BY DATE(st.created_at)
            ORDER BY date ASC
        """
        avg_reward_per_day_rows = await connection.fetch(avg_reward_per_day_query, project_id, start_date)
        avg_reward_per_day = [
            {"date": str(row["date"]), "avg_reward": float(row["avg_reward"]) if row["avg_reward"] is not None else None}
            for row in avg_reward_per_day_rows
        ]
        
        # Query 5: Tokens per day
        tokens_per_day_query = """
            SELECT DATE(st.created_at) AS date,
                   COALESCE(SUM(
                       CASE 
                           WHEN st.metadata IS NOT NULL 
                                AND st.metadata->'learning_usage'->'task'->'token_usage'->>'total_tokens' IS NOT NULL
                           THEN (st.metadata->'learning_usage'->'task'->'token_usage'->>'total_tokens')::float
                           ELSE 0
                       END
                   ), 0) AS tokens
            FROM sessions s
            JOIN session_tasks st ON st.session_id = s.id
            WHERE s.project_id = $1 AND st.created_at >= $2
            GROUP BY DATE(st.created_at)
            ORDER BY date ASC
        """
        tokens_per_day_rows = await connection.fetch(tokens_per_day_query, project_id, start_date)
        tokens_per_day = [
            {"date": str(row["date"]), "tokens": float(row["tokens"]) if row["tokens"] else 0}
            for row in tokens_per_day_rows
        ]
        
        # Query 6: Recent tasks (last 10)
        recent_tasks_query = """
            SELECT st.id AS task_id, 
                   (st.reward_stats->>'score')::float AS reward_score,
                   st.created_at
            FROM sessions s
            JOIN session_tasks st ON st.session_id = s.id
            WHERE s.project_id = $1
            ORDER BY st.created_at DESC
            LIMIT 10
        """
        recent_tasks_rows = await connection.fetch(recent_tasks_query, project_id)
        recent_tasks = [
            {
                "task_id": str(row["task_id"]),
                "reward_score": float(row["reward_score"]) if row["reward_score"] is not None else None,
                "created_at": _to_iso(row["created_at"]),
            }
            for row in recent_tasks_rows
        ]
        
        # Query 7: Recent pending learnings (last 10)
        # Note: Now scoped by project_id only, showing all pending learnings for the project
        recent_learnings_query = """
            SELECT learning_id, status, learning, created_at, updated_at
            FROM learning_objects
            WHERE project_id = $1 AND status = 'pending'
            ORDER BY updated_at DESC
            LIMIT 10
        """
        recent_learnings_rows = await connection.fetch(recent_learnings_query, project_id)
        recent_learnings = [
            {
                "learning_id": row["learning_id"],
                "status": row["status"],
                "learning": row["learning"],
                "created_at": _to_iso(row["created_at"]),
                "updated_at": _to_iso(row["updated_at"]),
            }
            for row in recent_learnings_rows
        ]
        
        # Query 8: Pending learnings count
        pending_count_query = """
            SELECT COUNT(*) AS count
            FROM learning_objects
            WHERE project_id = $1 AND status = 'pending'
        """
        pending_count_row = await connection.fetchrow(pending_count_query, project_id)
        pending_learnings_count = pending_count_row["count"] if pending_count_row else 0
    
    return {
        "kpis": {
            "total_sessions": total_sessions,
            "total_tasks": total_tasks,
            "total_tokens": total_tokens,
            "avg_tokens_per_task": avg_tokens_per_task,
            "avg_reward": avg_reward,
            "avg_reward_change_7d": avg_reward_change_7d,
        },
        "tasks_per_day": tasks_per_day,
        "avg_reward_per_day": avg_reward_per_day,
        "tokens_per_day": tokens_per_day,
        "recent_activity": {
            "tasks": recent_tasks,
            "learnings": recent_learnings,
        },
        "pending_learnings_count": pending_learnings_count,
    }

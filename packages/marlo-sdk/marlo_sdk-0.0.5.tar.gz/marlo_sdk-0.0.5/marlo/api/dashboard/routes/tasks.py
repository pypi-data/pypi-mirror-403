"""Task-focused dashboard routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from marlo.api.dashboard.common import DEFAULT_LIMIT, _agent_task_clause, _parse_time, _reward_score, _to_iso

router = APIRouter()


@router.get("/tasks")
async def list_tasks(
    request: Request,
    project_id: str = Query(...),
    limit: int = Query(DEFAULT_LIMIT, ge=1),
    offset: int = Query(0, ge=0),
    status: str | None = None,
    agent_id: str | None = None,
    session_id: int | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict[str, Any]:
    pool = request.app.state.pool
    params: list[Any] = [project_id]
    clauses: list[str] = ["s.project_id = $1"]
    if status:
        params.append(status)
        clauses.append(f"st.status = ${len(params)}")
    if session_id is not None:
        params.append(session_id)
        clauses.append(f"st.session_id = ${len(params)}")
    if agent_id:
        clauses.append(_agent_task_clause(agent_id, params))
    start_dt = _parse_time(start_time)
    end_dt = _parse_time(end_time)
    if start_dt:
        params.append(start_dt)
        clauses.append(f"st.created_at >= ${len(params)}")
    if end_dt:
        params.append(end_dt)
        clauses.append(f"st.created_at <= ${len(params)}")
    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    limit_idx = len(params)
    params.append(offset)
    offset_idx = len(params)
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
        {where_clause}
        ORDER BY st.created_at DESC
        LIMIT ${limit_idx} OFFSET ${offset_idx}
    """
    async with pool.acquire() as connection:
        rows = await connection.fetch(query, *params)
    tasks = []
    for row in rows:
        tasks.append(
            {
                "task_id": str(row["task_id"]),
                "session_id": str(row["session_id"]),
                "task": row["task"],
                "status": row["status"],
                "project_id": row["project_id"],
                "reward_score": _reward_score(row["reward_stats"]),
                "created_at": _to_iso(row["created_at"]),
                "completed_at": _to_iso(row["completed_at"]),
            }
        )
    return {"tasks": tasks}


@router.get("/tasks/{task_id}")
async def get_task(
    task_id: int,
    request: Request,
    project_id: str = Query(...),
) -> dict[str, Any]:
    pool = request.app.state.pool
    query = """
        SELECT id AS task_id,
               session_id,
               task,
               status,
               final_answer,
               reward,
               reward_stats,
               project_id,
               created_at,
               completed_at
        FROM session_tasks
        WHERE id = $1 AND project_id = $2
    """
    async with pool.acquire() as connection:
        row = await connection.fetchrow(query, task_id, project_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": str(row["task_id"]),
        "session_id": str(row["session_id"]),
        "task": row["task"],
        "status": row["status"],
        "final_answer": row["final_answer"],
        "reward": row["reward"],
        "reward_stats": row["reward_stats"],
        "project_id": row["project_id"],
        "created_at": _to_iso(row["created_at"]),
        "completed_at": _to_iso(row["completed_at"]),
    }


@router.get("/tasks/{task_id}/events")
async def list_task_events(
    task_id: int,
    request: Request,
    project_id: str = Query(...),
    limit: int = Query(DEFAULT_LIMIT, ge=1),
    offset: int = Query(0, ge=0),
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict[str, Any]:
    pool = request.app.state.pool
    params: list[Any] = [task_id, project_id]
    clauses = ["(event->>'task_id')::bigint = $1", "project_id = $2"]
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
    query = f"""
        SELECT id, event, created_at
        FROM trajectory_events
        WHERE {where_clause}
        ORDER BY created_at ASC
        LIMIT ${limit_idx} OFFSET ${offset_idx}
    """
    async with pool.acquire() as connection:
        rows = await connection.fetch(query, *params)
    events = []
    for row in rows:
        event = row["event"]
        if isinstance(event, dict):
            payload = dict(event)
        else:
            payload = {"raw": event} if event is not None else {}
        payload["event_id"] = row["id"]
        payload["created_at"] = _to_iso(row["created_at"])
        events.append(payload)
    return {"events": events}


@router.get("/tasks/{task_id}/summary")
async def get_task_summary(
    task_id: int,
    request: Request,
    project_id: str = Query(...),
) -> dict[str, Any]:
    pool = request.app.state.pool
    query = """
        SELECT event
        FROM trajectory_events
        WHERE (event->>'task_id')::bigint = $1 AND project_id = $2
        ORDER BY created_at ASC
    """
    async with pool.acquire() as connection:
        rows = await connection.fetch(query, task_id, project_id)
    event_count = 0
    event_types: dict[str, int] = {}
    tool_calls: dict[str, dict[str, Any]] = {}
    llm_calls: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    seen_errors: set[str] = set()
    for row in rows:
        event = row["event"] or {}
        if not isinstance(event, dict):
            continue
        event_count += 1
        event_type = str(event.get("event_type") or "unknown")
        event_types[event_type] = event_types.get(event_type, 0) + 1
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        error = payload.get("error") if isinstance(payload, dict) else None
        if isinstance(error, str) and error and error not in seen_errors:
            seen_errors.add(error)
            errors.append(error)
        if event_type == "tool_call":
            tool_name = payload.get("tool_name") if isinstance(payload, dict) else None
            if isinstance(tool_name, str) and tool_name:
                entry = tool_calls.setdefault(tool_name, {"tool_name": tool_name, "count": 0, "errors": 0})
                entry["count"] += 1
                if payload.get("error"):
                    entry["errors"] += 1
        if event_type == "llm_call":
            model = None
            if isinstance(payload, dict):
                model_params = payload.get("model_params")
                if isinstance(model_params, dict):
                    model = model_params.get("model")
            if isinstance(model, str) and model:
                entry = llm_calls.setdefault(model, {"model": model, "count": 0})
                entry["count"] += 1
    return {
        "task_id": task_id,
        "event_count": event_count,
        "event_types": event_types,
        "tool_calls": list(tool_calls.values()),
        "llm_calls": list(llm_calls.values()),
        "errors": errors,
    }


@router.get("/tasks/{task_id}/reward")
async def get_task_reward(
    task_id: int,
    request: Request,
    project_id: str = Query(...),
) -> dict[str, Any]:
    pool = request.app.state.pool
    async with pool.acquire() as connection:
        row = await connection.fetchrow(
            "SELECT reward FROM session_tasks WHERE id = $1 AND project_id = $2",
            task_id,
            project_id,
        )
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, "reward": row["reward"]}


@router.get("/tasks/{task_id}/reward_audit")
async def get_task_reward_audit(
    task_id: int,
    request: Request,
    project_id: str = Query(...),
) -> dict[str, Any]:
    pool = request.app.state.pool
    async with pool.acquire() as connection:
        row = await connection.fetchrow(
            "SELECT reward_audit FROM session_tasks WHERE id = $1 AND project_id = $2",
            task_id,
            project_id,
        )
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    audit = row["reward_audit"]
    if audit is None:
        audit = []
    return {"task_id": task_id, "audit": audit}


@router.get("/rewards")
async def list_rewards(
    request: Request,
    project_id: str = Query(...),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    min_score: float | None = Query(None, ge=0.0, le=1.0),
    max_score: float | None = Query(None, ge=0.0, le=1.0),
    agent_id: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict[str, Any]:
    """
    Aggregated rewards endpoint that returns all task rewards for a project
    with embedded task context. Replaces the need for multiple sequential calls
    to /sessions, /sessions/:id, /tasks/:id/reward, and /tasks/:id/reward_audit.
    """
    pool = request.app.state.pool
    params: list[Any] = [project_id]
    clauses: list[str] = ["s.project_id = $1"]

    # Filter by score range using reward_stats->'score'
    if min_score is not None:
        params.append(min_score)
        clauses.append(f"(st.reward_stats->>'score')::float >= ${len(params)}")
    if max_score is not None:
        params.append(max_score)
        clauses.append(f"(st.reward_stats->>'score')::float <= ${len(params)}")

    # Filter by agent_id if provided
    if agent_id:
        clauses.append(_agent_task_clause(agent_id, params))

    # Filter by time range
    start_dt = _parse_time(start_time)
    end_dt = _parse_time(end_time)
    if start_dt:
        params.append(start_dt)
        clauses.append(f"st.created_at >= ${len(params)}")
    if end_dt:
        params.append(end_dt)
        clauses.append(f"st.created_at <= ${len(params)}")

    where_clause = f"WHERE {' AND '.join(clauses)}"

    # Get total count for pagination
    count_query = f"""
        SELECT COUNT(*) AS total
        FROM session_tasks st
        JOIN sessions s ON s.id = st.session_id
        {where_clause}
    """

    params.append(limit)
    limit_idx = len(params)
    params.append(offset)
    offset_idx = len(params)

    # Main query to fetch rewards with task context
    query = f"""
        SELECT st.id AS task_id,
               st.session_id,
               st.task AS task_input,
               st.final_answer AS task_output,
               st.reward,
               st.reward_stats,
               st.reward_audit,
               st.created_at,
               st.completed_at,
               s.org_id,
               s.user_id
        FROM session_tasks st
        JOIN sessions s ON s.id = st.session_id
        {where_clause}
        ORDER BY st.created_at DESC
        LIMIT ${limit_idx} OFFSET ${offset_idx}
    """

    async with pool.acquire() as connection:
        # Execute count query (without limit/offset params)
        count_params = params[:-2]  # Exclude limit and offset
        count_row = await connection.fetchrow(count_query, *count_params)
        total = count_row["total"] if count_row else 0

        # Execute main query
        rows = await connection.fetch(query, *params)

    rewards = []
    for row in rows:
        # Determine if there are edits based on reward_audit
        # Check if any audit entry indicates a manual edit/override
        reward_audit = row["reward_audit"]
        has_edits = False
        if isinstance(reward_audit, list):
            for entry in reward_audit:
                if isinstance(entry, dict):
                    # Check for common edit indicators
                    if entry.get("edited") or entry.get("manual_override") or entry.get("user_modified"):
                        has_edits = True
                        break

        rewards.append(
            {
                "task_id": str(row["task_id"]),
                "session_id": str(row["session_id"]),
                "task_input": row["task_input"],
                "task_output": row["task_output"],
                "created_at": _to_iso(row["created_at"]),
                "completed_at": _to_iso(row["completed_at"]),
                "reward": row["reward"],
                "reward_audit": {"audit": reward_audit if reward_audit else []},
                "has_edits": has_edits,
            }
        )

    return {
        "rewards": rewards,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/tasks/{task_id}/learnings")
async def list_task_learnings(
    task_id: int,
    request: Request,
    project_id: str = Query(...),
    limit: int = Query(DEFAULT_LIMIT, ge=1),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """
    List learnings associated with a specific task.
    
    Note: org_id and user_id are no longer required for read operations.
    The project_id is sufficient to scope the data.
    """
    pool = request.app.state.pool
    query = """
        SELECT lo.learning_id, lo.learning_key, lo.version, lo.status, lo.agent_id, lo.project_id,
               lo.learning, lo.expected_outcome, lo.basis, lo.confidence, lo.created_at, lo.updated_at
        FROM learning_objects lo
        JOIN learning_evidence le ON le.learning_id = lo.learning_id
        WHERE le.task_id = $1 AND le.project_id = $2
          AND lo.project_id = $2
        ORDER BY lo.updated_at DESC
        LIMIT $3 OFFSET $4
    """
    async with pool.acquire() as connection:
        rows = await connection.fetch(query, task_id, project_id, limit, offset)
    learnings = []
    for row in rows:
        learnings.append(
            {
                "learning_id": row["learning_id"],
                "learning_key": row["learning_key"],
                "version": row["version"],
                "status": row["status"],
                "agent_id": row["agent_id"],
                "project_id": row["project_id"],
                "learning": row["learning"],
                "expected_outcome": row["expected_outcome"],
                "basis": row["basis"],
                "confidence": row["confidence"],
                "created_at": _to_iso(row["created_at"]),
                "updated_at": _to_iso(row["updated_at"]),
            }
        )
    return {"task_id": task_id, "learnings": learnings}

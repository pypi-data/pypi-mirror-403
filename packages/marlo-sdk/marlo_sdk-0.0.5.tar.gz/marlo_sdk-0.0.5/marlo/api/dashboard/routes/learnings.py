"""Learning management dashboard routes."""

from __future__ import annotations

from typing import Any

import asyncpg
from fastapi import APIRouter, HTTPException, Query, Request

from marlo.api.dashboard.common import DEFAULT_LIMIT, _to_iso

router = APIRouter()


@router.get("/learnings")
async def list_project_learnings(
    request: Request,
    project_id: str = Query(...),
    status: str | None = None,
    agent_id: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """
    Aggregated learnings endpoint that returns all learnings for a project
    with embedded evidence and counts by status. Replaces the need for multiple
    sequential calls to /sessions, /sessions/:id, and /tasks/:id/learnings.
    
    Note: org_id and user_id are no longer required for read operations.
    The project_id is sufficient to scope the data.
    """
    pool = request.app.state.pool
    params: list[Any] = [project_id]
    clauses: list[str] = ["lo.project_id = $1"]

    # Filter by status if provided
    if status:
        params.append(status)
        clauses.append(f"lo.status = ${len(params)}")

    # Filter by agent_id if provided
    if agent_id:
        params.append(agent_id)
        clauses.append(f"lo.agent_id = ${len(params)}")

    where_clause = f"WHERE {' AND '.join(clauses)}"

    # Get total count and counts by status
    count_query = f"""
        SELECT 
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE lo.status = 'pending') AS pending_count,
            COUNT(*) FILTER (WHERE lo.status = 'active') AS active_count,
            COUNT(*) FILTER (WHERE lo.status = 'declined') AS declined_count,
            COUNT(*) FILTER (WHERE lo.status = 'inactive') AS inactive_count
        FROM learning_objects lo
        {where_clause}
    """

    params.append(limit)
    limit_idx = len(params)
    params.append(offset)
    offset_idx = len(params)

    # Main query to fetch learnings
    query = f"""
        SELECT lo.learning_id,
               lo.learning_key,
               lo.version,
               lo.status,
               lo.agent_id,
               lo.project_id,
               lo.learning,
               lo.expected_outcome,
               lo.basis,
               lo.confidence,
               lo.created_at,
               lo.updated_at
        FROM learning_objects lo
        {where_clause}
        ORDER BY lo.updated_at DESC
        LIMIT ${limit_idx} OFFSET ${offset_idx}
    """

    async with pool.acquire() as connection:
        # Execute count query (without limit/offset params)
        count_params = params[:-2]  # Exclude limit and offset
        count_row = await connection.fetchrow(count_query, *count_params)
        total = count_row["total"] if count_row else 0
        counts = {
            "pending": count_row["pending_count"] if count_row else 0,
            "active": count_row["active_count"] if count_row else 0,
            "declined": count_row["declined_count"] if count_row else 0,
            "inactive": count_row["inactive_count"] if count_row else 0,
        }

        # Execute main query
        rows = await connection.fetch(query, *params)

        # Fetch evidence for all learnings in a single query
        learning_ids = [row["learning_id"] for row in rows]
        evidence_map: dict[str, dict[str, Any]] = {}
        if learning_ids:
            evidence_rows = await connection.fetch(
                """
                SELECT learning_id, task_id, rationale_snippet
                FROM learning_evidence
                WHERE learning_id = ANY($1) AND project_id = $2
                ORDER BY created_at DESC
                """,
                learning_ids,
                project_id,
            )
            for ev_row in evidence_rows:
                lid = ev_row["learning_id"]
                if lid not in evidence_map:
                    evidence_map[lid] = {"task_ids": [], "rationale_snippets": []}
                task_id = ev_row["task_id"]
                snippet = ev_row["rationale_snippet"]
                if task_id is not None and task_id not in evidence_map[lid]["task_ids"]:
                    evidence_map[lid]["task_ids"].append(task_id)
                if isinstance(snippet, str) and snippet and snippet not in evidence_map[lid]["rationale_snippets"]:
                    evidence_map[lid]["rationale_snippets"].append(snippet)

    learnings = []
    for row in rows:
        learning_id = row["learning_id"]
        learnings.append(
            {
                "learning_id": learning_id,
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
                "evidence": evidence_map.get(learning_id, {"task_ids": [], "rationale_snippets": []}),
            }
        )

    return {
        "learnings": learnings,
        "total": total,
        "counts": counts,
        "limit": limit,
        "offset": offset,
    }


@router.get("/learnings/{learning_id}")
async def get_learning(
    learning_id: str,
    request: Request,
    project_id: str = Query(...),
) -> dict[str, Any]:
    """
    Get details for a specific learning.
    
    Note: org_id and user_id are no longer required for read operations.
    The project_id is sufficient to scope the data.
    """
    pool = request.app.state.pool
    async with pool.acquire() as connection:
        row = await connection.fetchrow(
            """
            SELECT learning_id, learning_key, version, status, agent_id, project_id,
                   learning, expected_outcome, basis, confidence, created_at, updated_at
            FROM learning_objects
            WHERE learning_id = $1 AND project_id = $2
            """,
            learning_id,
            project_id,
        )
        evidence_rows = await connection.fetch(
            """
            SELECT task_id, rationale_snippet
            FROM learning_evidence
            WHERE learning_id = $1 AND project_id = $2
            ORDER BY created_at DESC
            """,
            learning_id,
            project_id,
        )
    if row is None:
        raise HTTPException(status_code=404, detail="Learning not found")
    task_ids: list[int] = []
    rationale_snippets: list[str] = []
    for evidence in evidence_rows:
        task_id = evidence["task_id"]
        snippet = evidence["rationale_snippet"]
        if task_id is not None and task_id not in task_ids:
            task_ids.append(task_id)
        if isinstance(snippet, str) and snippet and snippet not in rationale_snippets:
            rationale_snippets.append(snippet)
    return {
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
        "evidence": {"task_ids": task_ids, "rationale_snippets": rationale_snippets},
    }


async def _require_learning_scope(
    connection: asyncpg.Connection,
    *,
    learning_id: str,
    project_id: str,
    org_id: str,
    user_id: str,
) -> None:
    row = await connection.fetchrow(
        """
        SELECT learning_id
        FROM learning_objects
        WHERE learning_id = $1 AND project_id = $2 AND org_id = $3
        """,
        learning_id,
        project_id,
        org_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Learning not found")


async def _insert_learning_review(
    connection: asyncpg.Connection,
    *,
    learning_id: str,
    project_id: str,
    org_id: str,
    user_id: str,
    decision: str,
    reason: str | None = None,
    edited_learning: str | None = None,
    edited_expected_outcome: str | None = None,
    edited_basis: str | None = None,
) -> None:
    await connection.execute(
        """
        INSERT INTO learning_reviews(
            learning_id, project_id, org_id, user_id, decision, reason,
            edited_learning, edited_expected_outcome, edited_basis
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """,
        learning_id,
        project_id,
        org_id,
        user_id,
        decision,
        reason,
        edited_learning,
        edited_expected_outcome,
        edited_basis,
    )


async def _update_learning_status(
    connection: asyncpg.Connection,
    *,
    learning_id: str,
    project_id: str,
    org_id: str,
    user_id: str,
    status: str,
) -> None:
    await connection.execute(
        """
        UPDATE learning_objects
        SET status = $1, updated_at = NOW()
        WHERE learning_id = $2 AND project_id = $3 AND org_id = $4
        """,
        status,
        learning_id,
        project_id,
        org_id,
    )


@router.post("/learnings/{learning_id}/approve")
async def approve_learning(
    learning_id: str,
    request: Request,
    project_id: str = Query(...),
    org_id: str = Query(...),
    user_id: str = Query(...),
) -> dict[str, Any]:
    pool = request.app.state.pool
    async with pool.acquire() as connection:
        async with connection.transaction():
            await _require_learning_scope(
                connection,
                learning_id=learning_id,
                project_id=project_id,
                org_id=org_id,
                user_id=user_id,
            )
            await _update_learning_status(
                connection,
                learning_id=learning_id,
                project_id=project_id,
                org_id=org_id,
                user_id=user_id,
                status="active",
            )
            await _insert_learning_review(
                connection,
                learning_id=learning_id,
                project_id=project_id,
                org_id=org_id,
                user_id=user_id,
                decision="approved",
            )
    return {"learning_id": learning_id, "status": "active"}


@router.post("/learnings/{learning_id}/decline")
async def decline_learning(
    learning_id: str,
    request: Request,
    project_id: str = Query(...),
    org_id: str = Query(...),
    user_id: str = Query(...),
) -> dict[str, Any]:
    pool = request.app.state.pool
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    reason = payload.get("reason") if isinstance(payload, dict) else None
    async with pool.acquire() as connection:
        async with connection.transaction():
            await _require_learning_scope(
                connection,
                learning_id=learning_id,
                project_id=project_id,
                org_id=org_id,
                user_id=user_id,
            )
            await _update_learning_status(
                connection,
                learning_id=learning_id,
                project_id=project_id,
                org_id=org_id,
                user_id=user_id,
                status="declined",
            )
            await _insert_learning_review(
                connection,
                learning_id=learning_id,
                project_id=project_id,
                org_id=org_id,
                user_id=user_id,
                decision="declined",
                reason=reason if isinstance(reason, str) and reason.strip() else None,
            )
    return {"learning_id": learning_id, "status": "declined"}


@router.post("/learnings/{learning_id}/deactivate")
async def deactivate_learning(
    learning_id: str,
    request: Request,
    project_id: str = Query(...),
    org_id: str = Query(...),
    user_id: str = Query(...),
) -> dict[str, Any]:
    pool = request.app.state.pool
    async with pool.acquire() as connection:
        async with connection.transaction():
            await _require_learning_scope(
                connection,
                learning_id=learning_id,
                project_id=project_id,
                org_id=org_id,
                user_id=user_id,
            )
            await _update_learning_status(
                connection,
                learning_id=learning_id,
                project_id=project_id,
                org_id=org_id,
                user_id=user_id,
                status="inactive",
            )
            await _insert_learning_review(
                connection,
                learning_id=learning_id,
                project_id=project_id,
                org_id=org_id,
                user_id=user_id,
                decision="deactivated",
            )
    return {"learning_id": learning_id, "status": "inactive"}


@router.post("/learnings/{learning_id}/activate")
async def activate_learning(
    learning_id: str,
    request: Request,
    project_id: str = Query(...),
    org_id: str = Query(...),
    user_id: str = Query(...),
) -> dict[str, Any]:
    pool = request.app.state.pool
    async with pool.acquire() as connection:
        async with connection.transaction():
            await _require_learning_scope(
                connection,
                learning_id=learning_id,
                project_id=project_id,
                org_id=org_id,
                user_id=user_id,
            )
            await _update_learning_status(
                connection,
                learning_id=learning_id,
                project_id=project_id,
                org_id=org_id,
                user_id=user_id,
                status="active",
            )
            await _insert_learning_review(
                connection,
                learning_id=learning_id,
                project_id=project_id,
                org_id=org_id,
                user_id=user_id,
                decision="reactivated",
            )
    return {"learning_id": learning_id, "status": "active"}


@router.patch("/learnings/{learning_id}")
async def edit_learning(
    learning_id: str,
    request: Request,
    project_id: str = Query(...),
    org_id: str = Query(...),
    user_id: str = Query(...),
) -> dict[str, Any]:
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid payload")
    learning = payload.get("learning")
    expected_outcome = payload.get("expected_outcome")
    basis = payload.get("basis")
    if not isinstance(learning, str) or not learning.strip():
        raise HTTPException(status_code=400, detail="learning is required")
    if not isinstance(expected_outcome, str) or not expected_outcome.strip():
        raise HTTPException(status_code=400, detail="expected_outcome is required")
    if not isinstance(basis, str) or not basis.strip():
        raise HTTPException(status_code=400, detail="basis is required")
    pool = request.app.state.pool
    async with pool.acquire() as connection:
        async with connection.transaction():
            await _require_learning_scope(
                connection,
                learning_id=learning_id,
                project_id=project_id,
                org_id=org_id,
                user_id=user_id,
            )
            await connection.execute(
                """
                UPDATE learning_objects
                SET learning = $1,
                    expected_outcome = $2,
                    basis = $3,
                    status = 'active',
                    updated_at = NOW()
                WHERE learning_id = $4 AND project_id = $5 AND org_id = $6
                """,
                learning.strip(),
                expected_outcome.strip(),
                basis.strip(),
                learning_id,
                project_id,
                org_id,
            )
            await _insert_learning_review(
                connection,
                learning_id=learning_id,
                project_id=project_id,
                org_id=org_id,
                user_id=user_id,
                decision="edited",
                edited_learning=learning.strip(),
                edited_expected_outcome=expected_outcome.strip(),
                edited_basis=basis.strip(),
            )
    return {
        "learning_id": learning_id,
        "status": "active",
        "learning": learning.strip(),
        "expected_outcome": expected_outcome.strip(),
        "basis": basis.strip(),
    }


@router.get("/learnings/{learning_id}/reviews")
async def list_learning_reviews(
    learning_id: str,
    request: Request,
    project_id: str = Query(...),
    limit: int = Query(DEFAULT_LIMIT, ge=1),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """
    List review history for a specific learning.
    
    Note: org_id and user_id are no longer required for read operations.
    The project_id is sufficient to scope the data. Reviews from all users are returned.
    """
    pool = request.app.state.pool
    async with pool.acquire() as connection:
        rows = await connection.fetch(
            """
            SELECT id, learning_id, project_id, org_id, user_id, decision, reason,
                   edited_learning, edited_expected_outcome, edited_basis, created_at
            FROM learning_reviews
            WHERE learning_id = $1 AND project_id = $2
            ORDER BY created_at DESC
            LIMIT $3 OFFSET $4
            """,
            learning_id,
            project_id,
            limit,
            offset,
        )
    reviews = []
    for row in rows:
        reviews.append(
            {
                "id": row["id"],
                "learning_id": row["learning_id"],
                "project_id": row["project_id"],
                "org_id": row["org_id"],
                "user_id": row["user_id"],
                "decision": row["decision"],
                "reason": row["reason"],
                "edited_learning": row["edited_learning"],
                "edited_expected_outcome": row["edited_expected_outcome"],
                "edited_basis": row["edited_basis"],
                "created_at": _to_iso(row["created_at"]),
            }
        )
    return {"learning_id": learning_id, "reviews": reviews}


@router.get("/learnings/{learning_id}/usage")
async def get_learning_usage(
    learning_id: str,
    request: Request,
    project_id: str = Query(...),
    window: int = Query(DEFAULT_LIMIT, ge=1),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """
    Get usage statistics for a specific learning.
    
    Note: org_id and user_id are no longer required for read operations.
    The project_id is sufficient to scope the data.
    """
    pool = request.app.state.pool
    query = """
        SELECT task_id, reward_score, token_total, failure_flag, created_at
        FROM learning_usage
        WHERE learning_id = $1 AND project_id = $2
        ORDER BY created_at DESC
        LIMIT $3 OFFSET $4
    """
    async with pool.acquire() as connection:
        rows = await connection.fetch(query, learning_id, project_id, window, offset)
    usage = []
    for row in rows:
        usage.append(
            {
                "task_id": row["task_id"],
                "reward_score": row["reward_score"],
                "token_total": row["token_total"],
                "failure_flag": row["failure_flag"],
                "created_at": _to_iso(row["created_at"]),
            }
        )
    return {"learning_id": learning_id, "usage": usage}

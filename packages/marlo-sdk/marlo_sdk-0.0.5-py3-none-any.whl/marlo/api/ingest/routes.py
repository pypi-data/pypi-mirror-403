"""Ingest routes for Marlo SDK events and learning state."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request

from marlo.billing import InsufficientCreditsError, require_credits
from marlo.storage.postgres.agents import upsert_agent_definition
from marlo.storage.postgres.database import Database

logger = logging.getLogger(__name__)

router = APIRouter()

_SCOPE_PATH = "/internal/marlo/scope"
_DEFAULT_SCOPE_TTL_SECONDS = 60.0
_DEFAULT_TIMEOUT = 5.0


class _ScopeCache:
    def __init__(self, ttl_seconds: float) -> None:
        self._ttl = ttl_seconds
        self._cache: dict[str, tuple[float, dict[str, str]]] = {}

    def get(self, key: str) -> dict[str, str] | None:
        now = time.time()
        entry = self._cache.get(key)
        if not entry:
            return None
        expires_at, scope = entry
        if expires_at <= now:
            self._cache.pop(key, None)
            return None
        return scope

    def set(self, key: str, scope: dict[str, str]) -> None:
        self._cache[key] = (time.time() + self._ttl, scope)


_SCOPE_CACHE = _ScopeCache(_DEFAULT_SCOPE_TTL_SECONDS)


def _backend_url() -> str:
    value = os.getenv("MARLO_BACKEND_URL")
    if value:
        return value.rstrip("/")
    raise RuntimeError("MARLO_BACKEND_URL is required for ingest scope resolution.")


def _require_api_key(request: Request) -> str:
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth:
        raise HTTPException(status_code=401, detail="Missing API key")
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Invalid API key")
    token = auth.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return token


def _cache_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


async def _fetch_scope(api_key: str) -> dict[str, str]:
    import logging
    logger = logging.getLogger(__name__)

    cached = _SCOPE_CACHE.get(_cache_key(api_key))
    if cached:
        return cached
    url = f"{_backend_url()}{_SCOPE_PATH}"
    logger.info(f"Fetching scope from: {url}")
    try:
        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
            response = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
            logger.info(f"Scope response status: {response.status_code}")
    except Exception as exc:
        logger.error(f"Failed to fetch scope: {exc}")
        raise HTTPException(status_code=502, detail="Scope resolver unavailable") from exc
    if response.status_code == 401:
        raise HTTPException(status_code=401, detail="Invalid API key")
    if not (200 <= response.status_code < 300):
        logger.error(f"Scope resolver returned {response.status_code}: {response.text}")
        raise HTTPException(status_code=502, detail=f"Scope resolver error: {response.status_code}")
    try:
        payload = response.json()
    except ValueError as exc:
        raise HTTPException(status_code=502, detail="Invalid scope response") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=502, detail="Invalid scope response")
    # Extract scope from nested structure if present
    scope_data = payload.get("scope", payload)
    if not isinstance(scope_data, dict):
        raise HTTPException(status_code=502, detail="Invalid scope response")
    project_id = scope_data.get("project_id")
    org_id = scope_data.get("org_id")
    user_id = scope_data.get("user_id")
    if not isinstance(project_id, str) or not project_id.strip():
        raise HTTPException(status_code=502, detail="Invalid scope response")
    if not isinstance(org_id, str) or not org_id.strip():
        raise HTTPException(status_code=502, detail="Invalid scope response")
    if not isinstance(user_id, str) or not user_id.strip():
        raise HTTPException(status_code=502, detail="Invalid scope response")
    scope = {"project_id": project_id.strip(), "org_id": org_id.strip(), "user_id": user_id.strip()}
    _SCOPE_CACHE.set(_cache_key(api_key), scope)
    return scope


def _require_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise HTTPException(status_code=400, detail=f"{field} must be an int")
    return value


def _task_start_payload(event_payload: dict[str, Any] | None) -> tuple[str, dict[str, Any]]:
    task = "task"
    metadata: dict[str, Any] = {}
    if isinstance(event_payload, dict):
        payload_task = event_payload.get("task")
        if isinstance(payload_task, str) and payload_task.strip():
            task = payload_task.strip()
        payload_meta = event_payload.get("metadata")
        if isinstance(payload_meta, dict):
            metadata = dict(payload_meta)
    return task, metadata


def _task_end_payload(event_payload: dict[str, Any] | None) -> tuple[str, str | None]:
    status = "success"
    final_answer = None
    if isinstance(event_payload, dict):
        payload_status = event_payload.get("status")
        if isinstance(payload_status, str) and payload_status.strip():
            status = payload_status.strip()
        payload_final = event_payload.get("final_answer")
        if payload_final is not None:
            final_answer = str(payload_final)
    return status, final_answer


def _extract_token_usage_metadata(event_payload: dict[str, Any] | None) -> dict[str, Any] | None:
    """Extract token usage from task_end payload and format for learning_usage structure."""
    if not isinstance(event_payload, dict):
        return None
    token_usage = event_payload.get("token_usage")
    if not isinstance(token_usage, dict):
        return None
    prompt = token_usage.get("prompt_tokens", 0)
    completion = token_usage.get("completion_tokens", 0)
    reasoning = token_usage.get("reasoning_tokens", 0)
    total = token_usage.get("total_tokens", 0)
    calls = token_usage.get("calls", 0)
    if total == 0 and (prompt or completion or reasoning):
        total = (prompt or 0) + (completion or 0) + (reasoning or 0)
    if total == 0:
        return None
    return {
        "learning_usage": {
            "task": {
                "token_usage": {
                    "prompt_tokens": prompt,
                    "completion_tokens": completion,
                    "reasoning_tokens": reasoning,
                    "thinking_tokens": reasoning,
                    "total_tokens": total,
                    "calls": calls,
                },
                "failure_flag": False,
            },
            "roles": {},
        }
    }


@router.get("/scope")
async def get_scope(request: Request) -> dict[str, Any]:
    api_key = _require_api_key(request)
    scope = await _fetch_scope(api_key)
    return {"scope": scope}


@router.post("/events")
async def ingest_events(request: Request) -> dict[str, Any]:
    """
    Ingest events from SDK clients.

    This endpoint has comprehensive error handling to catch and log all exceptions.
    """
    import logging
    import traceback

    logger = logging.getLogger(__name__)

    try:
        api_key = _require_api_key(request)
        scope = await _fetch_scope(api_key)

        try:
            payload = await request.json()
        except Exception as exc:
            logger.error(f"Failed to parse JSON payload: {exc}")
            raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

        if not isinstance(payload, list):
            logger.error(f"Payload is not a list: {type(payload)}")
            raise HTTPException(status_code=400, detail="Payload must be a list of events")

        if not payload:
            return {"ingested": 0}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error in initial request processing: {exc}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal error: {exc!s}") from exc
    # Wrap the entire event processing in try-catch
    try:
        normalized_events: list[dict[str, Any]] = []
        session_ids: set[int] = set()
        task_start_map: dict[int, tuple[int, str, dict[str, Any]]] = {}
        session_metadata_map: dict[int, dict[str, Any]] = {}
        session_task_map: dict[int, str] = {}
        task_end_sessions: set[int] = set()

        for entry in payload:
            if not isinstance(entry, dict):
                raise HTTPException(status_code=400, detail="Invalid event entry")
            run_id = _require_int(entry.get("run_id"), "run_id")
            session_ids.add(run_id)
            task_id = entry.get("task_id")
            if task_id is not None:
                task_id = _require_int(task_id, "task_id")
            event_type = entry.get("event_type")
            if event_type == "task_start":
                if task_id is None:
                    raise HTTPException(status_code=400, detail="task_id is required for task_start")
                task_text, metadata = _task_start_payload(entry.get("payload"))
                # Include agent_id in metadata for learning system
                event_agent_id = entry.get("agent_id")
                if isinstance(event_agent_id, str) and event_agent_id.strip():
                    metadata["agent_id"] = event_agent_id.strip()
                task_start_map[task_id] = (run_id, task_text, metadata)
                session_task_map.setdefault(run_id, task_text)
                if metadata and run_id not in session_metadata_map:
                    session_metadata_map[run_id] = dict(metadata)
            normalized_events.append(entry)

        pool = request.app.state.pool
        logger.info(f"Processing {len(normalized_events)} events for {len(session_ids)} sessions")

        async with pool.acquire() as connection, connection.transaction():
            existing_sessions = set()
            if session_ids:
                rows = await connection.fetch(
                    "SELECT id FROM sessions WHERE id = ANY($1::bigint[])",
                    list(session_ids),
                )
                existing_sessions = {row["id"] for row in rows}
            missing_sessions = session_ids - existing_sessions
            for session_id in missing_sessions:
                task_text = session_task_map.get(session_id, "session")
                metadata = session_metadata_map.get(session_id)
                await connection.execute(
                    "INSERT INTO sessions(id, task, status, project_id, org_id, user_id, metadata)"
                    " VALUES ($1, $2, 'running', $3, $4, $5, $6)"
                    " ON CONFLICT DO NOTHING",
                    session_id,
                    task_text,
                    scope["project_id"],
                    scope["org_id"],
                    scope["user_id"],
                    json.dumps(metadata) if metadata else None,
                )

            task_ids = list(task_start_map.keys())
            existing_tasks: set[int] = set()
            if task_ids:
                rows = await connection.fetch(
                    "SELECT id FROM session_tasks WHERE id = ANY($1::bigint[])",
                    task_ids,
                )
                existing_tasks = {row["id"] for row in rows}
            for task_id, (session_id, task_text, metadata) in task_start_map.items():
                if task_id in existing_tasks:
                    continue
                await connection.execute(
                    "INSERT INTO session_tasks(id, session_id, task, status, project_id, org_id, user_id, metadata)"
                    " VALUES ($1, $2, $3, 'running', $4, $5, $6, $7)"
                    " ON CONFLICT DO NOTHING",
                    task_id,
                    session_id,
                    task_text,
                    scope["project_id"],
                    scope["org_id"],
                    scope["user_id"],
                    json.dumps(metadata) if metadata else None,
                )
                if metadata:
                    await connection.execute(
                        "UPDATE sessions SET metadata = "
                        "COALESCE(metadata, '{}'::jsonb) || "
                        "(CASE WHEN metadata ? 'thread_name' THEN $2::jsonb - 'thread_name' ELSE $2::jsonb END)"
                        " WHERE id = $1",
                        session_id,
                        json.dumps(metadata),
                    )

            for entry in normalized_events:
                event_type = entry.get("event_type")
                if event_type not in {"task_start", "task_end"}:
                    continue
                task_id = entry.get("task_id")
                if not isinstance(task_id, int) or isinstance(task_id, bool):
                    continue
                payload = entry.get("payload")
                if not isinstance(payload, dict):
                    continue
                metadata = payload.get("metadata")
                if not isinstance(metadata, dict) or not metadata:
                    continue
                await connection.execute(
                    "UPDATE session_tasks SET metadata = COALESCE(metadata, '{}'::jsonb) || $2::jsonb"
                    " WHERE id = $1",
                    task_id,
                    json.dumps(metadata),
                )
                session_id = entry.get("run_id")
                if isinstance(session_id, int) and not isinstance(session_id, bool):
                    await connection.execute(
                        "UPDATE sessions SET metadata = "
                        "COALESCE(metadata, '{}'::jsonb) || "
                        "(CASE WHEN metadata ? 'thread_name' THEN $2::jsonb - 'thread_name' ELSE $2::jsonb END)"
                        " WHERE id = $1",
                        session_id,
                        json.dumps(metadata),
                    )

            for entry in normalized_events:
                event_type = entry.get("event_type")
                if event_type != "task_end":
                    continue
                task_id = entry.get("task_id")
                if not isinstance(task_id, int) or isinstance(task_id, bool):
                    continue
                payload = entry.get("payload") if isinstance(entry.get("payload"), dict) else None
                status, final_answer = _task_end_payload(payload)
                token_metadata = _extract_token_usage_metadata(payload)
                if token_metadata:
                    await connection.execute(
                        "UPDATE session_tasks SET status = $2, final_answer = $3, completed_at = NOW(),"
                        " metadata = COALESCE(metadata, '{}'::jsonb) || $4::jsonb"
                        " WHERE id = $1",
                        task_id,
                        status,
                        final_answer,
                        json.dumps(token_metadata),
                    )
                else:
                    await connection.execute(
                        "UPDATE session_tasks SET status = $2, final_answer = $3, completed_at = NOW()"
                        " WHERE id = $1",
                        task_id,
                        status,
                        final_answer,
                    )
                session_id = entry.get("run_id")
                if isinstance(session_id, int) and not isinstance(session_id, bool):
                    task_end_sessions.add(session_id)

            for entry in normalized_events:
                event_type = entry.get("event_type")
                if event_type == "agent_definition":
                    run_id = entry.get("run_id")
                    if isinstance(run_id, int) and not isinstance(run_id, bool):
                        await upsert_agent_definition(connection, run_id, entry)

            rows = [
                (
                    entry.get("run_id"),
                    scope["project_id"],
                    scope["org_id"],
                    scope["user_id"],
                    json.dumps(entry),
                )
                for entry in normalized_events
            ]
            for row in rows:
                await connection.execute(
                    "INSERT INTO trajectory_events(session_id, project_id, org_id, user_id, event)"
                    " VALUES ($1, $2, $3, $4, $5)"
                    " ON CONFLICT ((event->>'event_id')) WHERE event->>'event_id' IS NOT NULL DO NOTHING",
                    *row,
                )

        rewards_skipped = False
        reward_skip_reason = None
        
        if task_end_sessions:
            from marlo.billing import get_billing_client
            billing_client = get_billing_client()
            
            for session_id in task_end_sessions:
                try:
                    usage_result = await billing_client.record_task_usage(
                        scope["org_id"], 
                        scope["project_id"]
                    )
                    if not usage_result.get("success"):
                        logger.warning(f"Failed to record task usage for session {session_id}")
                except Exception as e:
                    logger.warning(f"Error recording task usage for session {session_id}: {e}")
            
            try:
                await require_credits(scope["org_id"])
                database: Database = request.app.state.database
                for session_id in task_end_sessions:
                    await database.enqueue_reward_jobs_for_session(session_id)
                    await database.process_reward_jobs_for_session(session_id)
            except InsufficientCreditsError:
                can_run = await billing_client.check_can_run_reward(scope["org_id"])
                if not can_run:
                    try:
                        quota = await billing_client.get_quota(scope["org_id"])
                        if quota.get("freeTasksUsed", 0) >= quota.get("freeTasksLimit", 50) and not quota.get("hasPaymentMethod"):
                            reward_skip_reason = "Free tier exhausted. Add payment method to enable AI evaluations."
                        else:
                            reward_skip_reason = "Insufficient credits for AI evaluations."
                    except Exception as e:
                        logger.warning(f"Failed to get quota details: {e}")
                        reward_skip_reason = "Unable to process AI evaluations at this time."
                        
                    logger.warning(
                        f"Skipping reward processing for org {scope['org_id']}: {reward_skip_reason}"
                    )
                    rewards_skipped = True

        response: dict[str, Any] = {"ingested": len(normalized_events)}
        if rewards_skipped:
            response["reward_skipped"] = True
            response["reward_skip_reason"] = reward_skip_reason or "Unable to process AI evaluations."
            response["warning"] = reward_skip_reason or "Reward evaluation skipped: insufficient credits. Please add credits to enable AI-powered evaluations."
        return response
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error processing events: {exc}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal error: {exc!s}") from exc


@router.post("/learnings")
async def get_learnings(request: Request) -> dict[str, Any]:
    api_key = _require_api_key(request)
    scope = await _fetch_scope(api_key)
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid payload")
    learning_key = payload.get("learning_key")
    if not isinstance(learning_key, str) or not learning_key.strip():
        raise HTTPException(status_code=400, detail="learning_key is required")
    database: Database = request.app.state.database
    learning_state = await database.fetch_learning_state(
        learning_key.strip(),
        project_id=scope["project_id"],
        org_id=scope["org_id"],
        user_id=scope["user_id"],
    )
    return {"learning_state": learning_state}


@router.get("/sessions/{session_id}/agents")
async def get_session_agents(session_id: int, request: Request) -> dict[str, Any]:
    """Return all agents and their definitions for a session."""
    api_key = _require_api_key(request)
    scope = await _fetch_scope(api_key)
    database: Database = request.app.state.database

    session = await database.fetch_session(session_id, project_id=scope["project_id"])
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    agents = await database.fetch_session_agents(session_id)
    return {"agents": agents}

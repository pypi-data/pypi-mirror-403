"""Copilot conversation and search routes."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Literal

from fastapi import APIRouter, Query, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from marlo.api.dashboard.common import DEFAULT_LIMIT, _to_iso
from marlo.search.langgraph_pipeline import CopilotPipeline, StreamEvent
from marlo.search.storage.hot_storage import get_hot_storage_manager
from marlo.runtime import get_llm_client
from marlo.billing import require_credits, InsufficientCreditsError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/{project_id}/copilot", tags=["copilot"])

MAX_QUERY_LENGTH = 2000


class CreateThreadRequest(BaseModel):
    """Request body for creating a new thread and starting search."""

    query: str = Field(..., min_length=1, max_length=MAX_QUERY_LENGTH)


class ContinueThreadRequest(BaseModel):
    """Request body for continuing a conversation."""

    query: str = Field(..., min_length=1, max_length=MAX_QUERY_LENGTH)


class ThreadResponse(BaseModel):
    """Response for thread data."""

    id: str
    title: str | None
    status: Literal["active", "archived"]
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    """Response for message data."""

    id: str
    role: Literal["user", "assistant"]
    content: str
    metadata: dict[str, Any] | None
    created_at: str


class ThreadWithMessagesResponse(BaseModel):
    """Response for thread with messages."""

    thread: ThreadResponse
    messages: list[MessageResponse]


def _get_user_id(request: Request) -> str:
    """Extract user ID from request state or auth."""
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return user_id
    user = getattr(request.state, "user", None)
    if user and hasattr(user, "id"):
        return str(user.id)
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return "auth_user"
    return "anonymous"


@router.get("/threads")
async def list_threads(
    request: Request,
    project_id: str,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Literal["active", "archived"] | None = None,
) -> dict[str, Any]:
    """
    List user's copilot threads for a project.

    Returns threads ordered by most recently updated first.
    """
    pool = request.app.state.pool
    user_id = _get_user_id(request)

    params: list[Any] = [user_id, project_id]
    clauses = ["user_id = $1", "project_id = $2"]

    if status:
        params.append(status)
        clauses.append(f"status = ${len(params)}")

    params.extend([limit, offset])
    where_clause = " AND ".join(clauses)

    query = f"""
        SELECT id, title, status, created_at, updated_at
        FROM copilot_threads
        WHERE {where_clause}
        ORDER BY updated_at DESC
        LIMIT ${len(params) - 1} OFFSET ${len(params)}
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    threads = [
        {
            "id": str(row["id"]),
            "title": row["title"],
            "status": row["status"],
            "created_at": _to_iso(row["created_at"]),
            "updated_at": _to_iso(row["updated_at"]),
        }
        for row in rows
    ]

    count_query = f"""
        SELECT COUNT(*) FROM copilot_threads
        WHERE {" AND ".join(clauses[:2 + (1 if status else 0)])}
    """
    async with pool.acquire() as conn:
        total = await conn.fetchval(count_query, *params[:2 + (1 if status else 0)])

    return {
        "threads": threads,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/threads")
async def create_thread(
    request: Request,
    project_id: str,
    body: CreateThreadRequest,
) -> StreamingResponse:
    """
    Create a new copilot thread and start a search.

    Returns SSE stream with search progress and results.
    The thread ID is returned in the X-Thread-Id header.
    """
    pool = request.app.state.pool
    user_id = _get_user_id(request)

    # Check if user has credits before proceeding
    try:
        await require_credits(user_id)
    except InsufficientCreditsError:
        raise HTTPException(
            status_code=402,
            detail="Insufficient credits. Please add credits to continue using the copilot.",
        )

    llm_client = get_llm_client()
    hot_storage = get_hot_storage_manager()
    checkpointer = getattr(request.app.state, "checkpointer", None)

    thread_id = str(uuid.uuid4())
    title = body.query[:100] if len(body.query) > 100 else body.query

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO copilot_threads (id, project_id, user_id, title, status)
            VALUES ($1, $2, $3, $4, 'active')
            """,
            uuid.UUID(thread_id),
            project_id,
            user_id,
            title,
        )

        await conn.execute(
            """
            INSERT INTO copilot_messages (thread_id, role, content)
            VALUES ($1, 'user', $2)
            """,
            uuid.UUID(thread_id),
            body.query,
        )

    pipeline = CopilotPipeline(
        llm_client=llm_client,
        pool=pool,
        checkpointer=checkpointer,
        hot_storage=hot_storage,
    )

    async def generate():
        try:
            final_answer = ""
            findings: list[str] = []

            async for event in pipeline.execute(
                thread_id=thread_id,
                project_id=project_id,
                user_id=user_id,
                query=body.query,
            ):
                yield f"data: {json.dumps(event.to_dict())}\n\n"

                if event.type == "answer":
                    final_answer = event.data.get("answer", "")
                    findings = event.data.get("key_findings", [])
                elif event.type == "finding":
                    findings.append(event.data.get("content", ""))

            metadata: dict[str, Any] = {}
            if findings:
                metadata["findings"] = findings

            if final_answer:
                async with pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO copilot_messages (thread_id, role, content, metadata)
                        VALUES ($1, 'assistant', $2, $3)
                        """,
                        uuid.UUID(thread_id),
                        final_answer,
                        json.dumps(metadata) if metadata else None,
                    )

        except Exception as e:
            logger.exception("Copilot search failed")
            yield f"data: {json.dumps({'type': 'error', 'stage': 'pipeline', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Thread-Id": thread_id,
        },
    )


@router.get("/threads/{thread_id}")
async def get_thread(
    request: Request,
    project_id: str,
    thread_id: str,
) -> ThreadWithMessagesResponse:
    """
    Get a thread with all its messages.

    Includes conversation history for context.
    """
    pool = request.app.state.pool
    user_id = _get_user_id(request)

    try:
        thread_uuid = uuid.UUID(thread_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid thread ID format")

    async with pool.acquire() as conn:
        thread_row = await conn.fetchrow(
            """
            SELECT id, title, status, created_at, updated_at
            FROM copilot_threads
            WHERE id = $1 AND project_id = $2 AND user_id = $3
            """,
            thread_uuid,
            project_id,
            user_id,
        )

        if thread_row is None:
            raise HTTPException(status_code=404, detail="Thread not found")

        message_rows = await conn.fetch(
            """
            SELECT id, role, content, metadata, created_at
            FROM copilot_messages
            WHERE thread_id = $1
            ORDER BY created_at ASC
            """,
            thread_uuid,
        )

    thread = ThreadResponse(
        id=str(thread_row["id"]),
        title=thread_row["title"],
        status=thread_row["status"],
        created_at=_to_iso(thread_row["created_at"]) or "",
        updated_at=_to_iso(thread_row["updated_at"]) or "",
    )

    messages = [
        MessageResponse(
            id=str(row["id"]),
            role=row["role"],
            content=row["content"],
            metadata=row["metadata"] if isinstance(row["metadata"], dict) else None,
            created_at=_to_iso(row["created_at"]) or "",
        )
        for row in message_rows
    ]

    return ThreadWithMessagesResponse(thread=thread, messages=messages)


@router.post("/threads/{thread_id}/messages")
async def continue_thread(
    request: Request,
    project_id: str,
    thread_id: str,
    body: ContinueThreadRequest,
) -> StreamingResponse:
    """
    Continue a conversation in an existing thread.

    Uses previous messages as context for the new query.
    Returns SSE stream with search progress and results.
    """
    pool = request.app.state.pool
    user_id = _get_user_id(request)

    # Check if user has credits before proceeding
    try:
        await require_credits(user_id)
    except InsufficientCreditsError:
        raise HTTPException(
            status_code=402,
            detail="Insufficient credits. Please add credits to continue using the copilot.",
        )

    llm_client = get_llm_client()
    hot_storage = get_hot_storage_manager()
    checkpointer = getattr(request.app.state, "checkpointer", None)

    try:
        thread_uuid = uuid.UUID(thread_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid thread ID format")

    async with pool.acquire() as conn:
        thread_row = await conn.fetchrow(
            """
            SELECT id, status
            FROM copilot_threads
            WHERE id = $1 AND project_id = $2 AND user_id = $3
            """,
            thread_uuid,
            project_id,
            user_id,
        )

        if thread_row is None:
            raise HTTPException(status_code=404, detail="Thread not found")

        if thread_row["status"] == "archived":
            raise HTTPException(status_code=400, detail="Cannot continue archived thread")

        message_rows = await conn.fetch(
            """
            SELECT role, content
            FROM copilot_messages
            WHERE thread_id = $1
            ORDER BY created_at ASC
            LIMIT 20
            """,
            thread_uuid,
        )

        await conn.execute(
            """
            INSERT INTO copilot_messages (thread_id, role, content)
            VALUES ($1, 'user', $2)
            """,
            thread_uuid,
            body.query,
        )

    conversation_history = [
        {"role": row["role"], "content": row["content"]}
        for row in message_rows
    ]

    pipeline = CopilotPipeline(
        llm_client=llm_client,
        pool=pool,
        checkpointer=checkpointer,
        hot_storage=hot_storage,
    )

    async def generate():
        try:
            final_answer = ""
            findings: list[str] = []

            async for event in pipeline.execute(
                thread_id=thread_id,
                project_id=project_id,
                user_id=user_id,
                query=body.query,
                conversation_history=conversation_history,
            ):
                yield f"data: {json.dumps(event.to_dict())}\n\n"

                if event.type == "answer":
                    final_answer = event.data.get("answer", "")
                    findings = event.data.get("key_findings", [])
                elif event.type == "finding":
                    findings.append(event.data.get("content", ""))

            metadata: dict[str, Any] = {}
            if findings:
                metadata["findings"] = findings

            if final_answer:
                async with pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO copilot_messages (thread_id, role, content, metadata)
                        VALUES ($1, 'assistant', $2, $3)
                        """,
                        thread_uuid,
                        final_answer,
                        json.dumps(metadata) if metadata else None,
                    )

                    await conn.execute(
                        "UPDATE copilot_threads SET updated_at = NOW() WHERE id = $1",
                        thread_uuid,
                    )

        except Exception as e:
            logger.exception("Copilot continuation failed")
            yield f"data: {json.dumps({'type': 'error', 'stage': 'pipeline', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.delete("/threads/{thread_id}")
async def archive_thread(
    request: Request,
    project_id: str,
    thread_id: str,
) -> dict[str, str]:
    """
    Archive a copilot thread.

    Archived threads are hidden from the default list but can still be retrieved.
    """
    pool = request.app.state.pool
    user_id = _get_user_id(request)

    try:
        thread_uuid = uuid.UUID(thread_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid thread ID format")

    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE copilot_threads
            SET status = 'archived'
            WHERE id = $1 AND project_id = $2 AND user_id = $3
            """,
            thread_uuid,
            project_id,
            user_id,
        )

        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="Thread not found")

    return {"status": "archived", "thread_id": thread_id}

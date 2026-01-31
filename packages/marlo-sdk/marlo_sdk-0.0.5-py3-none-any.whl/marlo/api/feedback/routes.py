"""Feedback routes for processing user feedback and updating prompt chunks."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from marlo.feedback.chunk_updater import update_reward_chunk, update_learning_chunk
from marlo.storage.postgres.database import Database

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/feedback/reward")
async def process_reward_feedback(request: Request) -> dict[str, Any]:
    """
    Process reward feedback and update the project's reward guidelines chunk.

    Expected payload:
    {
        "project_id": str,
        "rationale": str,
        "user_feedback": str
    }
    """
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    project_id = payload.get("project_id")
    rationale = payload.get("rationale")
    user_feedback = payload.get("user_feedback")

    if not isinstance(project_id, str) or not project_id.strip():
        raise HTTPException(status_code=400, detail="project_id is required")
    if not isinstance(user_feedback, str) or not user_feedback.strip():
        raise HTTPException(status_code=400, detail="user_feedback is required")

    project_id = project_id.strip()
    user_feedback = user_feedback.strip()
    rationale = rationale.strip() if isinstance(rationale, str) else ""

    database: Database = request.app.state.database

    current_chunk = await database.fetch_feedback_chunk(project_id, "reward")
    current_chunk = current_chunk or ""

    updated_chunk = await update_reward_chunk(
        current_chunk=current_chunk,
        rationale=rationale,
        user_feedback=user_feedback,
    )

    await database.upsert_feedback_chunk(project_id, "reward", updated_chunk)

    await database.log_feedback_history(
        project_id=project_id,
        feedback_type="reward_feedback",
        context_data={"rationale": rationale},
        user_feedback=user_feedback,
        chunk_before=current_chunk,
        chunk_after=updated_chunk,
    )

    logger.info("Updated reward chunk for project %s", project_id)

    return {
        "status": "success",
        "project_id": project_id,
        "chunk_updated": current_chunk != updated_chunk,
    }


@router.post("/feedback/learning/edit")
async def process_learning_edit_feedback(request: Request) -> dict[str, Any]:
    """
    Process learning edit feedback and update the project's learning guidelines chunk.

    Expected payload:
    {
        "project_id": str,
        "original_learning": str,
        "edited_learning": str
    }
    """
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    project_id = payload.get("project_id")
    original_learning = payload.get("original_learning")
    edited_learning = payload.get("edited_learning")

    if not isinstance(project_id, str) or not project_id.strip():
        raise HTTPException(status_code=400, detail="project_id is required")
    if not isinstance(original_learning, str) or not original_learning.strip():
        raise HTTPException(status_code=400, detail="original_learning is required")
    if not isinstance(edited_learning, str) or not edited_learning.strip():
        raise HTTPException(status_code=400, detail="edited_learning is required")

    project_id = project_id.strip()
    original_learning = original_learning.strip()
    edited_learning = edited_learning.strip()

    if original_learning == edited_learning:
        return {
            "status": "skipped",
            "project_id": project_id,
            "reason": "No changes detected",
        }

    database: Database = request.app.state.database

    current_chunk = await database.fetch_feedback_chunk(project_id, "learning")
    current_chunk = current_chunk or ""

    updated_chunk = await update_learning_chunk(
        current_chunk=current_chunk,
        feedback_type="edit",
        original_learning=original_learning,
        edited_learning=edited_learning,
    )

    await database.upsert_feedback_chunk(project_id, "learning", updated_chunk)

    await database.log_feedback_history(
        project_id=project_id,
        feedback_type="learning_edit",
        context_data={
            "original_learning": original_learning,
            "edited_learning": edited_learning,
        },
        user_feedback=f"Edited: {original_learning} -> {edited_learning}",
        chunk_before=current_chunk,
        chunk_after=updated_chunk,
    )

    logger.info("Updated learning chunk for project %s (edit)", project_id)

    return {
        "status": "success",
        "project_id": project_id,
        "chunk_updated": current_chunk != updated_chunk,
    }


@router.post("/feedback/learning/reject")
async def process_learning_reject_feedback(request: Request) -> dict[str, Any]:
    """
    Process learning rejection feedback and update the project's learning guidelines chunk.

    Expected payload:
    {
        "project_id": str,
        "rejected_learning": str,
        "rejection_reason": str (optional)
    }
    """
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    project_id = payload.get("project_id")
    rejected_learning = payload.get("rejected_learning")
    rejection_reason = payload.get("rejection_reason")

    if not isinstance(project_id, str) or not project_id.strip():
        raise HTTPException(status_code=400, detail="project_id is required")
    if not isinstance(rejected_learning, str) or not rejected_learning.strip():
        raise HTTPException(status_code=400, detail="rejected_learning is required")

    project_id = project_id.strip()
    rejected_learning = rejected_learning.strip()
    rejection_reason = rejection_reason.strip() if isinstance(rejection_reason, str) else ""

    database: Database = request.app.state.database

    current_chunk = await database.fetch_feedback_chunk(project_id, "learning")
    current_chunk = current_chunk or ""

    updated_chunk = await update_learning_chunk(
        current_chunk=current_chunk,
        feedback_type="reject",
        rejected_learning=rejected_learning,
        rejection_reason=rejection_reason,
    )

    await database.upsert_feedback_chunk(project_id, "learning", updated_chunk)

    await database.log_feedback_history(
        project_id=project_id,
        feedback_type="learning_reject",
        context_data={
            "rejected_learning": rejected_learning,
            "rejection_reason": rejection_reason,
        },
        user_feedback=rejection_reason or "Rejected without reason",
        chunk_before=current_chunk,
        chunk_after=updated_chunk,
    )

    logger.info("Updated learning chunk for project %s (reject)", project_id)

    return {
        "status": "success",
        "project_id": project_id,
        "chunk_updated": current_chunk != updated_chunk,
    }


@router.get("/feedback/chunks/{project_id}")
async def get_feedback_chunks(project_id: str, request: Request) -> dict[str, Any]:
    """Get both feedback chunks for a project."""
    if not project_id or not project_id.strip():
        raise HTTPException(status_code=400, detail="project_id is required")

    project_id = project_id.strip()
    database: Database = request.app.state.database

    chunks = await database.fetch_all_feedback_chunks(project_id)

    return {
        "project_id": project_id,
        "reward_guidelines": chunks["reward"],
        "learning_guidelines": chunks["learning"],
    }


@router.post("/feedback/chunks/{project_id}/reward")
async def update_reward_chunk_directly(
    project_id: str, request: Request
) -> dict[str, Any]:
    """Directly update the reward guidelines chunk for a project."""
    if not project_id or not project_id.strip():
        raise HTTPException(status_code=400, detail="project_id is required")

    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    content = payload.get("content", "")
    if not isinstance(content, str):
        raise HTTPException(status_code=400, detail="content must be a string")

    project_id = project_id.strip()
    database: Database = request.app.state.database

    current_chunk = await database.fetch_feedback_chunk(project_id, "reward")
    await database.upsert_feedback_chunk(project_id, "reward", content)

    await database.log_feedback_history(
        project_id=project_id,
        feedback_type="reward_feedback",
        context_data={"source": "direct_edit"},
        user_feedback="Direct edit by user",
        chunk_before=current_chunk or "",
        chunk_after=content,
    )

    logger.info("Directly updated reward chunk for project %s", project_id)

    return {
        "status": "success",
        "project_id": project_id,
        "chunk_type": "reward",
    }


@router.post("/feedback/chunks/{project_id}/learning")
async def update_learning_chunk_directly(
    project_id: str, request: Request
) -> dict[str, Any]:
    """Directly update the learning guidelines chunk for a project."""
    if not project_id or not project_id.strip():
        raise HTTPException(status_code=400, detail="project_id is required")

    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    content = payload.get("content", "")
    if not isinstance(content, str):
        raise HTTPException(status_code=400, detail="content must be a string")

    project_id = project_id.strip()
    database: Database = request.app.state.database

    current_chunk = await database.fetch_feedback_chunk(project_id, "learning")
    await database.upsert_feedback_chunk(project_id, "learning", content)

    await database.log_feedback_history(
        project_id=project_id,
        feedback_type="learning_edit",
        context_data={"source": "direct_edit"},
        user_feedback="Direct edit by user",
        chunk_before=current_chunk or "",
        chunk_after=content,
    )

    logger.info("Directly updated learning chunk for project %s", project_id)

    return {
        "status": "success",
        "project_id": project_id,
        "chunk_type": "learning",
    }

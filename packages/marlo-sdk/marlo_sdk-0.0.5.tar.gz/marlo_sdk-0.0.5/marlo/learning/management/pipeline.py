"""Learning pipeline orchestration for generation, usage, and lifecycle updates."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from marlo.learning.generation.compiler import LearningCompiler
from marlo.learning.generation.generator import LearningGenerator
from marlo.runtime.llm_client import LLMClient

logger = logging.getLogger(__name__)
if TYPE_CHECKING:
    from marlo.storage.postgres.database import Database

_MAX_RATIONALE_CHARS = 280
_LEARNING_MODEL = "gemini-3-flash-preview"


async def process_learning_update(
    database: Database,
    *,
    session_id: int,
    task_id: int,
    reward_result: dict[str, Any],
    task_metadata: dict[str, Any],
    project_id: str | None = None,
    org_id: str | None = None,
    user_id: str | None = None,
) -> None:
    agent_id = _resolve_agent_id(task_metadata)
    learning_key = agent_id
    usage_records = _extract_usage_records(task_metadata, task_id, reward_result)
    if usage_records:
        await database.upsert_learning_usage(usage_records)

    scoped_project_id = _resolve_scope_value(task_metadata, project_id, "project_id")
    scoped_org_id = _resolve_scope_value(task_metadata, org_id, "org_id")
    scoped_user_id = _resolve_scope_value(task_metadata, user_id, "user_id")
    if not scoped_project_id or not scoped_org_id or not scoped_user_id:
        _record_learning_error(
            task_metadata,
            stage="missing_scope",
            message="project_id, org_id, and user_id are required for learning updates.",
        )
        return

    # Skip learning generation for technical errors
    is_technical_error = reward_result.get("is_technical_error") if isinstance(reward_result, dict) else False
    if is_technical_error:
        # Technical errors indicate system problems, not agent performance issues
        # Don't spend tokens generating learning objects for infrastructure failures
        return

    rationale = reward_result.get("rationale") if isinstance(reward_result, dict) else None
    if isinstance(rationale, str) and rationale.strip():
        try:
            await _generate_and_store_learning_objects(
                database,
                session_id=session_id,
                task_id=task_id,
                learning_key=learning_key,
                agent_id=agent_id,
                rationale=rationale,
                task_metadata=task_metadata,
                project_id=scoped_project_id,
                org_id=scoped_org_id,
                user_id=scoped_user_id,
            )
        except RuntimeError as exc:
            _record_learning_error(
                task_metadata,
                stage="missing_llm_client",
                message=str(exc),
            )
        except Exception as exc:
            _record_learning_error(
                task_metadata,
                stage="generation_error",
                message=str(exc),
            )




async def _generate_and_store_learning_objects(
    database: Database,
    *,
    session_id: int,
    task_id: int,
    learning_key: str,
    agent_id: str,
    rationale: str,
    task_metadata: dict[str, Any],
    project_id: str,
    org_id: str,
    user_id: str,
) -> None:
    existing_learnings = await database.fetch_active_learnings(
        learning_key=learning_key,
        agent_id=agent_id,
        project_id=project_id,
        org_id=org_id,
        user_id=user_id,
    )

    metadata = await _build_generation_metadata(database, session_id, task_metadata, project_id, org_id, user_id)
    client = LLMClient(model=_LEARNING_MODEL)
    generator = LearningGenerator(client)

    result = await generator.generate_learnings(
        rationale,
        metadata,
        existing_learnings=existing_learnings,
        user_id=user_id,
        project_id=project_id,
    )

    if result.action == "skip":
        logger.debug("Learning generation skipped: %s", result.reason)
        return

    if result.action == "update" and result.update_learning_id:
        await _update_existing_learning(
            database,
            learning_id=result.update_learning_id,
            insights=result.insights,
            task_id=task_id,
            rationale=rationale,
            project_id=project_id,
            org_id=org_id,
            user_id=user_id,
        )
        return

    if result.action == "strengthen" and result.update_learning_id:
        await _strengthen_existing_learning(
            database,
            learning_id=result.update_learning_id,
            insights=result.insights,
            task_id=task_id,
            rationale=rationale,
            project_id=project_id,
            org_id=org_id,
            user_id=user_id,
        )
        return

    if result.action == "create" and result.insights:
        await _create_new_learnings(
            database,
            learning_key=learning_key,
            agent_id=agent_id,
            insights=result.insights,
            task_id=task_id,
            rationale=rationale,
            project_id=project_id,
            org_id=org_id,
            user_id=user_id,
        )


async def _update_existing_learning(
    database: Database,
    *,
    learning_id: str,
    insights: list,
    task_id: int,
    rationale: str,
    project_id: str,
    org_id: str,
    user_id: str,
) -> None:
    if not insights:
        return

    insight = insights[0]
    await database.update_learning_object(
        learning_id=learning_id,
        learning=insight.learning,
        expected_outcome=insight.expected_outcome,
        basis=insight.basis,
        confidence=insight.confidence,
        project_id=project_id,
        org_id=org_id,
        user_id=user_id,
    )

    snippet = _truncate_rationale(rationale)
    await database.insert_learning_evidence([(learning_id, task_id, snippet)])
    logger.info("Updated learning %s", learning_id)


async def _strengthen_existing_learning(
    database: Database,
    *,
    learning_id: str,
    insights: list,
    task_id: int,
    rationale: str,
    project_id: str,
    org_id: str,
    user_id: str,
) -> None:
    """Strengthen an existing learning with additional evidence."""
    if not insights:
        return

    insight = insights[0]
    
    # For strengthen action, we mainly increase confidence and add evidence
    # without changing the core learning content significantly
    try:
        # Note: This assumes database has an update_learning_confidence method
        # If not available, we can use the existing update_learning_object method
        await database.update_learning_object(
            learning_id=learning_id,
            confidence=insight.confidence,
            project_id=project_id,
            org_id=org_id,
            user_id=user_id,
        )

        snippet = _truncate_rationale(rationale)
        await database.insert_learning_evidence([(learning_id, task_id, snippet)])
        logger.info("Strengthened learning %s with confidence %.2f", learning_id, insight.confidence)
        
    except Exception as exc:
        logger.warning("Failed to strengthen learning %s: %s", learning_id, exc)
        # Fallback to regular update
        await _update_existing_learning(
            database,
            learning_id=learning_id,
            insights=insights,
            task_id=task_id,
            rationale=rationale,
            project_id=project_id,
            org_id=org_id,
            user_id=user_id,
        )


async def _create_new_learnings(
    database: Database,
    *,
    learning_key: str,
    agent_id: str,
    insights: list,
    task_id: int,
    rationale: str,
    project_id: str,
    org_id: str,
    user_id: str,
) -> None:
    compiler = LearningCompiler()
    insight_dicts = [
        {
            "learning": ins.learning,
            "expected_outcome": ins.expected_outcome,
            "basis": ins.basis,
            "confidence": ins.confidence,
        }
        for ins in insights
    ]

    wrapped = [
        type("LI", (), {"agent_source": "learning_generator", "learning": d, "confidence": d["confidence"]})()
        for d in insight_dicts
    ]

    objects = compiler.compile(wrapped, agent_id=agent_id)
    if not objects:
        return

    await database.insert_learning_objects(
        learning_key,
        objects,
        project_id=project_id,
        org_id=org_id,
        user_id=user_id,
    )

    fallback_snippet = _truncate_rationale(rationale)
    evidence_records = []
    for obj in objects:
        learning_id = obj.get("learning_id")
        if not learning_id:
            continue
        evidence_records.append((learning_id, task_id, fallback_snippet))

    if evidence_records:
        await database.insert_learning_evidence(evidence_records)

    logger.info("Created %d new learnings", len(objects))


async def _build_generation_metadata(
    database: Database,
    session_id: int,
    task_metadata: dict[str, Any],
    project_id: str,
    org_id: str,
    user_id: str,
) -> dict[str, Any]:
    tools = _extract_tool_names(task_metadata)
    if not tools:
        tools = await database.fetch_session_tool_names(session_id)
    
    # Get session learning context
    session_learnings = []
    session_context = "No session context available."
    
    try:
        from marlo.learning.management.session_state import get_session_state
        session_state = await get_session_state(database, str(session_id))
        if session_state:
            session_learnings = session_state.learnings_generated_this_session
            session_summary = session_state.get_recent_scores_summary()
            session_context = f"""
Session Learning Context:
- Tasks completed: {session_summary['task_count']}
- Performance trend: {session_summary['reward_trend']}
- Sentiment trend: {session_summary['sentiment_trend']}
- Learnings generated this session: {session_summary['learnings_count']}

Recent session patterns:
{session_state.trajectory_digest or "No patterns identified yet."}
"""
    except Exception as exc:
        logger.warning(f"Failed to fetch session learning context: {exc}")

    return {
        "agent": _resolve_agent_id(task_metadata),
        "tools": tools,
        "session_learnings": session_learnings,
        "session_context": session_context,
    }


def _extract_tool_names(task_metadata: dict[str, Any]) -> list[str]:
    raw = task_metadata.get("tools") or task_metadata.get("tool_names")
    if isinstance(raw, str) and raw.strip():
        return [raw.strip()]
    if isinstance(raw, (list, tuple, set)):
        return [str(tool).strip() for tool in raw if str(tool).strip()]
    return []


def _resolve_agent_id(task_metadata: dict[str, Any]) -> str:
    for key in ("agent_id", "agent_name", "agent_role", "agent"):
        value = task_metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "agent"


def _resolve_scope_value(task_metadata: dict[str, Any], fallback: str | None, key: str) -> str | None:
    value = fallback
    if not value and isinstance(task_metadata, dict):
        value = task_metadata.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _extract_usage_records(
    task_metadata: dict[str, Any],
    task_id: int,
    reward_result: dict[str, Any],
) -> list[tuple[str, int, float | None, float | None, bool]]:
    usage_snapshot = task_metadata.get("learning_usage")
    task_block = usage_snapshot.get("task") if isinstance(usage_snapshot, dict) and isinstance(usage_snapshot.get("task"), dict) else {}
    reward_score = reward_result.get("score") if isinstance(reward_result, dict) else None
    token_total = _extract_token_total(task_metadata, task_block)
    failure_flag = bool(task_block.get("failure_flag")) if isinstance(task_block, dict) else False
    applied_ids = task_metadata.get("applied_learning_ids")
    if not isinstance(applied_ids, (list, tuple, set)):
        return []
    records = []
    seen: set[str] = set()
    for learning_id in applied_ids:
        if not isinstance(learning_id, str) or not learning_id.strip():
            continue
        normalized = learning_id.strip()
        if normalized in seen:
            continue
        seen.add(normalized)
        records.append(
            (
                normalized,
                task_id,
                _coerce_float(reward_score),
                _coerce_float(token_total),
                failure_flag,
            )
        )
    return records


def _extract_token_total(task_metadata: dict[str, Any], task_block: dict[str, Any]) -> float | None:
    token_usage = task_block.get("token_usage") if isinstance(task_block, dict) else None
    if not isinstance(token_usage, dict):
        token_usage = task_metadata.get("token_usage") if isinstance(task_metadata.get("token_usage"), dict) else {}
    total = token_usage.get("total_tokens")
    if total is not None:
        return _coerce_float(total)
    prompt = token_usage.get("prompt_tokens")
    completion = token_usage.get("completion_tokens")
    if prompt is None or completion is None:
        return None
    try:
        return float(prompt) + float(completion)
    except (TypeError, ValueError):
        return None


def _truncate_rationale(value: str) -> str:
    text = value.strip()
    if len(text) <= _MAX_RATIONALE_CHARS:
        return text
    return text[: _MAX_RATIONALE_CHARS - 3].rstrip() + "..."


def _record_learning_error(task_metadata: dict[str, Any], *, stage: str, message: str) -> None:
    if not isinstance(task_metadata, dict):
        return
    payload = {"stage": stage, "message": message}
    task_metadata["learning_error"] = payload


def _coerce_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


__all__ = ["process_learning_update"]

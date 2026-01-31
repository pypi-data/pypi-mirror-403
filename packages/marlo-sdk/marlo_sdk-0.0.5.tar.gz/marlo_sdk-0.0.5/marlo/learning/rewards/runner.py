"""Execution runner for the LLM-based Judge."""
from __future__ import annotations

import json
import logging
from statistics import pvariance
from typing import Any

from marlo.billing import (
    USAGE_TYPE_REWARD_FLASH,
    USAGE_TYPE_REWARD_PRO,
    BillingLLMClient,
)
from marlo.learning.rewards.judges.prompts import (
    SESSION_ARBITER_PROMPT,
    SESSION_REWARD_PROMPT,
    TRAJECTORY_COMPRESSION_PROMPT,
)
from marlo.learning.management.session_state import (
    get_session_state,
    update_session_state,
    compress_task_to_summary,
)
from marlo.runtime.llm_client import LLMClient
from marlo.trajectories.capture.context import ExecutionContext

logger = logging.getLogger(__name__)

FLASH_MODEL = "gemini/gemini-3-flash-preview"
PRO_MODEL = "gemini/gemini-3-pro-preview"
FLASH_TEMPERATURES = (0.0, 0.3, 0.7)
VARIANCE_THRESHOLD = 0.2
CHUNK_TOKEN_THRESHOLD = 100000
CHUNK_TARGET_TOKENS = 60000

def _truncate(text: str, limit: int = 500) -> str:
    return text[:limit]


def _record_reward_error(
    execution_context: ExecutionContext,
    *,
    stage: str,
    message: str,
    detail: str | None = None,
) -> None:
    task_meta = execution_context.metadata.setdefault("task_metadata", {})
    payload: dict[str, Any] = {"stage": stage, "message": message}
    if detail:
        payload["detail"] = detail
    task_meta["reward_error"] = payload
    execution_context.metadata["task_metadata"] = task_meta

async def evaluate_session(
    task: str,
    final_answer: str,
    execution_context: ExecutionContext,
    agent_context: dict[str, Any] | None = None,
    trajectory_context: dict[str, Any] | None = None,
    *,
    user_id: str | None = None,
    project_id: str | None = None,
) -> dict[str, Any] | None:
    """
    Evaluates the task using an LLM Judge and writes the result to context metadata.

    Args:
        task: The original user request.
        final_answer: The final string output produced by the agent.
        execution_context: The active execution context containing metadata/plan.
        agent_context: Optional context from the agent wrapper (e.g. tools, prompt).
        trajectory_context: Optional structured trajectory context for reward evaluation.
        user_id: Optional user ID for billing.
        project_id: Optional project ID for billing.

    Returns:
        The reward dictionary (score, rationale, principles).

    """
    try:
        task_metadata = execution_context.metadata.get("task_metadata", {})
        execution_mode = task_metadata.get("execution_mode", "default")

        memory_state = task_metadata.get("context_memory_state") if isinstance(task_metadata, dict) else None
        plan_data = memory_state.get("plan") if isinstance(memory_state, dict) else None

        display_metadata = _sanitize_task_metadata(task_metadata)
        if agent_context:
            display_metadata["agent_context"] = agent_context
        if trajectory_context:
            display_metadata["trajectory_context"] = trajectory_context

        if trajectory_context and _estimate_tokens(trajectory_context) > CHUNK_TOKEN_THRESHOLD:
            try:
                compressed_context = await _compress_trajectory_context(
                    trajectory_context, user_id=user_id, project_id=project_id
                )
            except Exception as exc:
                _record_reward_error(
                    execution_context,
                    stage="compression_error",
                    message="Failed to compress trajectory context.",
                    detail=_truncate(str(exc)),
                )
                return None
            display_metadata = _sanitize_task_metadata(task_metadata)
            if agent_context:
                display_metadata["agent_context"] = agent_context
            display_metadata["trajectory_context"] = compressed_context
        serialized_metadata = json.dumps(display_metadata, indent=2, default=str)
        context_bundle = serialized_metadata

        project_reward_guidelines = ""
        if project_id:
            from marlo.storage.postgres.database import Database
            from marlo.core.config.models import StorageConfig
            import os
            try:
                db_url = os.getenv("DATABASE_URL")
                if db_url:
                    config = StorageConfig(database_url=db_url)
                    db = Database(config)
                    await db.connect()
                    try:
                        chunk = await db.fetch_feedback_chunk(project_id, "reward")
                        if chunk and chunk.strip():
                            project_reward_guidelines = f"\nPROJECT-SPECIFIC EVALUATION GUIDELINES:\n{chunk}\n"
                    finally:
                        await db.disconnect()
            except Exception as exc:
                logger.debug("Could not fetch reward guidelines chunk: %s", exc)

        # Fetch and update session state for stateful evaluation
        session_id = str(execution_context.metadata.get("session_id", "unknown"))
        session_context_text = "No session state available."
        
        try:
            if project_id:
                # Get database connection for session state
                config = StorageConfig(database_url=os.getenv("DATABASE_URL", ""))
                db = Database(config)
                await db.connect()
                try:
                    session_state = await get_session_state(db, session_id)
                    if session_state:
                        session_summary = session_state.get_recent_scores_summary()
                        session_context_text = f"""
Session State Summary:
- Task Count: {session_summary['task_count']}
- Recent Reward Trend: {session_summary['reward_trend']}
- Recent Sentiment Trend: {session_summary['sentiment_trend']}
- Learnings Generated: {session_summary['learnings_count']}
- Recent Scores: {session_summary['recent_reward_scores']}

Session Trajectory Digest:
{session_state.trajectory_digest or "No trajectory digest available."}

Recent Task Summaries:
{json.dumps(session_state.task_summaries, indent=2) if session_state.task_summaries else "No recent task summaries."}
"""
                finally:
                    await db.disconnect()
        except Exception as exc:
            logger.debug("Could not fetch session state: %s", exc)
            session_context_text = f"Session state error: {exc}"

        prompt = SESSION_REWARD_PROMPT.format(
            task=task,
            execution_mode=execution_mode,
            focus_prompt=task_metadata.get("focus_prompt", "N/A"),
            plan=json.dumps(plan_data, indent=2, default=str),
            final_answer=final_answer,
            session_metadata=serialized_metadata,
            session_context=session_context_text,
            project_reward_guidelines=project_reward_guidelines,
        )

        reward_audit: list[dict[str, Any]] = []
        flash_scores: list[float] = []
        flash_results: list[dict[str, Any]] = []

        for temperature in FLASH_TEMPERATURES:
            params = _flash_params(temperature)
            result, error_payload = await _run_single_judge(
                prompt, params, user_id=user_id, project_id=project_id, is_pro_model=False
            )
            if error_payload is not None:
                _record_reward_error(
                    execution_context,
                    stage=error_payload.get("stage", "judge_error"),
                    message=error_payload.get("message", "Judge evaluation failed."),
                    detail=error_payload.get("detail"),
                )
                return None
            score = _coerce_score(result.get("score")) if isinstance(result, dict) else None
            if score is None:
                _record_reward_error(
                    execution_context,
                    stage="missing_score",
                    message="Judge output missing score.",
                    detail=_truncate(str(result)),
                )
                return None
            flash_scores.append(score)
            flash_results.append(result)
            reward_audit.append(
                {
                    "model": params.get("model"),
                    "temperature": params.get("temperature"),
                    "score": score,
                    "principles": result.get("principles") if isinstance(result, dict) else None,
                    "rationale": result.get("rationale") if isinstance(result, dict) else None,
                    "uncertainty": result.get("uncertainty") if isinstance(result, dict) else None,
                    "is_technical_error": result.get("is_technical_error") if isinstance(result, dict) else None,
                }
            )

        variance = pvariance(flash_scores) if len(flash_scores) > 1 else 0.0

        selected_index = 0
        min_uncertainty = float("inf")
        for i, result in enumerate(flash_results):
            uncertainty = result.get("uncertainty", 1.0) if isinstance(result, dict) else 1.0
            if uncertainty < min_uncertainty:
                min_uncertainty = uncertainty
                selected_index = i

        reward_audit.append({
            "variance": variance,
            "escalated": variance >= VARIANCE_THRESHOLD,
            "selected_index": selected_index,
            "selected_uncertainty": min_uncertainty,
        })

        final_result = flash_results[selected_index]
        if variance >= VARIANCE_THRESHOLD:
            params = _pro_params()
            tier1_samples = [
                {"temperature": temperature, "result": result}
                for temperature, result in zip(FLASH_TEMPERATURES, flash_results)
            ]
            tier1_payload = {"context": display_metadata, "samples": tier1_samples}
            tier1_summaries = json.dumps(tier1_payload, indent=2, default=str)
            arbiter_prompt = SESSION_ARBITER_PROMPT.format(
                task=task,
                execution_mode=execution_mode,
                final_answer=final_answer,
                focus_prompt=task_metadata.get("focus_prompt", "N/A"),
                context_bundle=context_bundle,
                tier1_summaries=tier1_summaries,
            )
            result, error_payload = await _run_single_judge(
                arbiter_prompt, params, user_id=user_id, project_id=project_id, is_pro_model=True
            )
            if error_payload is not None:
                _record_reward_error(
                    execution_context,
                    stage=error_payload.get("stage", "escalation_error"),
                    message=error_payload.get("message", "Escalation judge failed."),
                    detail=error_payload.get("detail"),
                )
                return None
            final_result = result
            score = _coerce_score(result.get("score")) if isinstance(result, dict) else None
            reward_audit.append(
                {
                    "model": params.model,
                    "temperature": params.temperature,
                    "score": score,
                    "principles": result.get("principles") if isinstance(result, dict) else None,
                    "rationale": result.get("rationale") if isinstance(result, dict) else None,
                    "uncertainty": result.get("uncertainty") if isinstance(result, dict) else None,
                    "is_technical_error": result.get("is_technical_error") if isinstance(result, dict) else None,
                    "escalated": True,
                }
            )

        execution_context.metadata["task_reward"] = final_result
        execution_context.metadata["task_reward_audit"] = reward_audit
        task_meta = execution_context.metadata.get("task_metadata", {})
        if isinstance(task_meta, dict):
            task_meta.pop("reward_error", None)
            execution_context.metadata["task_metadata"] = task_meta

        # Update session state with new reward information
        try:
            if project_id and isinstance(final_result, dict):
                config = StorageConfig(database_url=os.getenv("DATABASE_URL", ""))
                db = Database(config)
                await db.connect()
                try:
                    # Get current session state
                    session_state = await get_session_state(db, session_id)
                    if session_state:
                        # Create task summary
                        task_summary = await compress_task_to_summary(
                            db, task, final_answer, final_result, task_meta
                        )
                        
                        # Extract scores
                        reward_score = final_result.get("score")
                        sentiment_score = final_result.get("user_sentiment")
                        
                        # Create learning record if new insights generated
                        new_learning = None
                        if final_result.get("rationale") and not final_result.get("is_technical_error"):
                            new_learning = {
                                "task_id": task_meta.get("task_id"),
                                "score": reward_score,
                                "rationale_snippet": final_result.get("rationale", "")[:200],
                                "timestamp": task_meta.get("timestamp")
                            }
                        
                        # Update session state
                        await update_session_state(
                            db, session_state, 
                            task_summary=task_summary,
                            reward_score=reward_score,
                            sentiment_score=sentiment_score,
                            new_learning=new_learning
                        )
                finally:
                    await db.disconnect()
        except Exception as exc:
            logger.warning(f"Failed to update session state: {exc}")

        logger.info("Task Evaluated. Score: %s", final_result.get("score"))
        return final_result

    except Exception as e:
        logger.exception("Error running session evaluation: %s", e)
        _record_reward_error(
            execution_context,
            stage="exception",
            message="Reward evaluation raised an exception.",
            detail=_truncate(str(e)),
        )
        return None


def _flash_params(temperature: float) -> dict[str, Any]:
    return {
        "model": FLASH_MODEL,
        "temperature": temperature,
    }


def _pro_params() -> dict[str, Any]:
    return {
        "model": PRO_MODEL,
        "temperature": 0.0,
    }


def _coerce_score(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


async def _run_single_judge(
    prompt: str,
    params: dict[str, Any],
    *,
    user_id: str | None = None,
    project_id: str | None = None,
    is_pro_model: bool = False,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    client_params = dict(params or {})
    model = client_params.pop("model", None)
    base_client = LLMClient(model=str(model) if model else None, params=client_params)

    if user_id:
        usage_type = USAGE_TYPE_REWARD_PRO if is_pro_model else USAGE_TYPE_REWARD_FLASH
        client: Any = BillingLLMClient(
            base_client,
            user_id=user_id,
            project_id=project_id,
            usage_type=usage_type,
        )
    else:
        client = base_client

    response = await client.acomplete(messages=[{"role": "user", "content": prompt}])
    content = response.content
    if not content:
        logger.warning("Judge returned empty content.")
        return None, {"stage": "empty_response", "message": "Judge returned empty content."}

    cleaned_content = content.replace("```json", "").replace("```", "").strip()
    try:
        reward_result = json.loads(cleaned_content)
    except json.JSONDecodeError:
        logger.warning("Failed to parse Judge output: %s...", content[:100])
        return None, {
            "stage": "parse_error",
            "message": "Failed to parse judge output.",
            "detail": _truncate(cleaned_content),
        }

    if not isinstance(reward_result, dict):
        return None, {
            "stage": "invalid_payload",
            "message": "Judge output was not a JSON object.",
            "detail": _truncate(str(reward_result)),
        }

    return reward_result, None


def _chunk_events(events: list[Any]) -> list[list[Any]]:
    chunks: list[list[Any]] = []
    current: list[Any] = []
    current_tokens = 0.0
    for event in events:
        event_tokens = len(json.dumps(event, default=str)) / 4
        if current and (current_tokens + event_tokens) > CHUNK_TARGET_TOKENS:
            chunks.append(current)
            current = []
            current_tokens = 0.0
        current.append(event)
        current_tokens += event_tokens
    if current:
        chunks.append(current)
    return chunks


async def _compress_trajectory_context(
    trajectory_context: dict[str, Any],
    *,
    user_id: str | None = None,
    project_id: str | None = None,
) -> dict[str, Any]:
    scope = trajectory_context.get("scope")
    events_key = "root_events" if scope == "session" else "events"
    events = trajectory_context.get(events_key)
    if not isinstance(events, list):
        raise ValueError("Trajectory context missing events for compression.")

    chunks = _chunk_events(events)
    base_client = LLMClient(_flash_params(0.0))

    if user_id:
        client: Any = BillingLLMClient(
            base_client,
            user_id=user_id,
            project_id=project_id,
            usage_type=USAGE_TYPE_REWARD_FLASH,
        )
    else:
        client = base_client

    summaries: list[dict[str, Any]] = []
    for index, chunk in enumerate(chunks):
        summary = await _summarize_chunk(client, chunk)
        summaries.append(
            {
                "chunk_index": index,
                "event_count": len(chunk),
                "first_event_id": chunk[0].get("event_id") if chunk else None,
                "last_event_id": chunk[-1].get("event_id") if chunk else None,
                "summary": summary,
            }
        )

    compressed = dict(trajectory_context)
    compressed.pop(events_key, None)
    summary_key = "root_event_summaries" if scope == "session" else "event_summaries"
    compressed[summary_key] = summaries
    compressed["compression"] = {
        "model": FLASH_MODEL,
        "chunk_count": len(chunks),
        "chunk_target_tokens": CHUNK_TARGET_TOKENS,
    }
    compressed["event_count"] = len(events)
    return compressed


async def _summarize_chunk(client: Any, chunk: list[Any]) -> dict[str, Any]:
    events_json = json.dumps(chunk, default=str)
    prompt = TRAJECTORY_COMPRESSION_PROMPT.format(events_json=events_json)
    response = await client.acomplete(
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    content = response.content
    if not content:
        raise ValueError("Chunk summary returned empty content.")
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError("Chunk summary parse error.") from exc


def _estimate_tokens(payload: dict[str, Any]) -> float:
    serialized = json.dumps(payload, default=str)
    return len(serialized) / 4


def _sanitize_task_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(metadata, dict):
        return {}
    allowed_keys = {
        "token_usage",
        "trajectory_persist_error",
        "context_memory_state",
    }
    return {key: metadata[key] for key in allowed_keys if key in metadata}

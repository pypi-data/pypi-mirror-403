"""Learning generator for structured learning objects."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List

from marlo.core.interfaces import LLMClientProtocol
from marlo.learning.generation.prompts import LEARNING_GENERATION_PROMPT
from marlo.billing import BillingLLMClient, USAGE_TYPE_LEARNING

logger = logging.getLogger(__name__)


@dataclass
class LearningInsight:
    learning: str
    expected_outcome: str
    basis: str
    confidence: float
    session_relevance: float = 0.5


@dataclass
class LearningGenerationResult:
    action: str  # "skip" | "update" | "create"
    reason: str
    update_learning_id: str | None
    insights: List[LearningInsight]


class LearningGenerator:
    def __init__(self, client: LLMClientProtocol) -> None:
        self.client = client

    async def generate_learnings(
        self,
        reward_rationale: str,
        metadata: Dict[str, Any],
        existing_learnings: List[Dict[str, Any]] | None = None,
        *,
        user_id: str | None = None,
        project_id: str | None = None,
    ) -> LearningGenerationResult:
        if not reward_rationale:
            return LearningGenerationResult(
                action="skip",
                reason="No reward rationale provided",
                update_learning_id=None,
                insights=[],
            )

        payload = {
            "reward_rationale": reward_rationale,
            "existing_learnings": existing_learnings or [],
            "agent": metadata.get("agent"),
            "tools": metadata.get("tools"),
            "session_learnings": metadata.get("session_learnings", []),
            "session_context": metadata.get("session_context", "No session context available."),
        }

        project_learning_guidelines = ""
        if project_id:
            try:
                from marlo.storage.postgres.database import Database
                from marlo.core.config.models import StorageConfig
                import os
                db_url = os.getenv("DATABASE_URL")
                if db_url:
                    config = StorageConfig(database_url=db_url)
                    db = Database(config)
                    await db.connect()
                    try:
                        chunk = await db.fetch_feedback_chunk(project_id, "learning")
                        if chunk and chunk.strip():
                            project_learning_guidelines = f"\nPROJECT-SPECIFIC LEARNING GUIDELINES:\n{chunk}\n"
                    finally:
                        await db.disconnect()
            except Exception as exc:
                logger.debug("Could not fetch learning guidelines chunk: %s", exc)

        system_prompt = LEARNING_GENERATION_PROMPT.format(
            project_learning_guidelines=project_learning_guidelines,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(payload, default=str)},
        ]

        client: Any = self.client
        if user_id:
            client = BillingLLMClient(
                self.client,
                user_id=user_id,
                project_id=project_id,
                usage_type=USAGE_TYPE_LEARNING,
            )

        try:
            response = await client.acomplete(
                messages,
                response_format={"type": "json_object"},
            )
            return _parse_generation_response(response.content)
        except Exception as exc:
            logger.warning("Learning generation failed: %s", exc)
            return LearningGenerationResult(
                action="skip",
                reason=f"Generation error: {exc}",
                update_learning_id=None,
                insights=[],
            )


def _parse_generation_response(content: str) -> LearningGenerationResult:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return LearningGenerationResult(
            action="skip",
            reason="Failed to parse LLM response",
            update_learning_id=None,
            insights=[],
        )

    if not isinstance(parsed, dict):
        return LearningGenerationResult(
            action="skip",
            reason="Invalid response format",
            update_learning_id=None,
            insights=[],
        )

    action = parsed.get("action", "skip")
    if action not in ("skip", "update", "create", "strengthen"):
        action = "skip"

    reason = parsed.get("reason", "")
    if not isinstance(reason, str):
        reason = str(reason)

    update_learning_id = parsed.get("update_learning_id")
    if update_learning_id is not None and not isinstance(update_learning_id, str):
        update_learning_id = str(update_learning_id)

    insights: List[LearningInsight] = []
    raw_learnings = parsed.get("learnings", [])
    if isinstance(raw_learnings, list):
        for item in raw_learnings:
            if not isinstance(item, dict):
                continue
            insight = _coerce_insight(item)
            if insight.learning:
                insights.append(insight)

    return LearningGenerationResult(
        action=action,
        reason=reason,
        update_learning_id=update_learning_id,
        insights=insights,
    )


def _coerce_insight(item: Dict[str, Any]) -> LearningInsight:
    learning = item.get("learning", "")
    if not isinstance(learning, str):
        learning = str(learning)

    expected_outcome = item.get("expected_outcome", "")
    if not isinstance(expected_outcome, str):
        expected_outcome = str(expected_outcome)

    basis = item.get("basis", "")
    if not isinstance(basis, str):
        basis = str(basis)

    confidence = item.get("confidence", 0.0)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0

    session_relevance = item.get("session_relevance", 0.5)
    try:
        session_relevance = float(session_relevance)
    except (TypeError, ValueError):
        session_relevance = 0.5

    return LearningInsight(
        learning=learning.strip(),
        expected_outcome=expected_outcome.strip(),
        basis=basis.strip(),
        confidence=confidence,
        session_relevance=session_relevance,
    )


__all__ = ["LearningGenerator", "LearningGenerationResult", "LearningInsight"]

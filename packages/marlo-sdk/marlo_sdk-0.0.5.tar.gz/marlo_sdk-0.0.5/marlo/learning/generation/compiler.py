"""Learning object compilation pipeline."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

from marlo.learning.generation.generator import LearningInsight

_WHITESPACE = re.compile(r"\s+")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


@dataclass
class LearningObjectCandidate:
    learning_id: str
    version: int
    status: str
    agent_id: str
    learning: str
    expected_outcome: str
    basis: str
    confidence: float
    evidence: Dict[str, Any]


class LearningCompiler:
    def __init__(self, version: int = 1) -> None:
        self.version = max(int(version), 1)

    def compile(
        self,
        insights: List[LearningInsight],
        *,
        agent_id: str,
    ) -> List[Dict[str, Any]]:
        if not insights:
            return []

        candidates = [insight.learning for insight in insights if isinstance(insight.learning, dict)]
        merged = _merge_candidates(candidates, agent_id=agent_id, version=self.version)
        return [candidate.__dict__ for candidate in merged]


def _merge_candidates(
    candidates: Iterable[Dict[str, Any]],
    *,
    agent_id: str,
    version: int,
) -> List[LearningObjectCandidate]:
    grouped: dict[str, LearningObjectCandidate] = {}
    for item in candidates:
        learning_raw = item.get("learning")
        expected_outcome_raw = item.get("expected_outcome")
        basis_raw = item.get("basis")
        learning = str(learning_raw).strip() if learning_raw is not None else ""
        expected_outcome = str(expected_outcome_raw).strip() if expected_outcome_raw is not None else ""
        basis = str(basis_raw).strip() if basis_raw is not None else ""
        if not learning or not expected_outcome or not basis:
            continue
        confidence = _coerce_float(item.get("confidence"))
        rationale = _normalise_text(item.get("rationale"))
        signature = _signature(agent_id, learning, expected_outcome, basis)
        evidence = {"rationale_snippets": [rationale]} if rationale else {"rationale_snippets": []}

        existing = grouped.get(signature)
        if existing is None:
            grouped[signature] = LearningObjectCandidate(
                learning_id=signature,
                version=version,
                status="pending",
                agent_id=agent_id,
                learning=learning,
                expected_outcome=expected_outcome,
                basis=basis,
                confidence=confidence,
                evidence=evidence,
            )
            continue

        if confidence > existing.confidence:
            existing.confidence = confidence
        _merge_evidence(existing.evidence, evidence)
    return list(grouped.values())


def _signature(
    agent_id: str,
    learning: str,
    expected_outcome: str,
    basis: str,
) -> str:
    parts = [
        agent_id,
        _normalise_text(learning),
        _normalise_text(expected_outcome),
        _normalise_text(basis),
    ]
    digest = hashlib.sha256("||".join(parts).encode("utf-8")).hexdigest()
    return f"learning-{digest[:12]}"


def _merge_evidence(target: Dict[str, Any], incoming: Dict[str, Any]) -> None:
    snippets = target.setdefault("rationale_snippets", [])
    for snippet in incoming.get("rationale_snippets", []):
        if snippet and snippet not in snippets:
            snippets.append(snippet)


def _normalise_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = _NON_ALNUM.sub(" ", text)
    text = _WHITESPACE.sub(" ", text)
    return text.strip()


def _coerce_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


__all__ = ["LearningCompiler", "LearningObjectCandidate"]

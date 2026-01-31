"""Learning lifecycle rules for promotion, demotion, and pruning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DEFAULT_METRICS_WINDOW = 50
MIN_PROMOTION_SAMPLES = 10
MIN_REWARD_DELTA = 0.01
MAX_FAILURE_DELTA = 0.05
MAX_TOKEN_DELTA = 50.0
PRUNE_MIN_SAMPLES = 20
MIN_EFFECT_DELTA = 0.005


@dataclass(frozen=True)
class StatusDecision:
    new_status: str
    reason: str


def assess_pruning(status: str, metrics: dict[str, Any]) -> StatusDecision | None:
    return None


def assess_promotion(status: str, metrics: dict[str, Any]) -> StatusDecision | None:
    return None


def _exceeds_failure_delta(value: Any) -> bool:
    if value is None:
        return False
    try:
        return float(value) > MAX_FAILURE_DELTA
    except (TypeError, ValueError):
        return False


def _exceeds_token_delta(value: Any) -> bool:
    if value is None:
        return False
    try:
        return float(value) > MAX_TOKEN_DELTA
    except (TypeError, ValueError):
        return False


__all__ = [
    "StatusDecision",
    "assess_promotion",
    "assess_pruning",
    "DEFAULT_METRICS_WINDOW",
    "MIN_PROMOTION_SAMPLES",
]

"""Trace schemas for runtime sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MarloRewardBreakdown:
    score: float | None = None
    judges: list[dict[str, Any]] | None = None
    rationale: str | None = None
    uncertainty: float | None = None
    is_technical_error: bool | None = None
    raw: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> MarloRewardBreakdown:
        if payload is None:
            return cls()
        if isinstance(payload, cls):
            return payload
        if not isinstance(payload, dict):
            return cls()
        return cls(
            score=payload.get("score"),
            judges=payload.get("judges") or payload.get("samples"),
            rationale=payload.get("rationale"),
            uncertainty=payload.get("uncertainty"),
            is_technical_error=payload.get("is_technical_error"),
            raw=dict(payload) if isinstance(payload, dict) else None,
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.score is not None:
            data["score"] = self.score
        if self.uncertainty is not None:
            data["uncertainty"] = self.uncertainty
        if self.rationale is not None:
            data["rationale"] = self.rationale
        if self.is_technical_error is not None:
            data["is_technical_error"] = self.is_technical_error
        if self.judges is not None:
            data["judges"] = self.judges
        if self.raw is not None:
            data["raw"] = self.raw
        return data


@dataclass
class MarloStepTrace:
    step_id: int
    description: str = ""
    trace: str = ""
    output: str = ""
    reward: MarloRewardBreakdown | dict[str, Any] | None = None
    tool: str | None = None
    tool_params: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    validation: dict[str, Any] = field(default_factory=dict)
    attempts: int = 1
    guidance: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, Any] | None = None
    deliverable: Any = None
    runtime: Any = None
    depends_on: list[Any] | None = None

    def __post_init__(self) -> None:
        if isinstance(self.reward, dict):
            self.reward = MarloRewardBreakdown.from_dict(self.reward)

    @property
    def attempt_history(self) -> list[dict[str, Any]] | None:
        history = self.metadata.get("attempt_history")
        return history if isinstance(history, list) else None


@dataclass
class MarloSessionTrace:
    task: str
    final_answer: str
    plan: dict[str, Any] | None
    steps: list[MarloStepTrace] = field(default_factory=list)
    session_metadata: dict[str, Any] = field(default_factory=dict)
    session_reward: dict[str, Any] | None = None
    trajectory_events: list[dict[str, Any]] | None = None
    learning: str | None = None
    learning_history: dict[str, Any] | None = None
    adaptive_summary: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if hasattr(self.plan, "model_dump"):
            try:
                self.plan = self.plan.model_dump()
            except Exception:
                pass

    @property
    def learning_key(self) -> str | None:
        value = self.session_metadata.get("learning_key") if isinstance(self.session_metadata, dict) else None
        return str(value) if value is not None else None

    @property
    def reward_summary(self) -> dict[str, Any] | None:
        summary = self.session_metadata.get("reward_summary") if isinstance(self.session_metadata, dict) else None
        return summary if isinstance(summary, dict) else None

    @property
    def drift(self) -> dict[str, Any] | None:
        details = self.session_metadata.get("drift") if isinstance(self.session_metadata, dict) else None
        return details if isinstance(details, dict) else None

    @property
    def drift_alert(self) -> bool | None:
        alert = self.session_metadata.get("drift_alert") if isinstance(self.session_metadata, dict) else None
        return bool(alert) if alert is not None else None

    @property
    def triage_dossier(self) -> dict[str, Any] | None:
        dossier = self.session_metadata.get("triage_dossier") if isinstance(self.session_metadata, dict) else None
        return dossier if isinstance(dossier, dict) else None

    @property
    def reward_audit(self) -> list[dict[str, Any]] | None:
        audit = self.session_metadata.get("reward_audit") if isinstance(self.session_metadata, dict) else None
        return audit if isinstance(audit, list) else None


__all__ = [
    "MarloRewardBreakdown",
    "MarloSessionTrace",
    "MarloStepTrace",
]

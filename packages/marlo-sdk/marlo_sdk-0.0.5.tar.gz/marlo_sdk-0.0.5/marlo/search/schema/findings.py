"""Findings and analysis result dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class WeightedFact:
    """A fact extracted from trajectory analysis with importance score."""

    content: str
    importance: float  # 0.0-1.0
    source_session_id: int
    source_event_id: int | str
    event_type: str
    source_task_id: int | None = None
    agent_id: str | None = None
    created_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "content": self.content,
            "importance": self.importance,
            "source_session_id": self.source_session_id,
            "source_event_id": self.source_event_id,
            "source_task_id": self.source_task_id,
            "event_type": self.event_type,
            "agent_id": self.agent_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WeightedFact:
        """Create from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        return cls(
            content=data["content"],
            importance=data["importance"],
            source_session_id=data["source_session_id"],
            source_event_id=data["source_event_id"],
            source_task_id=data.get("source_task_id"),
            event_type=data["event_type"],
            agent_id=data.get("agent_id"),
            created_at=created_at,
        )


@dataclass
class AnalysisResult:
    """Result from analyzing a chunk of trajectory events."""

    facts: list[WeightedFact] = field(default_factory=list)
    patterns: list[str] = field(default_factory=list)
    suggested_refinements: list[str] = field(default_factory=list)
    events_processed: int = 0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "facts": [f.to_dict() for f in self.facts],
            "patterns": self.patterns,
            "suggested_refinements": self.suggested_refinements,
            "events_processed": self.events_processed,
            "error": self.error,
        }


@dataclass
class SynthesisResult:
    """Final synthesized answer from the search."""

    answer: str
    confidence: float  # 0.0-1.0
    key_findings: list[str] = field(default_factory=list)
    evidence_citations: list[dict[str, Any]] = field(default_factory=list)
    patterns_discovered: list[str] = field(default_factory=list)
    data_coverage: dict[str, Any] = field(default_factory=dict)
    limitations: str | None = None
    suggested_follow_ups: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "answer": self.answer,
            "confidence": self.confidence,
            "key_findings": self.key_findings,
            "evidence_citations": self.evidence_citations,
            "patterns_discovered": self.patterns_discovered,
            "data_coverage": self.data_coverage,
            "limitations": self.limitations,
            "suggested_follow_ups": self.suggested_follow_ups,
        }

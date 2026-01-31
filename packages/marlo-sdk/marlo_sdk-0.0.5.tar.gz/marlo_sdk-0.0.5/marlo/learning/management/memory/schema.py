"""Memory schema for trace-based context summarization."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class WeightedFact:
    content: str
    importance: float
    source_event_id: str


@dataclass(slots=True)
class StructuredPlan:
    objective: str
    search_targets: List[str] = field(default_factory=list)
    ignore_patterns: List[str] = field(default_factory=list)


__all__ = ["StructuredPlan", "WeightedFact"]

"""Context memory provider base types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol


@dataclass(slots=True)
class ContextRequest:
    task: str
    trace_history: List[Any] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContextProvider(Protocol):
    async def provide(self, request: ContextRequest) -> Dict[str, Any]:
        ...


__all__ = ["ContextRequest", "ContextProvider"]

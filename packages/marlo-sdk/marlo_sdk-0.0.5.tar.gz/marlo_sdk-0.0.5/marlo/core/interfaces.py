"""Protocol definitions for dependency injection."""

from __future__ import annotations

from typing import Any, Dict, Protocol


class LLMClientProtocol(Protocol):
    async def acomplete(
        self,
        messages: list[dict[str, Any]],
        response_format: Dict[str, Any] | None = None,
    ) -> Any:
        ...


__all__ = ["LLMClientProtocol"]

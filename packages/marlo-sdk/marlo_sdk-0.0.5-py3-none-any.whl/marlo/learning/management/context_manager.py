"""Simple context manager for trace-based memory providers."""

from __future__ import annotations

from typing import Any

from marlo.learning.management.memory.base import ContextProvider, ContextRequest


class MarloContextManager:
    def __init__(self, providers: list[ContextProvider]) -> None:
        self.providers = providers

    async def get_context(
        self,
        task: str,
        trace_history: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        request = ContextRequest(task=task, trace_history=trace_history or [], metadata=metadata or {})
        results: dict[str, Any] = {}
        for provider in self.providers:
            payload = await provider.provide(request)
            if isinstance(payload, dict):
                results.update(payload)
        return results


__all__ = ["MarloContextManager"]

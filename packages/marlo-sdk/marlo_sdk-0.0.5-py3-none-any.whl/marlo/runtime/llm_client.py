"""LLM client wrapper for reward and learning pipelines."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Optional

_DEFAULT_MODEL = "gemini-3-flash-preview"
_CLIENT: Any | None = None


@dataclass(slots=True)
class LLMResponse:
    content: str
    raw: Any | None = None
    usage: Dict[str, int] | None = None
    model: str | None = None


class LLMClient:
    def __init__(self, *, model: str | None = None, params: Dict[str, Any] | None = None) -> None:
        if _CLIENT is None:
            raise RuntimeError("LLM client is not registered.")
        self._client = _CLIENT
        self._model = model or _DEFAULT_MODEL
        self._params = dict(params or {})

    async def acomplete(
        self,
        messages: list[dict[str, Any]],
        response_format: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        payload = {
            "messages": messages,
            "response_format": response_format,
            "model": self._model,
        }
        payload.update(self._params)
        client = self._client
        if hasattr(client, "acomplete"):
            response = await client.acomplete(**payload)
            return _normalize_response(response)
        if hasattr(client, "complete"):
            response = await asyncio.to_thread(client.complete, **payload)
            return _normalize_response(response)
        if callable(client):
            response = client(**payload)
            if asyncio.iscoroutine(response):
                response = await response
            return _normalize_response(response)
        raise RuntimeError("LLM client does not support completion calls.")


def _normalize_response(response: Any) -> LLMResponse:
    if isinstance(response, LLMResponse):
        return response
    if hasattr(response, "content"):
        content = getattr(response, "content")
        usage = getattr(response, "usage", None)
        model = getattr(response, "model", None)
        return LLMResponse(
            content=str(content) if content is not None else "",
            raw=response,
            usage=usage,
            model=model,
        )
    if isinstance(response, dict):
        content = response.get("content")
        usage = response.get("usage")
        model = response.get("model")
        return LLMResponse(
            content=str(content) if content is not None else "",
            raw=response,
            usage=usage,
            model=model,
        )
    return LLMResponse(content=str(response), raw=response)


def register_llm_client(client: Any, *, default_model: str | None = None) -> None:
    global _CLIENT, _DEFAULT_MODEL
    _CLIENT = client
    if default_model:
        _DEFAULT_MODEL = default_model


def get_llm_client() -> LLMClient:
    """Get the registered LLM client wrapper."""
    if _CLIENT is None:
        raise RuntimeError("LLM client is not registered. Call register_llm_client first.")
    return LLMClient()


__all__ = ["LLMClient", "LLMResponse", "register_llm_client", "get_llm_client"]

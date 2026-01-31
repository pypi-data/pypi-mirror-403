"""Gemini client wrapper for reward and learning pipelines."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import time
from typing import Any, Dict, Iterable, List

import google.genai as genai

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
BASE_DELAY = 1.0
MAX_DELAY = 30.0


def _normalize_model(model: str | None) -> str:
    if not isinstance(model, str) or not model.strip():
        raise ValueError("model is required for Gemini client")
    value = model.strip()
    if "/" in value:
        value = value.split("/")[-1]
    return value


def _stringify_message(content: Any) -> str:
    if isinstance(content, str):
        return content
    return json.dumps(content, default=str)


def _messages_to_contents(messages: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    contents: list[dict[str, Any]] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        role = message.get("role") or "user"
        content = _stringify_message(message.get("content"))
        gemini_role = "model" if role == "assistant" else "user"
        contents.append({"role": gemini_role, "parts": [{"text": content}]})
    if not contents:
        raise ValueError("messages must contain at least one entry")
    return contents


def _extract_sdk_text(response: Any) -> str:
    text = getattr(response, "text", None)
    if text:
        return str(text)
    candidates = getattr(response, "candidates", None)
    if isinstance(candidates, list) and candidates:
        content = getattr(candidates[0], "content", None)
        parts = getattr(content, "parts", None)
        if isinstance(parts, list) and parts:
            part_text = getattr(parts[0], "text", None)
            if part_text is not None:
                return str(part_text)
    raise RuntimeError("Gemini response missing content")


def _extract_usage_metadata(response: Any) -> Dict[str, int]:
    """Extract token usage from Gemini response.

    For thinking models, reasoning tokens are billed at output token rates,
    so we add them to output_tokens for billing purposes.
    """
    usage_metadata = getattr(response, "usage_metadata", None)
    if usage_metadata is None:
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    input_tokens = getattr(usage_metadata, "prompt_token_count", 0) or 0
    candidates_tokens = getattr(usage_metadata, "candidates_token_count", 0) or 0
    thinking_tokens = getattr(usage_metadata, "thinking_token_count", 0) or 0
    total_tokens = getattr(usage_metadata, "total_token_count", 0) or 0

    # Include thinking tokens in output for billing (reasoning is billed as output)
    output_tokens = candidates_tokens + thinking_tokens

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "thinking_tokens": thinking_tokens,
        "total_tokens": total_tokens,
    }


def _is_retryable_error(error: Exception) -> bool:
    """Check if an error is retryable (503, 429, etc.)."""
    error_str = str(error).lower()
    retryable_indicators = [
        "503",
        "overloaded",
        "unavailable",
        "429",
        "rate limit",
        "quota",
        "resource exhausted",
        "too many requests",
        "temporarily unavailable",
    ]
    return any(indicator in error_str for indicator in retryable_indicators)


def _calculate_delay(attempt: int) -> float:
    """Calculate delay with exponential backoff and jitter."""
    delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
    jitter = random.uniform(0, delay * 0.1)
    return delay + jitter


class GeminiClient:
    def __init__(self, *, api_key: str | None = None) -> None:
        resolved_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not resolved_key:
            raise RuntimeError("GOOGLE_API_KEY is required to use the Gemini client.")
        self._client = genai.Client(api_key=resolved_key)

    def complete(
        self,
        *,
        messages: list[dict[str, Any]],
        model: str,
        response_format: Dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Dict[str, str]:
        model_name = _normalize_model(model)
        contents = _messages_to_contents(messages)
        generation_config: dict[str, Any] = {}
        temperature = kwargs.get("temperature")
        if temperature is not None:
            generation_config["temperature"] = float(temperature)
        if response_format and response_format.get("type") == "json_object":
            generation_config["response_mime_type"] = "application/json"

        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                response = self._client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=generation_config or None,
                )

                usage = _extract_usage_metadata(response)
                return {
                    "content": _extract_sdk_text(response),
                    "usage": usage,
                    "model": model_name,
                }

            except Exception as e:
                last_error = e
                if _is_retryable_error(e) and attempt < MAX_RETRIES - 1:
                    delay = _calculate_delay(attempt)
                    logger.warning(f"Retryable error, retrying in {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    raise

        raise last_error or RuntimeError("Request failed after retries")

    async def acomplete(
        self,
        *,
        messages: list[dict[str, Any]],
        model: str | None = None,
        response_format: Dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Dict[str, str]:
        model_name = _normalize_model(model or kwargs.get("model"))
        contents = _messages_to_contents(messages)
        generation_config: dict[str, Any] = {}
        temperature = kwargs.get("temperature")
        if temperature is not None:
            generation_config["temperature"] = float(temperature)
        if response_format and response_format.get("type") == "json_object":
            generation_config["response_mime_type"] = "application/json"

        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                response = await asyncio.to_thread(
                    self._client.models.generate_content,
                    model=model_name,
                    contents=contents,
                    config=generation_config or None,
                )

                usage = _extract_usage_metadata(response)
                return {
                    "content": _extract_sdk_text(response),
                    "usage": usage,
                    "model": model_name,
                }

            except Exception as e:
                last_error = e
                if _is_retryable_error(e) and attempt < MAX_RETRIES - 1:
                    delay = _calculate_delay(attempt)
                    logger.warning(f"Retryable error, retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                else:
                    raise

        raise last_error or RuntimeError("Async request failed after retries")


__all__ = ["GeminiClient"]

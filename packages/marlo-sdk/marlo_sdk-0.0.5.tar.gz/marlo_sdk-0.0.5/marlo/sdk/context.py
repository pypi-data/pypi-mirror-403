from __future__ import annotations

import logging
import uuid
from typing import Any

from marlo.core.digest import json_digest
from marlo.sdk.client import get_client, is_enabled
from marlo.sdk.ids import generate_id
from marlo.sdk.registry import get_agent, mark_agent_sent, needs_resend

logger = logging.getLogger(__name__)


def task(thread_id: str, agent: str, thread_name: str | None = None) -> TaskContext:
    return TaskContext(thread_id, agent, thread_name)


def _compute_session_id(project_id: str, thread_id: str) -> int:
    digest = json_digest(f"{project_id}:{thread_id}")
    # Mask to 63 bits to fit in signed int64 (PostgreSQL bigint)
    return int(digest[:16], 16) & 0x7FFFFFFFFFFFFFFF


def _generate_id() -> int:
    return generate_id()


def _generate_invocation_id() -> str:
    return str(uuid.uuid4())


class TaskContext:
    def __init__(
        self,
        thread_id: str,
        agent: str,
        thread_name: str | None,
        parent: TaskContext | None = None,
    ) -> None:
        self._thread_id = thread_id
        self._agent_name = agent
        self._thread_name = thread_name
        self._parent = parent
        self._task_id: int | None = None
        self._session_id: int | None = None
        self._invocation_id: str | None = None
        self._input_text: str | None = None
        self._output_text: str | None = None
        self._error_message: str | None = None
        self._events: list[dict] = []
        self._total_prompt_tokens: int = 0
        self._total_completion_tokens: int = 0
        self._total_reasoning_tokens: int = 0
        self._llm_call_count: int = 0

    def __enter__(self) -> TaskContext:
        try:
            client = get_client()
            project_id = client.scope.get("project_id", "") if client else ""
            self._session_id = _compute_session_id(project_id, self._thread_id)
            self._task_id = _generate_id()
            self._invocation_id = _generate_invocation_id()

            if needs_resend(self._agent_name):
                agent_def = get_agent(self._agent_name)
                if agent_def is not None:
                    self._emit(
                        "agent_definition",
                        {
                            "name": agent_def.name,
                            "system_prompt": agent_def.system_prompt,
                            "tool_definitions": agent_def.tools,
                            "mcp_definitions": agent_def.mcp,
                            "model_config": agent_def.model_config,
                            "definition_hash": agent_def.definition_hash,
                        },
                    )
                    mark_agent_sent(self._agent_name)
        except Exception as exc:
            logger.warning("TaskContext enter failed: %s", exc)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> bool:
        try:
            status = "error" if exc_type or self._error_message else "success"
            payload: dict[str, Any] = {"status": status}
            if self._output_text is not None:
                payload["final_answer"] = self._output_text
            if self._error_message is not None:
                payload["error"] = self._error_message

            # Include aggregated token usage for dashboard stats
            total_tokens = (
                self._total_prompt_tokens
                + self._total_completion_tokens
                + self._total_reasoning_tokens
            )
            if total_tokens > 0:
                payload["token_usage"] = {
                    "prompt_tokens": self._total_prompt_tokens,
                    "completion_tokens": self._total_completion_tokens,
                    "reasoning_tokens": self._total_reasoning_tokens,
                    "total_tokens": total_tokens,
                    "calls": self._llm_call_count,
                }

            self._emit("task_end", payload)
            self._flush()
        except Exception as exc:
            logger.warning("TaskContext exit failed: %s", exc)
        return False

    def input(self, text: str) -> None:
        try:
            self._input_text = text
            metadata: dict[str, Any] = {"thread_id": self._thread_id}
            if self._thread_name is not None:
                metadata["thread_name"] = self._thread_name
            self._emit("task_start", {"task": text, "metadata": metadata})
        except Exception as exc:
            logger.warning("TaskContext input failed: %s", exc)

    def output(self, text: str) -> None:
        try:
            self._output_text = text
        except Exception as exc:
            logger.warning("TaskContext output failed: %s", exc)

    def tool(
        self,
        name: str,
        input: dict,
        output: Any,
        error: str | None = None,
    ) -> None:
        try:
            payload: dict[str, Any] = {
                "tool_name": name,
                "input": input,
                "output": output,
            }
            if error is not None:
                payload["error"] = error
            self._emit("tool_call", payload)
        except Exception as exc:
            logger.warning("TaskContext tool failed: %s", exc)

    def reasoning(self, text: str) -> None:
        try:
            self._emit("log", {"reasoning": text})
        except Exception as exc:
            logger.warning("TaskContext reasoning failed: %s", exc)

    def llm(
        self,
        *,
        model: str,
        usage: dict,
        messages: list | None = None,
        response: str | None = None,
    ) -> None:
        try:
            if messages is None:
                logger.warning("llm() called without messages")
            if response is None:
                logger.warning("llm() called without response")

            # Aggregate token usage
            if isinstance(usage, dict):
                prompt = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
                completion = usage.get("completion_tokens") or usage.get("output_tokens") or 0
                reasoning = usage.get("reasoning_tokens") or usage.get("thinking_tokens") or 0
                self._total_prompt_tokens += int(prompt) if prompt else 0
                self._total_completion_tokens += int(completion) if completion else 0
                self._total_reasoning_tokens += int(reasoning) if reasoning else 0
                self._llm_call_count += 1

            payload: dict[str, Any] = {"model": model, "usage": usage}
            if messages is not None:
                payload["messages"] = messages
            if response is not None:
                payload["response"] = response
            self._emit("llm_call", payload)
        except Exception as exc:
            logger.warning("TaskContext llm failed: %s", exc)

    def error(self, message: str) -> None:
        try:
            self._error_message = message
            self._emit("error", {"error": message})
        except Exception as exc:
            logger.warning("TaskContext error failed: %s", exc)

    def child(self, agent: str) -> TaskContext:
        return TaskContext(self._thread_id, agent, self._thread_name, parent=self)

    def get_learnings(self) -> dict | None:
        try:
            client = get_client()
            if client is None:
                return None
            return client.fetch_learnings(self._agent_name)
        except Exception as exc:
            logger.warning("TaskContext get_learnings failed: %s", exc)
            return None

    def _emit(self, event_type: str, payload: dict) -> None:
        agent_def = get_agent(self._agent_name)
        agent_id = agent_def.name if agent_def else self._agent_name
        parent_agent_id = self._parent._agent_name if self._parent else None

        event = {
            "event_id": str(uuid.uuid4()),
            "run_id": self._session_id,
            "agent_id": agent_id,
            "parent_agent_id": parent_agent_id,
            "invocation_id": self._invocation_id,
            "task_id": self._task_id,
            "event_type": event_type,
            "payload": payload,
        }
        self._events.append(event)

    def _flush(self) -> None:
        """Send events to background queue. Non-blocking."""
        client = get_client()
        if client is None or not is_enabled():
            self._events.clear()
            return
        try:
            # Just enqueue events - background thread handles sending
            # This is non-blocking and safe for async contexts
            client.send_events(self._events)
        except Exception as exc:
            logger.warning("TaskContext flush failed: %s", exc)
        finally:
            self._events.clear()


__all__ = ["task", "TaskContext"]

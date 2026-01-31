"""Decorators and helpers for agent-aware trajectory capture."""

from __future__ import annotations

import asyncio
import functools
import inspect
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, TypeVar

from marlo.core.digest import json_digest
from marlo.core.ids import agent_id_for_name, require_project_id
from marlo.trajectories.capture.context import (
    ExecutionContext,
    ensure_run_id,
    get_run_id,
    get_current_agent_id,
    require_agent_context,
    reset_agent_context,
    reset_run_id,
    set_agent_context,
)
from marlo.trajectories.schema.agents import AgentDefinition
from marlo.trajectories.schema.events import TrajectoryEvent, TrajectoryEventType

T = TypeVar("T", bound=Callable[..., Any])


def _validate_agent_definition_inputs(
    *,
    system_prompt: Any,
    tool_definitions: Any,
    mcp_definitions: Any,
    model_config: Any,
) -> None:
    if system_prompt is None or tool_definitions is None or mcp_definitions is None or model_config is None:
        raise ValueError(
            "system_prompt, tool_definitions, mcp_definitions, and model_config are required for agent tracing."
        )


def _emit_event(event_type: TrajectoryEventType | str, payload: Dict[str, Any] | None = None) -> None:
    run_id, agent_id, parent_agent_id, invocation_id = require_agent_context()
    task_id = _resolve_task_id()
    event = TrajectoryEvent(
        run_id=run_id,
        agent_id=agent_id,
        parent_agent_id=parent_agent_id,
        invocation_id=invocation_id,
        task_id=task_id,
        event_type=event_type,
        payload=payload,
    )
    ExecutionContext.get().emit(event.to_dict())


def register_agent_definition(
    *,
    name: str,
    system_prompt: str,
    tool_definitions: Any,
    mcp_definitions: Any,
    model_config: Dict[str, Any],
) -> None:
    _validate_agent_definition_inputs(
        system_prompt=system_prompt,
        tool_definitions=tool_definitions,
        mcp_definitions=mcp_definitions,
        model_config=model_config,
    )
    _, agent_id, parent_agent_id, _ = require_agent_context()
    definition = AgentDefinition(
        agent_id=agent_id,
        parent_agent_id=parent_agent_id,
        name=name,
        system_prompt=system_prompt,
        tool_definitions=tool_definitions,
        mcp_definitions=mcp_definitions,
        model_config=model_config,
        created_at=datetime.now(timezone.utc),
    )
    payload = definition.to_dict()
    definition_hash = json_digest(
        {
            "name": name,
            "system_prompt": system_prompt,
            "tool_definitions": tool_definitions,
            "mcp_definitions": mcp_definitions,
            "model_config": model_config,
        }
    )
    payload["definition_hash"] = definition_hash
    ExecutionContext.get().metadata["definition_hash"] = definition_hash
    _emit_event(TrajectoryEventType.AGENT_DEFINITION, payload)


def emit_llm_call(
    *,
    messages: Any,
    model_params: Dict[str, Any],
    response: Any,
    usage: Dict[str, Any] | None = None,
    reasoning: Dict[str, Any] | None = None,
    error: Optional[str] = None,
    telemetry_error: list[str] | None = None,
) -> None:
    payload: Dict[str, Any] = {
        "messages": messages,
        "model_params": model_params,
        "response": response,
        "usage": usage if isinstance(usage, dict) else {},
        "reasoning": reasoning if isinstance(reasoning, dict) else {},
    }
    if error is not None:
        payload["error"] = error
    if telemetry_error:
        payload["telemetry_error"] = telemetry_error
    _emit_event(TrajectoryEventType.LLM_CALL, payload)


def emit_tool_call(
    *,
    tool_name: str,
    tool_input: Any,
    tool_output: Any,
    error: Optional[str] = None,
) -> None:
    payload: Dict[str, Any] = {
        "tool_name": tool_name,
        "input": tool_input,
        "output": tool_output,
    }
    if error is not None:
        payload["error"] = error
    _emit_event(TrajectoryEventType.TOOL_CALL, payload)


def emit_log(metadata: Dict[str, Any]) -> None:
    _emit_event(TrajectoryEventType.LOG, {"metadata": metadata})


def emit_task_start(*, task_id: int, task: str, metadata: Dict[str, Any] | None = None) -> None:
    payload = {"task_id": task_id, "task": task}
    if metadata:
        payload["metadata"] = metadata
    _emit_event(TrajectoryEventType.TASK_START, payload)


def emit_task_end(
    *,
    task_id: int,
    status: str,
    final_answer: str | None = None,
    metadata: Dict[str, Any] | None = None,
) -> None:
    payload: Dict[str, Any] = {"task_id": task_id, "status": status}
    if final_answer is not None:
        payload["final_answer"] = final_answer
    if metadata:
        payload["metadata"] = metadata
    _emit_event(TrajectoryEventType.TASK_END, payload)


def _require_project_id() -> str:
    context = ExecutionContext.get()
    project_id = require_project_id(context.metadata.get("project_id"))
    context.metadata["project_id"] = project_id
    return project_id


def _resolve_task_id() -> int | None:
    try:
        metadata = ExecutionContext.get().metadata
    except Exception:
        return None
    if not isinstance(metadata, dict):
        return None
    task_id = metadata.get("task_id")
    if isinstance(task_id, int):
        return task_id
    return None


def _coerce_mapping(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "model_dump"):
        try:
            payload = value.model_dump()
            return dict(payload) if isinstance(payload, dict) else {}
        except Exception:
            return {}
    if hasattr(value, "to_dict"):
        try:
            payload = value.to_dict()
            return dict(payload) if isinstance(payload, dict) else {}
        except Exception:
            return {}
    try:
        return {key: val for key, val in vars(value).items() if not key.startswith("_")}
    except Exception:
        return {}


def _extract_usage_from_candidate(candidate: Any) -> Any:
    if candidate is None:
        return None
    if isinstance(candidate, dict):
        for key in ("usage", "token_usage", "usage_metadata", "usageMetadata", "tokenUsage"):
            if key in candidate:
                return candidate.get(key)
        return None
    for key in ("usage", "token_usage", "usage_metadata", "usageMetadata", "tokenUsage"):
        if hasattr(candidate, key):
            return getattr(candidate, key)
    return None


def _iter_usage_candidates(response: Any) -> list[Any]:
    candidates = [response]
    if isinstance(response, dict):
        for key in ("response", "raw", "data", "result"):
            if key in response:
                candidates.append(response.get(key))
    else:
        for key in ("response", "raw", "data", "result"):
            if hasattr(response, key):
                candidates.append(getattr(response, key))
    return candidates


def _find_reasoning_tokens(response: Any, usage: Any) -> Any:
    for candidate in _iter_usage_candidates(response):
        if isinstance(candidate, dict) and "reasoning_tokens" in candidate:
            return candidate.get("reasoning_tokens")
        if hasattr(candidate, "reasoning_tokens"):
            return getattr(candidate, "reasoning_tokens")
    if isinstance(usage, dict) and "reasoning_tokens" in usage:
        return usage.get("reasoning_tokens")
    if hasattr(usage, "reasoning_tokens"):
        return getattr(usage, "reasoning_tokens")
    return None


def _maybe_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _normalise_usage_counts(usage_dict: Dict[str, Any]) -> None:
    prompt = usage_dict.get("prompt_tokens")
    completion = usage_dict.get("completion_tokens")
    total = usage_dict.get("total_tokens")

    if prompt is None:
        prompt = _maybe_int(usage_dict.get("input_tokens"))
    if completion is None:
        completion = _maybe_int(usage_dict.get("output_tokens"))
    if prompt is None:
        prompt = _maybe_int(usage_dict.get("promptTokenCount"))
    if completion is None:
        completion = _maybe_int(usage_dict.get("candidatesTokenCount"))
    if total is None:
        total = _maybe_int(usage_dict.get("totalTokenCount"))

    if prompt is not None:
        usage_dict.setdefault("prompt_tokens", prompt)
    if completion is not None:
        usage_dict.setdefault("completion_tokens", completion)
    if total is None and prompt is not None and completion is not None:
        total = prompt + completion
    if total is not None:
        usage_dict.setdefault("total_tokens", total)


def extract_usage(response: Any) -> tuple[Dict[str, Any], Optional[str]]:
    try:
        usage = None
        for candidate in _iter_usage_candidates(response):
            usage = _extract_usage_from_candidate(candidate)
            if usage is not None:
                break

        if usage is None:
            return {}, "missing_usage"

        usage_dict = _coerce_mapping(usage)
        if not usage_dict:
            return {}, "missing_usage"

        details = usage_dict.get("completion_tokens_details")
        if details is not None and not isinstance(details, dict):
            usage_dict["completion_tokens_details"] = _coerce_mapping(details)

        if "completion_tokens_details" not in usage_dict or not usage_dict.get("completion_tokens_details"):
            extra_details = None
            if isinstance(response, dict) and "completion_tokens_details" in response:
                extra_details = response.get("completion_tokens_details")
            elif hasattr(response, "completion_tokens_details"):
                extra_details = getattr(response, "completion_tokens_details")
            if extra_details is None and hasattr(usage, "completion_tokens_details"):
                extra_details = getattr(usage, "completion_tokens_details")
            if extra_details is not None:
                usage_dict["completion_tokens_details"] = _coerce_mapping(extra_details)

        _normalise_usage_counts(usage_dict)

        reasoning_tokens = _find_reasoning_tokens(response, usage)
        if reasoning_tokens is not None:
            details = usage_dict.get("completion_tokens_details")
            if not isinstance(details, dict):
                details = {}
            details.setdefault("reasoning_tokens", reasoning_tokens)
            usage_dict["completion_tokens_details"] = details

        return usage_dict, None
    except Exception:
        return {}, "telemetry_error"


def _normalise_reasoning_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def _append_reasoning_text(reasoning: Dict[str, Any], value: Any) -> None:
    text = _normalise_reasoning_text(value)
    if not text:
        return
    existing = reasoning.get("reasoning_content")
    if isinstance(existing, str) and existing:
        reasoning["reasoning_content"] = f"{existing}\n{text}"
    else:
        reasoning["reasoning_content"] = text


def _append_reasoning_block(reasoning: Dict[str, Any], block: Dict[str, Any]) -> None:
    blocks = reasoning.setdefault("thinking_blocks", [])
    if isinstance(blocks, list):
        blocks.append(block)


def _collect_reasoning_fields(payload: Any, reasoning: Dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        return
    for key in ("reasoning_content", "thinking", "thinking_blocks"):
        if key in payload:
            reasoning.setdefault(key, payload.get(key))


def _collect_reasoning_from_content(content: Any, reasoning: Dict[str, Any]) -> None:
    if isinstance(content, dict):
        _collect_reasoning_fields(content, reasoning)
        for key in ("thought", "thoughts", "analysis", "reasoning"):
            if key in content:
                _append_reasoning_text(reasoning, content.get(key))
                _append_reasoning_block(reasoning, {"type": key, "text": content.get(key)})
        block_type = content.get("type")
        if isinstance(block_type, str) and block_type in ("thinking", "thought", "analysis", "reasoning"):
            _append_reasoning_text(reasoning, content.get("text") or content.get("content"))
            _append_reasoning_block(
                reasoning,
                {"type": block_type, "text": content.get("text") or content.get("content")},
            )
        nested = content.get("content")
        if nested is not None and nested is not content:
            _collect_reasoning_from_content(nested, reasoning)
        return
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                _collect_reasoning_fields(item, reasoning)
                for key in ("thought", "thoughts", "analysis", "reasoning"):
                    if key in item:
                        _append_reasoning_text(reasoning, item.get(key))
                        _append_reasoning_block(reasoning, {"type": key, "text": item.get(key)})
                block_type = item.get("type")
                if isinstance(block_type, str) and block_type in ("thinking", "thought", "analysis", "reasoning"):
                    _append_reasoning_text(reasoning, item.get("text") or item.get("content"))
                    _append_reasoning_block(
                        reasoning,
                        {"type": block_type, "text": item.get("text") or item.get("content")},
                    )
                nested = item.get("content")
                if nested is not None and nested is not item:
                    _collect_reasoning_from_content(nested, reasoning)


def _collect_reasoning_from_message(message: Any, reasoning: Dict[str, Any]) -> None:
    if isinstance(message, dict):
        _collect_reasoning_fields(message, reasoning)
        _collect_reasoning_from_content(message.get("content"), reasoning)
        return
    for key in ("reasoning_content", "thinking", "thinking_blocks"):
        if hasattr(message, key):
            reasoning.setdefault(key, getattr(message, key))
    if hasattr(message, "content"):
        _collect_reasoning_from_content(getattr(message, "content"), reasoning)


def extract_reasoning(response: Any) -> tuple[Dict[str, Any], Optional[str]]:
    try:
        reasoning: Dict[str, Any] = {}
        if isinstance(response, dict):
            _collect_reasoning_fields(response, reasoning)
            _collect_reasoning_from_message(response.get("message"), reasoning)
            _collect_reasoning_from_content(response.get("content"), reasoning)
            output = response.get("output")
            if output is not None:
                _collect_reasoning_from_content(output, reasoning)
            choices = response.get("choices")
            if isinstance(choices, list):
                for choice in choices:
                    if not isinstance(choice, dict):
                        continue
                    _collect_reasoning_from_message(choice.get("message") or choice.get("delta"), reasoning)
                    _collect_reasoning_from_content(choice.get("content"), reasoning)
            candidates = response.get("candidates")
            if isinstance(candidates, list):
                for candidate in candidates:
                    if not isinstance(candidate, dict):
                        continue
                    content = candidate.get("content")
                    if isinstance(content, dict):
                        _collect_reasoning_from_content(content.get("parts"), reasoning)
                    else:
                        _collect_reasoning_from_content(content, reasoning)
        else:
            for key in ("reasoning_content", "thinking", "thinking_blocks"):
                if hasattr(response, key):
                    reasoning.setdefault(key, getattr(response, key))
            message = getattr(response, "message", None)
            if message is not None:
                _collect_reasoning_from_message(message, reasoning)
            content = getattr(response, "content", None)
            if content is not None:
                _collect_reasoning_from_content(content, reasoning)
            output = getattr(response, "output", None)
            if output is not None:
                _collect_reasoning_from_content(output, reasoning)
            choices = getattr(response, "choices", None)
            if isinstance(choices, list):
                for choice in choices:
                    _collect_reasoning_from_message(getattr(choice, "message", None) or getattr(choice, "delta", None), reasoning)
                    _collect_reasoning_from_content(getattr(choice, "content", None), reasoning)
            candidates = getattr(response, "candidates", None)
            if isinstance(candidates, list):
                for candidate in candidates:
                    content = getattr(candidate, "content", None)
                    if hasattr(content, "parts"):
                        _collect_reasoning_from_content(getattr(content, "parts", None), reasoning)
                    else:
                        _collect_reasoning_from_content(content, reasoning)

        reasoning = {key: value for key, value in reasoning.items() if value is not None}
        if not reasoning:
            return {}, "missing_reasoning"
        return reasoning, None
    except Exception:
        return {}, "telemetry_error"


async def capture_llm_call(
    target: Callable[[], Any],
    *,
    messages: Any,
    model_params: Dict[str, Any],
) -> Any:
    response = None
    call_error: Exception | None = None
    telemetry_errors: list[str] = []
    try:
        result = target()
        if inspect.isawaitable(result):
            response = await result
        else:
            response = result
    except Exception as exc:
        call_error = exc

    if call_error is None:
        usage, usage_error = extract_usage(response)
        if usage_error:
            telemetry_errors.append(usage_error)
        reasoning, reasoning_error = extract_reasoning(response)
        if reasoning_error:
            telemetry_errors.append(reasoning_error)
    else:
        usage = {}
        reasoning = {}
        telemetry_errors.extend(["missing_usage", "missing_reasoning"])

    emit_llm_call(
        messages=messages,
        model_params=model_params,
        response=response,
        usage=usage,
        reasoning=reasoning,
        error=str(call_error) if call_error is not None else None,
        telemetry_error=telemetry_errors or None,
    )

    if call_error is not None:
        raise call_error
    return response


def log(data: Dict[str, Any]) -> None:
    """Log structured metadata to the active agent trace."""
    emit_log(data)


def get_learnings(trace_id: Optional[str] = None) -> list[str]:
    """
    Retrieve relevant learnings for the current context.

    Args:
        trace_id: Optional trace ID to fetch learnings for. If None, uses current context.

    Returns:
        List of learning strings.
    """
    try:
        context = ExecutionContext.get()
        state = context.metadata.get("learning_state")
        if isinstance(state, dict):
            active = state.get("active")
            if isinstance(active, list):
                learnings = []
                for entry in active:
                    if not isinstance(entry, dict):
                        continue
                    learning = entry.get("learning")
                    if isinstance(learning, str) and learning.strip():
                        learnings.append(learning.strip())
                return learnings
        return []
    except Exception:
        return []


class _AgentTrace:
    def __init__(
        self,
        *,
        name: str,
        system_prompt: str,
        tool_definitions: Any,
        mcp_definitions: Any,
        model_config: Dict[str, Any],
        session: Any = None,
        agent_name: str | None = None,
        agent_id: str | None = None,
        parent_agent_name: str | None = None,
        parent_agent_id: str | None = None,
        trace_type: str | None = None,
        metadata: Dict[str, Any] | None = None,
        project: str | None = None,
    ) -> None:
        self._name = name
        self._system_prompt = system_prompt
        self._tool_definitions = tool_definitions
        self._mcp_definitions = mcp_definitions
        self._model_config = model_config
        self._session = session
        self._agent_name = agent_name
        self._agent_id = agent_id
        self._parent_agent_name = parent_agent_name
        self._parent_agent_id = parent_agent_id
        self._trace_type = trace_type
        self._metadata = metadata
        self._project = project
        self._run_token = None
        self._agent_tokens: tuple[Any, Any, Any] | None = None
        self._event_context: tuple[int, str, str | None, str] | None = None
        self._start_time: float | None = None

    def _enter(self) -> "_AgentTrace":
        _validate_agent_definition_inputs(
            system_prompt=self._system_prompt,
            tool_definitions=self._tool_definitions,
            mcp_definitions=self._mcp_definitions,
            model_config=self._model_config,
        )
        _, run_token = ensure_run_id()
        self._run_token = run_token
        project_id = None
        agent_name = self._agent_name or self._name
        if self._agent_id is not None:
            agent_id = self._agent_id
        else:
            project_id = _require_project_id()
            agent_id = agent_id_for_name(project_id, agent_name)
        if self._parent_agent_id is not None:
            parent_agent_id = self._parent_agent_id
        elif self._parent_agent_name is not None:
            if project_id is None:
                project_id = _require_project_id()
            parent_agent_id = agent_id_for_name(project_id, self._parent_agent_name)
        else:
            parent_agent_id = get_current_agent_id()
        invocation_id = str(uuid.uuid4())
        self._agent_tokens = set_agent_context(
            agent_id=agent_id,
            parent_agent_id=parent_agent_id,
            invocation_id=invocation_id,
        )
        context = ExecutionContext.get()
        context.metadata["agent_id"] = agent_id
        context.metadata["parent_agent_id"] = parent_agent_id
        context.metadata["invocation_id"] = invocation_id
        self._event_context = (get_run_id(), agent_id, parent_agent_id, invocation_id)
        self._start_time = time.time()
        start_payload: Dict[str, Any] = {
            "name": self._name,
            "started_at": self._start_time,
        }
        if self._trace_type:
            start_payload["trace_type"] = self._trace_type
        if self._metadata:
            start_payload["metadata"] = self._metadata
        try:
            _emit_event(TrajectoryEventType.AGENT_START, start_payload)
            if self._session is None:
                register_agent_definition(
                    name=self._name,
                    system_prompt=self._system_prompt,
                    tool_definitions=self._tool_definitions,
                    mcp_definitions=self._mcp_definitions,
                    model_config=self._model_config,
                )
        except Exception:
            if self._agent_tokens is not None:
                reset_agent_context(self._agent_tokens)
            reset_run_id(self._run_token)
            raise
        return self

    def _exit(self, exc: BaseException | None) -> bool:
        end_time = time.time()
        status = "error" if exc is not None else "success"
        payload: Dict[str, Any] = {
            "name": self._name,
            "started_at": self._start_time,
            "ended_at": end_time,
            "duration": end_time - self._start_time if self._start_time is not None else None,
            "status": status,
        }
        if exc is not None:
            payload["error"] = str(exc)
        try:
            if self._event_context is not None:
                run_id, agent_id, parent_agent_id, invocation_id = self._event_context
                event = TrajectoryEvent(
                    run_id=run_id,
                    agent_id=agent_id,
                    parent_agent_id=parent_agent_id,
                    invocation_id=invocation_id,
                    task_id=_resolve_task_id(),
                    event_type=TrajectoryEventType.AGENT_END,
                    payload=payload,
                )
                ExecutionContext.get().emit(event.to_dict())
            else:
                _emit_event(TrajectoryEventType.AGENT_END, payload)
        finally:
            if self._agent_tokens is not None:
                reset_agent_context(self._agent_tokens)
            try:
                context = ExecutionContext.get()
                if isinstance(context.metadata, dict):
                    context.metadata.pop("agent_id", None)
                    context.metadata.pop("parent_agent_id", None)
                    context.metadata.pop("invocation_id", None)
            except Exception:
                pass
            reset_run_id(self._run_token)
        return False

    def __enter__(self) -> "_AgentTrace":
        return self._enter()

    def __exit__(self, exc_type, exc, traceback) -> bool:
        return self._exit(exc)

    async def __aenter__(self) -> "_AgentTrace":
        return self._enter()

    async def __aexit__(self, exc_type, exc, traceback) -> bool:
        return self._exit(exc)


def trace_agent(
    *,
    name: str,
    system_prompt: str,
    tool_definitions: Any,
    mcp_definitions: Any,
    model_config: Dict[str, Any],
    agent_name: str | None = None,
    agent_id: str | None = None,
    parent_agent_name: str | None = None,
    parent_agent_id: str | None = None,
) -> _AgentTrace:
    return _AgentTrace(
        name=name,
        system_prompt=system_prompt,
        tool_definitions=tool_definitions,
        mcp_definitions=mcp_definitions,
        model_config=model_config,
        agent_name=agent_name,
        agent_id=agent_id,
        parent_agent_name=parent_agent_name,
        parent_agent_id=parent_agent_id,
    )


def trace(
    name: Optional[str] = None,
    project: Optional[str] = None,
    trace_type: str = "chain",
    metadata: Optional[Dict[str, Any]] = None,
    *,
    session: Any = None,
    system_prompt: str,
    tool_definitions: Any,
    mcp_definitions: Any,
    model_config: Dict[str, Any],
    agent_name: str | None = None,
    parent_agent_name: str | None = None,
    parent_agent_id: str | None = None,
) -> Callable[[T], T]:
    """
    Decorator to capture execution traces for Marlo.

    Args:
        name: Name of the trace (defaults to function name)
        project: Project identifier
        trace_type: Type of trace (chain, tool, generation, etc.)
        metadata: Additional metadata
    """
    def decorator(func: T) -> T:
        trace_name = name or func.__name__
        resolved_agent_name = agent_name or trace_name

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            agent_override = None
            if session and get_current_agent_id() is None:
                agent_override = session.agent_id
            if session is None:
                async with _AgentTrace(
                    name=trace_name,
                    system_prompt=system_prompt,
                    tool_definitions=tool_definitions,
                    mcp_definitions=mcp_definitions,
                    model_config=model_config,
                    agent_name=resolved_agent_name,
                    agent_id=agent_override,
                    parent_agent_name=parent_agent_name,
                    parent_agent_id=parent_agent_id,
                    trace_type=trace_type,
                    metadata=metadata,
                    project=project,
                ):
                    return await func(*args, **kwargs)
            with session.activate():
                async with _AgentTrace(
                    name=trace_name,
                    system_prompt=system_prompt,
                    tool_definitions=tool_definitions,
                    mcp_definitions=mcp_definitions,
                    model_config=model_config,
                    session=session,
                    agent_name=resolved_agent_name,
                    agent_id=agent_override,
                    parent_agent_name=parent_agent_name,
                    parent_agent_id=parent_agent_id,
                    trace_type=trace_type,
                    metadata=metadata,
                    project=project,
                ):
                    return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            agent_override = None
            if session and get_current_agent_id() is None:
                agent_override = session.agent_id
            if session is None:
                with _AgentTrace(
                    name=trace_name,
                    system_prompt=system_prompt,
                    tool_definitions=tool_definitions,
                    mcp_definitions=mcp_definitions,
                    model_config=model_config,
                    agent_name=resolved_agent_name,
                    agent_id=agent_override,
                    parent_agent_name=parent_agent_name,
                    parent_agent_id=parent_agent_id,
                    trace_type=trace_type,
                    metadata=metadata,
                    project=project,
                ):
                    return func(*args, **kwargs)
            with session.activate():
                with _AgentTrace(
                    name=trace_name,
                    system_prompt=system_prompt,
                    tool_definitions=tool_definitions,
                    mcp_definitions=mcp_definitions,
                    model_config=model_config,
                    session=session,
                    agent_name=resolved_agent_name,
                    agent_id=agent_override,
                    parent_agent_name=parent_agent_name,
                    parent_agent_id=parent_agent_id,
                    trace_type=trace_type,
                    metadata=metadata,
                    project=project,
                ):
                    return func(*args, **kwargs)

        if inspect.isasyncgenfunction(func):
            @functools.wraps(func)
            async def async_gen_wrapper(*args, **kwargs):
                agent_override = None
                if session and get_current_agent_id() is None:
                    agent_override = session.agent_id

                if session is None:
                    async with _AgentTrace(
                        name=trace_name,
                        system_prompt=system_prompt,
                        tool_definitions=tool_definitions,
                        mcp_definitions=mcp_definitions,
                        model_config=model_config,
                        agent_name=resolved_agent_name,
                        agent_id=agent_override,
                        parent_agent_name=parent_agent_name,
                        parent_agent_id=parent_agent_id,
                        trace_type=trace_type,
                        metadata=metadata,
                        project=project,
                    ):
                        async for item in func(*args, **kwargs):
                            yield item
                    return

                with session.activate():
                    async with _AgentTrace(
                        name=trace_name,
                        system_prompt=system_prompt,
                        tool_definitions=tool_definitions,
                        mcp_definitions=mcp_definitions,
                        model_config=model_config,
                        session=session,
                        agent_name=resolved_agent_name,
                        agent_id=agent_override,
                        parent_agent_name=parent_agent_name,
                        parent_agent_id=parent_agent_id,
                        trace_type=trace_type,
                        metadata=metadata,
                        project=project,
                    ):
                        async for item in func(*args, **kwargs):
                            yield item
            return async_gen_wrapper

        if asyncio.iscoroutinefunction(func):
            return async_wrapper

        return sync_wrapper

    return decorator


def wrap_agent(
    name: Optional[str] = None,
    project: Optional[str] = None,
    trace_type: str = "chain",
    metadata: Optional[Dict[str, Any]] = None,
    *,
    session: Any = None,
    system_prompt: str,
    tool_definitions: Any,
    mcp_definitions: Any,
    model_config: Dict[str, Any],
    agent_name: str | None = None,
    parent_agent_name: str | None = None,
    parent_agent_id: str | None = None,
) -> Callable[[T], T]:
    return trace(
        name=name,
        project=project,
        trace_type=trace_type,
        metadata=metadata,
        session=session,
        system_prompt=system_prompt,
        tool_definitions=tool_definitions,
        mcp_definitions=mcp_definitions,
        model_config=model_config,
        agent_name=agent_name,
        parent_agent_name=parent_agent_name,
        parent_agent_id=parent_agent_id,
    )


__all__ = [
    "capture_llm_call",
    "emit_llm_call",
    "emit_log",
    "emit_task_end",
    "emit_task_start",
    "emit_tool_call",
    "extract_reasoning",
    "extract_usage",
    "get_learnings",
    "log",
    "register_agent_definition",
    "trace",
    "trace_agent",
    "wrap_agent",
]

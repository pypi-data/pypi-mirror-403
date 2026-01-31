"""Learning engine public exports."""

from __future__ import annotations

from typing import Any

from marlo.learning.generation.compiler import LearningCompiler
from marlo.learning.generation.generator import LearningGenerator, LearningInsight
from marlo.trajectories.capture.context import ExecutionContext, get_current_agent_id


def track_llm(
    session: Any = None,
    *,
    messages: Any | None = None,
    model: str | None = None,
    model_params: dict[str, Any] | None = None,
    input: str | None = None,
    output: Any | None = None,
    response: Any | None = None,
    usage: dict[str, Any] | None = None,
    reasoning: dict[str, Any] | None = None,
    error: str | None = None,
    telemetry_error: list[str] | None = None,
) -> None:
    from marlo.trajectories.schema.events import TrajectoryEvent, TrajectoryEventType

    payload_messages = messages
    if payload_messages is None and input is not None:
        payload_messages = [{"role": "user", "content": input}]
    params = dict(model_params or {})
    if model and not params.get("model"):
        params["model"] = model
    payload_response = response if response is not None else output
    if payload_response is None and output is not None:
        payload_response = {"text": output}
    if payload_response is None:
        payload_response = {}
    payload_usage = usage if isinstance(usage, dict) else {}
    payload_reasoning = reasoning if isinstance(reasoning, dict) else {}

    payload: dict[str, Any] = {
        "messages": payload_messages or [],
        "model_params": params,
        "response": payload_response,
        "usage": payload_usage,
        "reasoning": payload_reasoning,
    }
    if error:
        payload["error"] = error
    if telemetry_error:
        payload["telemetry_error"] = telemetry_error

    if session is not None:
        context = session.context
        task_id = context.metadata.get("task_id")
        invocation_id = context.metadata.get("invocation_id") or f"{session.session_id}-session"
        event = TrajectoryEvent(
            run_id=session.session_id,
            agent_id=session.agent_id,
            parent_agent_id=None,
            invocation_id=invocation_id,
            task_id=task_id,
            event_type=TrajectoryEventType.LLM_CALL,
            payload=payload,
        )
        context.emit(event.to_dict())
    else:
        from marlo.trajectories.capture.decorators import emit_llm_call
        emit_llm_call(
            messages=payload_messages or [],
            model_params=params,
            response=payload_response,
            usage=payload_usage,
            reasoning=payload_reasoning,
            error=error,
            telemetry_error=telemetry_error,
        )


def track_tool(
    session: Any = None,
    *,
    tool_name: str | None = None,
    tool: str | None = None,
    input: Any = None,
    output: Any = None,
    error: str | None = None,
) -> None:
    from marlo.trajectories.schema.events import TrajectoryEvent, TrajectoryEventType

    name = tool_name or tool
    if not name:
        raise ValueError("tool_name is required for tool tracking.")

    payload: dict[str, Any] = {
        "tool_name": name,
        "tool_input": input,
        "tool_output": output,
    }
    if error:
        payload["error"] = error

    if session is not None:
        context = session.context
        task_id = context.metadata.get("task_id")
        invocation_id = context.metadata.get("invocation_id") or f"{session.session_id}-session"
        event = TrajectoryEvent(
            run_id=session.session_id,
            agent_id=session.agent_id,
            parent_agent_id=None,
            invocation_id=invocation_id,
            task_id=task_id,
            event_type=TrajectoryEventType.TOOL_CALL,
            payload=payload,
        )
        context.emit(event.to_dict())
    else:
        from marlo.trajectories.capture.decorators import emit_tool_call
        emit_tool_call(
            tool_name=name,
            tool_input=input,
            tool_output=output,
            error=error,
        )


def track_log(*, metadata: dict[str, Any]) -> None:
    from marlo.trajectories.capture.decorators import emit_log

    emit_log(metadata)


__all__ = [
    "LearningCompiler",
    "LearningGenerator",
    "LearningInsight",
    "get_current_agent_id",
    "track_llm",
    "track_log",
    "track_tool",
]

_CAPTURE_EXPORTS = {
    "emit_llm_call",
    "emit_log",
    "emit_task_end",
    "emit_task_start",
    "emit_tool_call",
    "register_agent_definition",
    "trace",
    "trace_agent",
    "wrap_agent",
}


def __getattr__(name: str):
    if name in _CAPTURE_EXPORTS:
        import importlib

        capture = importlib.import_module("marlo.trajectories.capture")
        return getattr(capture, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(__all__) | _CAPTURE_EXPORTS)

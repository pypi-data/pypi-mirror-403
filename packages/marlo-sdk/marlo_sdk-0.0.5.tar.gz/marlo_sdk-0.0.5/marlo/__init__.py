"""Marlo public API for SDK wrappers."""

from __future__ import annotations

from marlo.trajectories.capture import get_learnings, log, trace
from marlo.trajectories.schema import MarloRewardBreakdown, MarloSessionTrace, MarloStepTrace

__all__ = [
    "trace",
    "log",
    "get_learnings",
    "MarloRewardBreakdown",
    "MarloSessionTrace",
    "MarloStepTrace",
    "init",
    "init_async",
    "init_in_thread",
    "agent",
    "task",
    "shutdown",
]

_SDK_EXPORTS = {
    "init": ("marlo.sdk.client", "init"),
    "init_async": ("marlo.sdk.client", "init_async"),
    "init_in_thread": ("marlo.sdk.client", "init_in_thread"),
    "agent": ("marlo.sdk.registry", "register_agent"),
    "task": ("marlo.sdk.context", "task"),
    "shutdown": ("marlo.sdk.client", "shutdown"),
}


def __getattr__(name: str):
    if name in _SDK_EXPORTS:
        import importlib
        module_path, attr_name = _SDK_EXPORTS[name]
        module = importlib.import_module(module_path)
        return getattr(module, attr_name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(__all__) | set(_SDK_EXPORTS.keys()))

"""Decorators for marking simulation environments and agents.

These are intentionally no-op beyond tagging the decorated class so that
discovery/scaffolding tooling can locate them.
"""

from __future__ import annotations

from typing import TypeVar

T = TypeVar("T", bound=type)


def environment(cls: T) -> T:
    setattr(cls, "__marlo_environment__", True)
    return cls


def agent(cls: T) -> T:
    setattr(cls, "__marlo_agent__", True)
    return cls


__all__ = ["agent", "environment"]


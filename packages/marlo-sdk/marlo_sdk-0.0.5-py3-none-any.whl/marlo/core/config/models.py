"""Configuration models used across Marlo subsystems."""

from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field


class StorageConfig(BaseModel):
    database_url: str
    min_connections: int = 1
    max_connections: int = 10
    statement_timeout_seconds: float = 60.0

    model_config = ConfigDict(extra="allow")


__all__ = [
    "StorageConfig",
]

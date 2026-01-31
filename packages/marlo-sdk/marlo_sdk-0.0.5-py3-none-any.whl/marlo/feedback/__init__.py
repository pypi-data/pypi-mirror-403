"""Feedback module for project-specific prompt customization."""

from __future__ import annotations

from marlo.feedback.chunk_updater import update_reward_chunk, update_learning_chunk
from marlo.feedback.prompts import (
    REWARD_CHUNK_UPDATE_PROMPT,
    LEARNING_CHUNK_UPDATE_PROMPT,
)

__all__ = [
    "update_reward_chunk",
    "update_learning_chunk",
    "REWARD_CHUNK_UPDATE_PROMPT",
    "LEARNING_CHUNK_UPDATE_PROMPT",
]

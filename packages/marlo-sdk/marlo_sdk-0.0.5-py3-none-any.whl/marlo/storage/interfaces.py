"""Storage interfaces used by domain modules.

Domain packages (trajectories/learning/measurement/simulation) should depend on
these protocols rather than importing concrete storage implementations.
"""

from __future__ import annotations

from typing import Any, Protocol, Sequence


class RewardBaselineStore(Protocol):
    async def fetch_reward_baseline(
        self,
        learning_key: str | None = None,
        *,
        project_id: str,
        window: int = 50,
    ) -> dict[str, Any]:
        ...


class LearningReportStore(RewardBaselineStore, Protocol):
    async def fetch_learning_tasks(
        self,
        *,
        project_id: str,
        org_id: str,
        user_id: str,
        learning_key: str | None = None,
        project_root: str | None = None,
        task: str | None = None,
        tags: Sequence[str] | None = None,
        limit: int | None = None,
        offset: int = 0,
        order: str = "asc",
    ) -> list[dict[str, Any]]:
        ...

    async def fetch_task_event_counts(self, task_ids: Sequence[int]) -> dict[int, int]:
        ...

    async def fetch_trajectory_events(
        self, session_id: int, *, task_id: int | None = None, limit: int = 200
    ) -> list[dict[str, Any]]:
        ...

    async def fetch_discovery_runs(
        self,
        *,
        project_root: str | None = None,
        task: str | None = None,
        source: str | Sequence[str] | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        ...

    async def fetch_learning_objects_with_details(
        self,
        learning_key: str,
        *,
        project_id: str,
        org_id: str,
        user_id: str,
        statuses: Sequence[str] | None = None,
        agent_id: str | None = None,
        evidence_limit: int = 5,
    ) -> list[dict[str, Any]]:
        ...

"""Asynchronous PostgreSQL persistence layer."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from statistics import fmean, median, pstdev
from typing import Any, Dict, Iterable, List, Optional, Sequence

try:
    from importlib import resources as importlib_resources
except ImportError:  # pragma: no cover
    import importlib_resources  # type: ignore

try:
    import asyncpg  # type: ignore[import-untyped]
    _ASYNCPG_ERROR = None
except ModuleNotFoundError as exc:
    asyncpg = None
    _ASYNCPG_ERROR = exc

from marlo.core.config.models import StorageConfig
from marlo.trajectories.schema.traces import MarloRewardBreakdown
from marlo.learning.management import MarloContextManager, TraceMemoryProvider
from marlo.learning.rewards.judges.base import (
    build_agent_context,
    build_agent_trajectory_context,
    build_task_trajectory_context,
    collect_subtree_ids,
    filter_events_by_agents,
    normalize_events,
    resolve_agent_tree,
)
from marlo.learning.management.pipeline import process_learning_update
from marlo.learning.rewards.runner import evaluate_session
from marlo.trajectories.capture.context import ExecutionContext
from marlo.storage.postgres.agents import upsert_agent_definition

logger = logging.getLogger(__name__)

_SCHEMA_FILES = (
    "sessions.sql",
    "tasks.sql",
    "trajectory.sql",
    "agents.sql",
    "reward.sql",
    "learning.sql",
    "search.sql",
    "copilot.sql",
    "feedback.sql",
)


class Database:
    def __init__(self, config: StorageConfig) -> None:
        self._config = config
        self._pool: asyncpg.Pool | None = None
        self._schema_sql: list[str] | None = None
        self._schema_initialized: bool = False

    async def connect(self) -> None:
        if asyncpg is None:
            raise RuntimeError("asyncpg is required for database persistence") from _ASYNCPG_ERROR
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                dsn=self._config.database_url,
                min_size=self._config.min_connections,
                max_size=self._config.max_connections,
                statement_cache_size=0,
            )
            async with self._pool.acquire() as connection:
                await connection.execute(f"SET statement_timeout = {int(self._config.statement_timeout_seconds * 1000)}")
                await self._initialize_schema(connection)

    async def disconnect(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def create_session(
        self,
        task: str,
        metadata: Dict[str, Any] | None = None,
        *,
        project_id: str | None = None,
        org_id: str | None = None,
        user_id: str | None = None,
    ) -> int:
        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("project_id is required to create a session")
        if not isinstance(org_id, str) or not org_id.strip():
            raise ValueError("org_id is required to create a session")
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("user_id is required to create a session")
        pool = self._require_pool()
        serialized_metadata = self._serialize_json(metadata) if metadata else None
        async with pool.acquire() as connection:
            return await connection.fetchval(
                "INSERT INTO sessions(task, metadata, project_id, org_id, user_id)"
                " VALUES ($1, $2, $3, $4, $5) RETURNING id",
                task,
                serialized_metadata,
                project_id.strip(),
                org_id.strip(),
                user_id.strip(),
            )

    async def create_task(
        self,
        session_id: int,
        task: str,
        metadata: Dict[str, Any] | None = None,
        *,
        project_id: str | None = None,
        org_id: str | None = None,
        user_id: str | None = None,
    ) -> int:
        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("project_id is required to create a task")
        if not isinstance(org_id, str) or not org_id.strip():
            raise ValueError("org_id is required to create a task")
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("user_id is required to create a task")
        pool = self._require_pool()
        serialized_metadata = self._serialize_json(metadata) if metadata else None
        async with pool.acquire() as connection:
            return await connection.fetchval(
                "INSERT INTO session_tasks(session_id, task, project_id, org_id, user_id, metadata)"
                " VALUES ($1, $2, $3, $4, $5, $6) RETURNING id",
                session_id,
                task,
                project_id.strip(),
                org_id.strip(),
                user_id.strip(),
                serialized_metadata,
            )

    async def log_intermediate_step(self, session_id: int, event: Any) -> None:
        pool = self._require_pool()
        event_payload = self._coerce_event_payload(event)
        serialized_event = self._serialize_json(event_payload) or "{}"
        async with pool.acquire() as connection:
            project_id, org_id, user_id = await self._fetch_session_scope(connection, session_id)
            if not project_id or not org_id or not user_id:
                raise ValueError("session scope is required to log telemetry")
            if self._is_agent_definition_event(event_payload):
                await upsert_agent_definition(connection, session_id, event_payload)
            await connection.execute(
                "INSERT INTO trajectory_events(session_id, project_id, org_id, user_id, event)"
                " VALUES ($1, $2, $3, $4, $5)"
                " ON CONFLICT ((event->>'event_id')) WHERE event->>'event_id' IS NOT NULL DO NOTHING",
                session_id,
                project_id,
                org_id,
                user_id,
                serialized_event,
            )

    async def _fetch_session_scope(
        self,
        connection: "asyncpg.connection.Connection",
        session_id: int,
    ) -> tuple[str | None, str | None, str | None]:
        row = await connection.fetchrow(
            "SELECT project_id, org_id, user_id FROM sessions WHERE id = $1",
            session_id,
        )
        if row is None:
            return None, None, None
        return row.get("project_id"), row.get("org_id"), row.get("user_id")

    async def _fetch_task_scopes(
        self,
        connection: "asyncpg.connection.Connection",
        task_ids: Sequence[int],
    ) -> dict[int, tuple[str, str, str]]:
        if not task_ids:
            return {}
        rows = await connection.fetch(
            "SELECT id, project_id, org_id, user_id FROM session_tasks WHERE id = ANY($1::bigint[])",
            list(task_ids),
        )
        scope_map: dict[int, tuple[str, str, str]] = {}
        for row in rows:
            task_id = row.get("id")
            project_id = row.get("project_id")
            org_id = row.get("org_id")
            user_id = row.get("user_id")
            if isinstance(task_id, int) and project_id and org_id and user_id:
                scope_map[task_id] = (project_id, org_id, user_id)
        return scope_map

    async def _fetch_learning_scope_for_key(
        self,
        connection: "asyncpg.connection.Connection",
        learning_key: str,
        project_id: str,
    ) -> tuple[str | None, str | None, str | None]:
        if not project_id:
            return None, None, None
        row = await connection.fetchrow(
            "SELECT project_id, org_id, user_id"
            " FROM session_tasks"
            " WHERE metadata->>'learning_key' = $1 AND project_id = $2"
            " ORDER BY created_at DESC LIMIT 1",
            learning_key,
            project_id,
        )
        if row is None:
            return None, None, None
        return row.get("project_id"), row.get("org_id"), row.get("user_id")

    async def _fetch_learning_scope_for_id(
        self,
        connection: "asyncpg.connection.Connection",
        learning_id: str,
    ) -> tuple[str | None, str | None, str | None]:
        row = await connection.fetchrow(
            "SELECT project_id, org_id, user_id FROM learning_objects WHERE learning_id = $1",
            learning_id,
        )
        if row is None:
            return None, None, None
        return row.get("project_id"), row.get("org_id"), row.get("user_id")


    async def log_discovery_run(
        self,
        *,
        project_root: str,
        task: str,
        payload: Dict[str, Any],
        metadata: Dict[str, Any] | None = None,
        source: str = "discovery",
    ) -> int:
        pool = self._require_pool()
        serialized_payload = self._serialize_json(payload) or "{}"
        serialized_metadata = self._serialize_json(metadata) if metadata else None
        async with pool.acquire() as connection:
            return await connection.fetchval(
                "INSERT INTO discovery_runs(project_root, task, source, payload, metadata)"
                " VALUES ($1, $2, $3, $4, $5) RETURNING id",
                project_root,
                task,
                source,
                serialized_payload,
                serialized_metadata,
            )

    async def finalize_session(self, session_id: int, final_answer: str, status: str) -> None:
        pool = self._require_pool()
        async with pool.acquire() as connection:
            await connection.execute(
                "UPDATE sessions SET status = $1, final_answer = $2, completed_at = NOW() WHERE id = $3",
                status,
                final_answer,
                session_id,
            )

    async def update_task_metadata(self, task_id: int, metadata: Dict[str, Any]) -> None:
        pool = self._require_pool()
        serialized_metadata = self._serialize_json(metadata) if metadata else None
        async with pool.acquire() as connection:
            await connection.execute(
                "UPDATE session_tasks SET metadata = $2 WHERE id = $1",
                task_id,
                serialized_metadata,
            )

    async def finalize_task(self, task_id: int, final_answer: str, status: str) -> None:
        pool = self._require_pool()
        async with pool.acquire() as connection:
            await connection.execute(
                "UPDATE session_tasks SET status = $1, final_answer = $2, completed_at = NOW() WHERE id = $3",
                status,
                final_answer,
                task_id,
            )

    async def log_task_reward(
        self,
        task_id: int,
        reward: MarloRewardBreakdown | Dict[str, Any] | None,
        learning: Optional[str],
        reward_stats: Optional[Dict[str, Any]] = None,
        reward_audit: Optional[Iterable[Dict[str, Any]]] = None,
    ) -> None:
        pool = self._require_pool()
        serialized_reward = self._serialize_json(reward.to_dict() if hasattr(reward, "to_dict") else reward) if reward else None
        serialized_stats = self._serialize_json(reward_stats) if reward_stats else None
        serialized_audit = self._serialize_json(list(reward_audit)) if reward_audit else None
        async with pool.acquire() as connection:
            await connection.execute(
                "UPDATE session_tasks SET reward = $1, learning = $2, reward_stats = $3, reward_audit = $4 WHERE id = $5",
                serialized_reward,
                learning,
                serialized_stats,
                serialized_audit,
                task_id,
            )

    async def log_agent_reward(
        self,
        session_id: int,
        task_id: int,
        agent_id: str,
        *,
        score: float | None = None,
        rationale: Any | None = None,
        principles: Any | None = None,
        error: str | None = None,
    ) -> None:
        pool = self._require_pool()
        serialized_rationale = self._serialize_json(rationale) if rationale is not None else None
        serialized_principles = self._serialize_json(principles) if principles is not None else None
        async with pool.acquire() as connection:
            project_id, org_id, user_id = await self._fetch_session_scope(connection, session_id)
            if not project_id or not org_id or not user_id:
                raise ValueError("session scope is required to log agent rewards")
            await connection.execute(
                "INSERT INTO agent_rewards("
                "session_id, task_id, agent_id, project_id, org_id, user_id, score, rationale, principles, error"
                ") VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)"
                " ON CONFLICT (session_id, task_id, agent_id) DO UPDATE SET"
                " score = EXCLUDED.score,"
                " rationale = EXCLUDED.rationale,"
                " principles = EXCLUDED.principles,"
                " error = EXCLUDED.error",
                session_id,
                task_id,
                agent_id,
                project_id,
                org_id,
                user_id,
                score,
                serialized_rationale,
                serialized_principles,
                error,
            )

    async def fetch_sessions(self, limit: int = 50, offset: int = 0) -> List[dict[str, Any]]:
        pool = self._require_pool()
        async with pool.acquire() as connection:
            rows = await connection.fetch(
                "SELECT id, task, status, review_status, review_notes, metadata, final_answer, reward,"
                " reward_stats, reward_audit, learning, project_id, org_id, user_id, created_at, completed_at"
                " FROM sessions ORDER BY created_at DESC LIMIT $1 OFFSET $2",
                limit,
                offset,
            )
        return [dict(row) for row in rows]

    async def fetch_session(self, session_id: int, *, project_id: str) -> dict[str, Any] | None:
        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("project_id is required to fetch a session")
        pool = self._require_pool()
        async with pool.acquire() as connection:
            row = await connection.fetchrow(
                "SELECT id, task, status, review_status, review_notes, metadata, final_answer, reward,"
                " reward_stats, reward_audit, learning, project_id, org_id, user_id, created_at, completed_at"
                " FROM sessions WHERE id = $1 AND project_id = $2",
                session_id,
                project_id.strip(),
            )
            if row is None:
                return None
        session = dict(row)
        return session

    async def fetch_session_tasks(self, session_id: int) -> List[dict[str, Any]]:
        pool = self._require_pool()
        async with pool.acquire() as connection:
            rows = await connection.fetch(
                "SELECT id, session_id, task, status, metadata, final_answer, reward, reward_stats,"
                " reward_audit, learning, project_id, org_id, user_id, created_at, completed_at"
                " FROM session_tasks WHERE session_id = $1 ORDER BY created_at ASC",
                session_id,
            )
        return [dict(row) for row in rows]

    async def fetch_task(self, task_id: int, *, project_id: str) -> dict[str, Any] | None:
        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("project_id is required to fetch a task")
        pool = self._require_pool()
        async with pool.acquire() as connection:
            row = await connection.fetchrow(
                "SELECT id, session_id, task, status, metadata, final_answer, reward, reward_stats,"
                " reward_audit, learning, project_id, org_id, user_id, created_at, completed_at"
                " FROM session_tasks WHERE id = $1 AND project_id = $2",
                task_id,
                project_id.strip(),
            )
            if row is None:
                return None
        return dict(row)

    async def list_sessions_by_status(
        self,
        review_status: str,
        *,
        project_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[dict[str, Any]]:
        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("project_id is required to list sessions by status")
        pool = self._require_pool()
        async with pool.acquire() as connection:
            rows = await connection.fetch(
                "SELECT id, task, status, review_status, review_notes, metadata, final_answer, reward, reward_stats, reward_audit, learning, created_at, completed_at"
                " FROM sessions WHERE review_status = $1 AND project_id = $2"
                " ORDER BY created_at DESC LIMIT $3 OFFSET $4",
                review_status,
                project_id.strip(),
                limit,
                offset,
            )
        return [dict(row) for row in rows]

    async def update_session_review_status(
        self,
        session_id: int,
        review_status: str,
        notes: Optional[str] = None,
    ) -> None:
        pool = self._require_pool()
        async with pool.acquire() as connection:
            if notes is None:
                await connection.execute(
                    "UPDATE sessions SET review_status = $1 WHERE id = $2",
                    review_status,
                    session_id,
                )
            else:
                await connection.execute(
                    "UPDATE sessions SET review_status = $1, review_notes = $2 WHERE id = $3",
                    review_status,
                    notes,
                    session_id,
                )

    async def fetch_reward_baseline(
        self,
        learning_key: Optional[str] = None,
        *,
        project_id: str,
        window: int = 50,
    ) -> dict[str, Any]:
        if not project_id:
            raise ValueError("project_id is required to fetch reward baseline")
        pool = self._require_pool()
        constraints: list[str] = ["reward_stats IS NOT NULL", "project_id = $1"]
        params: list[Any] = [project_id]
        if learning_key:
            constraints.append("(metadata ->> 'learning_key') = $" + str(len(params) + 1))
            params.append(learning_key)
        limit_index = len(params) + 1
        params.append(max(window, 1))
        where_clause = " AND ".join(constraints)
        query = (
            "SELECT reward_stats FROM session_tasks"
            f" WHERE {where_clause}"
            " ORDER BY created_at DESC LIMIT $" + str(limit_index)
        )
        async with pool.acquire() as connection:
            rows = await connection.fetch(query, *params)
        stats_payloads: list[dict[str, Any]] = []
        for row in rows:
            raw_stats = row.get("reward_stats")
            payload = self._deserialize_json(raw_stats)
            if isinstance(payload, dict):
                stats_payloads.append(payload)
        return self._aggregate_reward_baseline(stats_payloads, window=window)

    async def fetch_learning_keys(
        self,
        *,
        project_id: str,
        limit: int | None = None,
        offset: int = 0,
        project_root: str | None = None,
        task: str | None = None,
        tags: Sequence[str] | None = None,
    ) -> List[dict[str, Any]]:
        if not project_id:
            raise ValueError("project_id is required to fetch learning keys")
        pool = self._require_pool()
        params: list[Any] = [project_id]
        constraints: list[str] = ["metadata->>'learning_key' IS NOT NULL", "project_id = $1"]
        if project_root:
            params.append(project_root)
            constraints.append(f"(metadata ->> 'project_root') = ${len(params)}")
        if task:
            params.append(task)
            constraints.append(f"task = ${len(params)}")
        if tags:
            filtered_tags = [tag for tag in tags if tag]
            for tag_value in filtered_tags:
                params.append(tag_value)
                constraints.append(
                    f"EXISTS (SELECT 1 FROM jsonb_array_elements_text(metadata->'tags') AS tag WHERE tag = ${len(params)})"
                )
        query = (
            "SELECT metadata->>'learning_key' AS learning_key,"
            " COUNT(*) AS task_count,"
            " MIN(created_at) AS first_seen,"
            " MAX(created_at) AS last_seen"
            " FROM session_tasks"
        )
        if constraints:
            query += " WHERE " + " AND ".join(constraints)
        query += (
            " GROUP BY learning_key"
            " ORDER BY task_count DESC, last_seen DESC"
        )
        if limit is not None:
            params.append(max(int(limit), 0))
            query += f" LIMIT ${len(params)}"
        if offset:
            params.append(max(int(offset), 0))
            query += f" OFFSET ${len(params)}"
        async with pool.acquire() as connection:
            rows = await connection.fetch(query, *params)
        return [dict(row) for row in rows]

    async def fetch_sessions_for_learning_key(
        self,
        learning_key: str,
        *,
        project_id: str,
        limit: int | None = None,
        offset: int = 0,
    ) -> List[dict[str, Any]]:
        if not learning_key or not project_id:
            return []
        pool = self._require_pool()
        params: list[Any] = [learning_key, project_id]
        query = (
            "SELECT id, task, status, metadata, final_answer,"
            " reward, reward_stats, reward_audit, learning,"
            " created_at, completed_at, session_id"
            " FROM session_tasks"
            " WHERE metadata->>'learning_key' = $1 AND project_id = $2"
            " ORDER BY created_at ASC"
        )
        if limit is not None:
            params.append(max(int(limit), 0))
            query += f" LIMIT ${len(params)}"
        if offset:
            params.append(max(int(offset), 0))
            query += f" OFFSET ${len(params)}"
        async with pool.acquire() as connection:
            rows = await connection.fetch(query, *params)
        return [dict(row) for row in rows]

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
    ) -> List[dict[str, Any]]:
        if not project_id or not org_id or not user_id:
            raise ValueError("project_id, org_id, and user_id are required to fetch learning tasks")
        pool = self._require_pool()
        params: list[Any] = [project_id, org_id, user_id]
        clauses: list[str] = ["project_id = $1", "org_id = $2", "user_id = $3"]
        if learning_key:
            params.append(learning_key)
            clauses.append(f"(metadata ->> 'learning_key') = ${len(params)}")
        if project_root:
            params.append(project_root)
            clauses.append(f"(metadata ->> 'project_root') = ${len(params)}")
        if task:
            params.append(task)
            clauses.append(f"task = ${len(params)}")
        if tags:
            filtered_tags = [tag for tag in tags if tag]
            for tag_value in filtered_tags:
                params.append(tag_value)
                clauses.append(
                    f"EXISTS (SELECT 1 FROM jsonb_array_elements_text(metadata->'tags') AS tag WHERE tag = ${len(params)})"
                )
        ordering = "ASC" if str(order).lower() != "desc" else "DESC"
        query = (
            "SELECT id, session_id, task, status, metadata, reward, reward_stats, reward_audit,"
            " learning, created_at, completed_at,"
            " metadata->>'learning_key' AS learning_key"
            " FROM session_tasks"
        )
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += f" ORDER BY created_at {ordering}"
        if limit is not None:
            params.append(max(int(limit), 0))
            query += f" LIMIT ${len(params)}"
        if offset:
            params.append(max(int(offset), 0))
            query += f" OFFSET ${len(params)}"
        async with pool.acquire() as connection:
            rows = await connection.fetch(query, *params)
        return [dict(row) for row in rows]

    async def fetch_discovery_runs(
        self,
        *,
        project_root: str | None = None,
        task: str | None = None,
        source: str | Sequence[str] | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> List[dict[str, Any]]:
        pool = self._require_pool()
        params: list[Any] = []
        clauses: list[str] = []
        if project_root:
            params.append(project_root)
            clauses.append(f"project_root = ${len(params)}")
        if task:
            params.append(task)
            clauses.append(f"task = ${len(params)}")
        if source:
            sources = list(source) if isinstance(source, (list, tuple, set)) else [source]
            sources = [item for item in sources if item is not None]
            if sources:
                placeholders: list[str] = []
                for value in sources:
                    params.append(value)
                    placeholders.append(f"${len(params)}")
                clauses.append(f"source IN ({', '.join(placeholders)})")
        query = "SELECT id, project_root, task, source, payload, metadata, created_at FROM discovery_runs"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC"
        if limit is not None:
            params.append(max(int(limit), 0))
            query += f" LIMIT ${len(params)}"
        if offset:
            params.append(max(int(offset), 0))
            query += f" OFFSET ${len(params)}"
        async with pool.acquire() as connection:
            rows = await connection.fetch(query, *params)
        return [dict(row) for row in rows]

    async def fetch_task_event_counts(self, task_ids: Sequence[int]) -> Dict[int, int]:
        if not task_ids:
            return {}
        pool = self._require_pool()
        async with pool.acquire() as connection:
            rows = await connection.fetch(
                "SELECT (event->>'task_id')::bigint AS task_id, COUNT(*) AS event_count"
                " FROM trajectory_events"
                " WHERE (event->>'task_id')::bigint = ANY($1::bigint[])"
                " GROUP BY (event->>'task_id')::bigint",
                task_ids,
            )
        return {int(row["task_id"]): int(row["event_count"]) for row in rows}

    async def _initialize_schema(self, connection: "asyncpg.connection.Connection") -> None:
        if self._schema_initialized:
            return
        if not getattr(self._config, "apply_schema_on_connect", True):
            return
        if self._schema_sql is None:
            base = importlib_resources.files("marlo.storage.postgres")
            self._schema_sql = [
                base.joinpath(filename).read_text(encoding="utf-8")
                for filename in _SCHEMA_FILES
            ]
        for statement in self._schema_sql:
            await connection.execute(statement)
        self._schema_initialized = True

    async def fetch_learning_history(self, learning_key: str, *, project_id: str) -> List[dict[str, Any]]:
        if not learning_key or not project_id:
            return []
        pool = self._require_pool()
        async with pool.acquire() as connection:
            rows = await connection.fetch(
                "SELECT reward, learning, created_at, completed_at"
                " FROM session_tasks"
                " WHERE metadata->>'learning_key' = $1 AND project_id = $2 AND reward IS NOT NULL"
                " ORDER BY created_at ASC",
                learning_key,
                project_id,
            )
        history: List[dict[str, Any]] = []
        for row in rows:
            history.append(
                {
                    "reward": self._deserialize_json(row["reward"]),
                    "learning": row.get("learning"),
                    "created_at": row.get("created_at"),
                    "completed_at": row.get("completed_at"),
                }
            )
        return history

    async def fetch_learning_state(
        self,
        learning_key: str,
        *,
        project_id: str,
        org_id: str,
        user_id: str,
    ) -> dict[str, Any] | None:
        if not learning_key or not project_id or not org_id or not user_id:
            return None
        objects = await self.fetch_learning_objects(
            learning_key,
            project_id=project_id,
            org_id=org_id,
            user_id=user_id,
            statuses=["active"],
        )
        if not objects:
            return None
        updated_at = None
        for obj in objects:
            candidate = obj.get("updated_at")
            if candidate is None:
                continue
            if updated_at is None or candidate > updated_at:
                updated_at = candidate
        return {
            "active": objects,
            "updated_at": updated_at,
        }

    async def fetch_learning_objects(
        self,
        learning_key: str,
        *,
        project_id: str,
        org_id: str,
        user_id: str,
        statuses: Sequence[str] | None = None,
        agent_id: str | None = None,
    ) -> List[dict[str, Any]]:
        if not learning_key or not project_id or not org_id or not user_id:
            return []
        pool = self._require_pool()
        params: list[Any] = [learning_key, project_id, org_id, user_id]
        clauses = ["learning_key = $1", "project_id = $2", "org_id = $3", "user_id = $4"]
        if statuses:
            params.append(list(statuses))
            clauses.append(f"status = ANY(${len(params)})")
        if agent_id:
            params.append(agent_id)
            clauses.append(f"agent_id = ${len(params)}")
        where_clause = " AND ".join(clauses)
        query = (
            "SELECT learning_id, learning_key, version, status, agent_id, learning,"
            " expected_outcome, basis, confidence, created_at, updated_at"
            " FROM learning_objects"
            f" WHERE {where_clause}"
            " ORDER BY updated_at DESC"
        )
        async with pool.acquire() as connection:
            rows = await connection.fetch(query, *params)
        return [self._learning_object_from_row(row) for row in rows]

    async def fetch_active_learnings(
        self,
        *,
        learning_key: str,
        agent_id: str,
        project_id: str,
        org_id: str,
        user_id: str,
    ) -> List[dict[str, Any]]:
        """Fetch active learnings for the given agent and project scope.

        This method is used by the learning pipeline to check existing learnings
        before generating new ones.
        """
        return await self.fetch_learning_objects(
            learning_key,
            project_id=project_id,
            org_id=org_id,
            user_id=user_id,
            statuses=["active"],
            agent_id=agent_id,
        )

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
    ) -> List[dict[str, Any]]:
        objects = await self.fetch_learning_objects(
            learning_key,
            project_id=project_id,
            org_id=org_id,
            user_id=user_id,
            statuses=statuses,
            agent_id=agent_id,
        )
        if not objects:
            return []
        learning_ids = [obj["learning_id"] for obj in objects if obj.get("learning_id")]
        evidence_map = await self.fetch_learning_evidence_map(learning_ids, limit=evidence_limit)
        rollout_map = await self.fetch_latest_learning_rollouts_map(learning_ids)
        for obj in objects:
            learning_id = obj.get("learning_id")
            if learning_id is None:
                continue
            obj["evidence"] = evidence_map.get(learning_id, {"task_ids": [], "rationale_snippets": []})
            obj["rollout"] = rollout_map.get(learning_id)
        return objects

    async def fetch_learning_evidence_map(
        self,
        learning_ids: Sequence[str],
        *,
        limit: int = 5,
    ) -> dict[str, dict[str, Any]]:
        if not learning_ids:
            return {}
        pool = self._require_pool()
        async with pool.acquire() as connection:
            rows = await connection.fetch(
                "SELECT learning_id, task_id, rationale_snippet, created_at"
                " FROM learning_evidence"
                " WHERE learning_id = ANY($1)"
                " ORDER BY created_at DESC",
                list(learning_ids),
            )
        evidence_map: dict[str, dict[str, Any]] = {}
        for row in rows:
            learning_id = row.get("learning_id")
            if learning_id is None:
                continue
            entry = evidence_map.setdefault(
                learning_id,
                {"task_ids": [], "rationale_snippets": []},
            )
            if limit and len(entry["task_ids"]) >= limit and len(entry["rationale_snippets"]) >= limit:
                continue
            task_id = row.get("task_id")
            snippet = row.get("rationale_snippet")
            if task_id is not None and task_id not in entry["task_ids"]:
                entry["task_ids"].append(task_id)
            if snippet and snippet not in entry["rationale_snippets"]:
                entry["rationale_snippets"].append(snippet)
        if limit:
            for entry in evidence_map.values():
                entry["task_ids"] = entry["task_ids"][:limit]
                entry["rationale_snippets"] = entry["rationale_snippets"][:limit]
        return evidence_map

    async def fetch_latest_learning_rollouts_map(
        self,
        learning_ids: Sequence[str],
    ) -> dict[str, dict[str, Any]]:
        if not learning_ids:
            return {}
        pool = self._require_pool()
        async with pool.acquire() as connection:
            rows = await connection.fetch(
                "SELECT DISTINCT ON (learning_id) learning_id, previous_status, new_status, reason, created_at"
                " FROM learning_rollouts"
                " WHERE learning_id = ANY($1)"
                " ORDER BY learning_id, created_at DESC",
                list(learning_ids),
            )
        return {row["learning_id"]: dict(row) for row in rows}

    async def insert_learning_objects(
        self,
        learning_key: str,
        objects: Sequence[dict[str, Any]],
        *,
        project_id: str | None = None,
        org_id: str | None = None,
        user_id: str | None = None,
    ) -> list[str]:
        if not learning_key or not objects:
            return []
        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("project_id is required to insert learning objects")
        if not isinstance(org_id, str) or not org_id.strip():
            raise ValueError("org_id is required to insert learning objects")
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("user_id is required to insert learning objects")
        learning_ids = [obj.get("learning_id") for obj in objects if obj.get("learning_id")]
        if not learning_ids:
            return []
        existing = await self.fetch_existing_learning_ids(learning_ids)
        to_insert = [obj for obj in objects if obj.get("learning_id") not in existing]
        to_update = [obj for obj in objects if obj.get("learning_id") in existing]
        pool = self._require_pool()
        async with pool.acquire() as connection:
            if to_insert:
                records = []
                for obj in to_insert:
                    records.append(
                        (
                            obj["learning_id"],
                            learning_key,
                            int(obj.get("version") or 1),
                            obj.get("status") or "pending",
                            obj.get("agent_id") or "",
                            project_id.strip(),
                            org_id.strip(),
                            user_id.strip(),
                            obj.get("learning") or "",
                            obj.get("expected_outcome") or "",
                            obj.get("basis") or "",
                            float(obj.get("confidence") or 0.0),
                        )
                    )
                await connection.executemany(
                    "INSERT INTO learning_objects("
                    "learning_id, learning_key, version, status, agent_id, project_id, org_id, user_id,"
                    " learning, expected_outcome, basis, confidence"
                    ") VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)",
                    records,
                )
            for obj in to_update:
                await connection.execute(
                    "UPDATE learning_objects SET"
                    " confidence = GREATEST(confidence, $2),"
                    " updated_at = NOW()"
                    " WHERE learning_id = $1",
                    obj.get("learning_id"),
                    float(obj.get("confidence") or 0.0),
                )
        return [obj["learning_id"] for obj in to_insert if obj.get("learning_id")]

    async def fetch_existing_learning_ids(self, learning_ids: Sequence[str]) -> set[str]:
        if not learning_ids:
            return set()
        pool = self._require_pool()
        async with pool.acquire() as connection:
            rows = await connection.fetch(
                "SELECT learning_id FROM learning_objects WHERE learning_id = ANY($1)",
                list(learning_ids),
            )
        return {row["learning_id"] for row in rows}

    async def insert_learning_evidence(
        self,
        records: Sequence[tuple[str, int, str]],
    ) -> None:
        if not records:
            return
        pool = self._require_pool()
        async with pool.acquire() as connection:
            task_ids = [record[1] for record in records]
            scope_map = await self._fetch_task_scopes(connection, task_ids)
            scoped_records = []
            for learning_id, task_id, snippet in records:
                scope = scope_map.get(task_id)
                if scope is None:
                    raise ValueError("learning evidence requires task scope")
                project_id, org_id, user_id = scope
                scoped_records.append((learning_id, task_id, project_id, org_id, user_id, snippet))
            await connection.executemany(
                "INSERT INTO learning_evidence(learning_id, task_id, project_id, org_id, user_id, rationale_snippet)"
                " VALUES ($1, $2, $3, $4, $5, $6)"
                " ON CONFLICT (learning_id, task_id) DO NOTHING",
                scoped_records,
            )

    async def upsert_learning_usage(
        self,
        records: Sequence[tuple[str, int, float | None, float | None, bool]],
    ) -> None:
        if not records:
            return
        pool = self._require_pool()
        async with pool.acquire() as connection:
            task_ids = [record[1] for record in records]
            scope_map = await self._fetch_task_scopes(connection, task_ids)
            scoped_records = []
            for record in records:
                learning_id, task_id = record[0], record[1]
                scope = scope_map.get(task_id)
                if scope is None:
                    raise ValueError("learning usage requires task scope")
                project_id, org_id, user_id = scope
                scoped_records.append(
                    (
                        learning_id,
                        task_id,
                        project_id,
                        org_id,
                        user_id,
                        record[2],
                        record[3],
                        record[4],
                    )
                )
            await connection.executemany(
                "INSERT INTO learning_usage("
                "learning_id, task_id, project_id, org_id, user_id, reward_score, token_total, failure_flag"
                ") VALUES ($1, $2, $3, $4, $5, $6, $7, $8)"
                " ON CONFLICT (learning_id, task_id) DO UPDATE SET"
                " reward_score = EXCLUDED.reward_score,"
                " token_total = EXCLUDED.token_total,"
                " failure_flag = EXCLUDED.failure_flag",
                scoped_records,
            )

    async def fetch_learning_usage_window(
        self,
        learning_id: str,
        *,
        window_size: int,
    ) -> List[dict[str, Any]]:
        if not learning_id:
            return []
        pool = self._require_pool()
        async with pool.acquire() as connection:
            rows = await connection.fetch(
                "SELECT learning_id, task_id, reward_score, token_total, failure_flag, created_at"
                " FROM learning_usage"
                " WHERE learning_id = $1"
                " ORDER BY created_at DESC"
                " LIMIT $2",
                learning_id,
                max(int(window_size), 1),
            )
        return [dict(row) for row in rows]

    async def update_learning_status(
        self,
        learning_id: str,
        *,
        status: str,
        project_id: str,
        org_id: str,
        user_id: str,
    ) -> None:
        if not learning_id:
            return
        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("project_id is required to update learning status")
        if not isinstance(org_id, str) or not org_id.strip():
            raise ValueError("org_id is required to update learning status")
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("user_id is required to update learning status")
        status_value = str(status or "").strip().lower()
        if status_value not in {"pending", "active", "inactive", "declined"}:
            raise ValueError(f"Unsupported learning status: {status}")
        pool = self._require_pool()
        async with pool.acquire() as connection:
            await connection.execute(
                "UPDATE learning_objects SET status = $2, updated_at = NOW()"
                " WHERE learning_id = $1 AND project_id = $3 AND org_id = $4 AND user_id = $5",
                learning_id,
                status_value,
                project_id.strip(),
                org_id.strip(),
                user_id.strip(),
            )

    async def record_learning_review(
        self,
        learning_id: str,
        *,
        project_id: str,
        org_id: str,
        user_id: str,
        decision: str,
        reason: str | None = None,
        edited_learning: str | None = None,
        edited_expected_outcome: str | None = None,
        edited_basis: str | None = None,
    ) -> None:
        if not learning_id:
            return
        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("project_id is required to record learning reviews")
        if not isinstance(org_id, str) or not org_id.strip():
            raise ValueError("org_id is required to record learning reviews")
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("user_id is required to record learning reviews")
        if not isinstance(decision, str) or not decision.strip():
            raise ValueError("decision is required to record learning reviews")
        pool = self._require_pool()
        async with pool.acquire() as connection:
            await connection.execute(
                "INSERT INTO learning_reviews("
                "learning_id, project_id, org_id, user_id, decision, reason,"
                " edited_learning, edited_expected_outcome, edited_basis"
                ") VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)",
                learning_id,
                project_id.strip(),
                org_id.strip(),
                user_id.strip(),
                decision.strip(),
                reason,
                edited_learning,
                edited_expected_outcome,
                edited_basis,
            )

    async def fetch_learning_reviews(
        self,
        learning_id: str,
        *,
        project_id: str,
        org_id: str,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[dict[str, Any]]:
        if not learning_id:
            return []
        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("project_id is required to fetch learning reviews")
        if not isinstance(org_id, str) or not org_id.strip():
            raise ValueError("org_id is required to fetch learning reviews")
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("user_id is required to fetch learning reviews")
        pool = self._require_pool()
        async with pool.acquire() as connection:
            rows = await connection.fetch(
                "SELECT id, learning_id, project_id, org_id, user_id, decision, reason,"
                " edited_learning, edited_expected_outcome, edited_basis, created_at"
                " FROM learning_reviews"
                " WHERE learning_id = $1 AND project_id = $2 AND org_id = $3 AND user_id = $4"
                " ORDER BY created_at DESC"
                " LIMIT $5 OFFSET $6",
                learning_id,
                project_id.strip(),
                org_id.strip(),
                user_id.strip(),
                max(int(limit), 1),
                max(int(offset), 0),
            )
        return [dict(row) for row in rows]

    async def log_learning_rollout(
        self,
        learning_id: str,
        *,
        previous_status: str | None,
        new_status: str,
        reason: str,
    ) -> None:
        if not learning_id:
            return
        pool = self._require_pool()
        async with pool.acquire() as connection:
            project_id, org_id, user_id = await self._fetch_learning_scope_for_id(connection, learning_id)
            if not project_id or not org_id or not user_id:
                raise ValueError("learning scope is required to log learning rollouts")
            await connection.execute(
                "INSERT INTO learning_rollouts("
                "learning_id, previous_status, new_status, reason, project_id, org_id, user_id"
                ") VALUES ($1, $2, $3, $4, $5, $6, $7)",
                learning_id,
                previous_status,
                new_status,
                reason,
                project_id,
                org_id,
                user_id,
            )

    def _learning_object_from_row(self, row: Any) -> dict[str, Any]:
        return dict(row)

    async def fetch_trajectory_events(
        self,
        session_id: int,
        *,
        task_id: int | None = None,
        limit: int | None = 200,
    ) -> List[dict[str, Any]]:
        pool = self._require_pool()
        params: list[Any] = [session_id]
        clauses: list[str] = ["session_id = $1"]
        if isinstance(task_id, int):
            params.append(task_id)
            clauses.append(f"(event->>'task_id')::bigint = ${len(params)}")
        where_clause = " AND ".join(clauses)
        async with pool.acquire() as connection:
            if limit is None:
                rows = await connection.fetch(
                    "SELECT id, event, created_at FROM trajectory_events"
                    f" WHERE {where_clause} ORDER BY id DESC",
                    *params,
                )
            else:
                params.append(limit)
                rows = await connection.fetch(
                    "SELECT id, event, created_at FROM trajectory_events"
                    f" WHERE {where_clause} ORDER BY id DESC LIMIT ${len(params)}",
                    *params,
                )
        return [dict(row) for row in rows]

    async def fetch_session_agents(self, session_id: int) -> List[dict[str, Any]]:
        pool = self._require_pool()
        async with pool.acquire() as connection:
            rows = await connection.fetch(
                "SELECT sa.agent_id, sa.parent_agent_id, sa.invocation_id, sa.definition_hash, sa.created_at,"
                " ar.name, ar.system_prompt, ar.tool_definitions, ar.mcp_definitions, ar.model_config"
                " FROM session_agents sa"
                " JOIN agent_registry ar ON sa.definition_hash = ar.definition_hash"
                " WHERE sa.session_id = $1"
                " ORDER BY sa.created_at ASC",
                session_id,
            )
        results: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            item["tool_definitions"] = self._deserialize_json(item.get("tool_definitions"))
            item["mcp_definitions"] = self._deserialize_json(item.get("mcp_definitions"))
            item["model_config"] = self._deserialize_json(item.get("model_config"))
            results.append(item)
        return results

    async def fetch_session_tool_names(self, session_id: int) -> list[str]:
        if not session_id:
            return []
        agents = await self.fetch_session_agents(session_id)
        tool_names: list[str] = []
        for agent in agents:
            definitions = agent.get("tool_definitions")
            if isinstance(definitions, dict):
                definitions = definitions.get("tools") or definitions.get("definitions")
            if not isinstance(definitions, list):
                continue
            for tool in definitions:
                if isinstance(tool, dict):
                    name = tool.get("name")
                    if isinstance(name, str) and name.strip() and name.strip() not in tool_names:
                        tool_names.append(name.strip())
        return tool_names

    async def enqueue_reward_job(self, session_id: int) -> None:
        await self.enqueue_reward_jobs_for_session(session_id)

    async def enqueue_reward_jobs_for_session(self, session_id: int) -> None:
        pool = self._require_pool()
        async with pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute(
                    "SELECT id FROM sessions WHERE id = $1 FOR UPDATE",
                    session_id,
                )
                await connection.execute(
                    "INSERT INTO reward_jobs(session_id, task_id, scope, agent_id, project_id, org_id, user_id)"
                    " SELECT $1, t.id, 'task', '', s.project_id, s.org_id, s.user_id"
                    " FROM session_tasks t"
                    " JOIN sessions s ON s.id = t.session_id"
                    " WHERE t.session_id = $1 AND t.completed_at IS NOT NULL"
                    " ON CONFLICT (session_id, task_id, scope, COALESCE(agent_id, '')) DO NOTHING",
                    session_id,
                )

    async def process_reward_jobs_for_session(self, session_id: int) -> None:
        await self.enqueue_reward_jobs_for_session(session_id)
        pool = self._require_pool()
        async with pool.acquire() as connection:
            rows = await connection.fetch(
                "SELECT session_id, task_id, scope, agent_id, project_id"
                " FROM reward_jobs WHERE session_id = $1 AND status = 'pending'"
                " ORDER BY updated_at ASC",
                session_id,
            )
        for row in rows:
            scope = row.get("scope")
            agent_id = row.get("agent_id")
            task_id = row.get("task_id")
            project_id = row.get("project_id")
            claimed = await self.mark_reward_job_running(session_id, task_id, scope, agent_id)
            if not claimed:
                continue
            try:
                await _process_reward_job(self, session_id, task_id, scope, agent_id, project_id)
            except Exception as exc:
                logger.exception("Reward job failed: session=%s task=%s scope=%s", session_id, task_id, scope)
                await self.mark_reward_job_failed(session_id, task_id, scope, agent_id, str(exc))

    async def fetch_pending_reward_job(self, limit: int = 10) -> List[dict[str, Any]]:
        pool = self._require_pool()
        async with pool.acquire() as connection:
            rows = await connection.fetch(
                "SELECT session_id, task_id, scope, agent_id, project_id, status, attempts, last_error, created_at, updated_at"
                " FROM reward_jobs WHERE status = 'pending' ORDER BY updated_at ASC LIMIT $1",
                limit,
            )
        return [dict(row) for row in rows]

    async def mark_reward_job_running(
        self,
        session_id: int,
        task_id: int | None,
        scope: str,
        agent_id: str | None,
    ) -> bool:
        pool = self._require_pool()
        async with pool.acquire() as connection:
            result = await connection.execute(
                "UPDATE reward_jobs SET status = 'running', attempts = attempts + 1, updated_at = NOW()"
                " WHERE session_id = $1 AND task_id IS NOT DISTINCT FROM $2 AND scope = $3"
                " AND agent_id IS NOT DISTINCT FROM $4"
                " AND status = 'pending'",
                session_id,
                task_id,
                scope,
                agent_id,
            )
        return result.endswith("1")

    async def mark_reward_job_succeeded(
        self,
        session_id: int,
        task_id: int | None,
        scope: str,
        agent_id: str | None,
    ) -> None:
        pool = self._require_pool()
        async with pool.acquire() as connection:
            await connection.execute(
                "UPDATE reward_jobs SET status = 'succeeded', updated_at = NOW()"
                " WHERE session_id = $1 AND task_id IS NOT DISTINCT FROM $2 AND scope = $3"
                " AND agent_id IS NOT DISTINCT FROM $4",
                session_id,
                task_id,
                scope,
                agent_id,
            )

    async def mark_reward_job_failed(
        self,
        session_id: int,
        task_id: int | None,
        scope: str,
        agent_id: str | None,
        error: str,
    ) -> None:
        pool = self._require_pool()
        async with pool.acquire() as connection:
            await connection.execute(
                "UPDATE reward_jobs SET status = 'failed', last_error = $5, updated_at = NOW()"
                " WHERE session_id = $1 AND task_id IS NOT DISTINCT FROM $2 AND scope = $3"
                " AND agent_id IS NOT DISTINCT FROM $4",
                session_id,
                task_id,
                scope,
                agent_id,
                error,
            )

    async def query_training_sessions(
        self,
        *,
        min_reward: Optional[float] = None,
        created_after: Optional[datetime] = None,
        learning_key: Optional[str] = None,
        status_filters: Optional[Sequence[str]] = None,
        review_status_filters: Optional[Sequence[str]] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[dict[str, Any]]:
        """
        Query sessions with reward-based filtering.

        Extracts reward score from JSONB for comparison.
        """
        pool = self._require_pool()
        constraints: list[str] = []
        params: list[Any] = []

        if min_reward is not None:
            params.append(min_reward)
            constraints.append(
                f"(reward_stats IS NOT NULL AND (reward_stats->>'score')::float >= ${len(params)})"
            )

        if created_after is not None:
            params.append(created_after)
            constraints.append(f"created_at >= ${len(params)}")

        if learning_key is not None:
            params.append(learning_key)
            constraints.append(f"(metadata->>'learning_key') = ${len(params)}")

        if status_filters:
            params.append(list(status_filters))
            constraints.append(f"status = ANY(${len(params)})")

        if review_status_filters:
            params.append(list(review_status_filters))
            constraints.append(f"review_status = ANY(${len(params)})")

        where_clause = " AND ".join(constraints) if constraints else "TRUE"

        query = (
            "SELECT s.id, s.task, s.status, s.review_status, s.review_notes, s.metadata, "
            "s.final_answer, s.reward, s.reward_stats, s.reward_audit, "
            "s.learning, s.created_at, s.completed_at "
            "FROM sessions s "
            f"WHERE {where_clause} "
            "ORDER BY s.created_at DESC"
        )

        if limit is not None:
            params.append(limit)
            query += f" LIMIT ${len(params)}"
            params.append(offset)
            query += f" OFFSET ${len(params)}"
        else:
            params.append(offset)
            query += f" OFFSET ${len(params)}"

        async with pool.acquire() as connection:
            rows = await connection.fetch(query, *params)

        results: list[dict[str, Any]] = []
        for row in rows:
            session_dict = dict(row)
            results.append(session_dict)

        return results


    async def update_session_metadata(self, session_id: int, metadata: Dict[str, Any]) -> None:
        """Replace metadata payload for a session."""
        pool = self._require_pool()
        payload = self._serialize_json(metadata) if metadata is not None else None
        async with pool.acquire() as connection:
            await connection.execute(
                "UPDATE sessions SET metadata = $2 WHERE id = $1",
                session_id,
                payload,
            )

    async def fetch_feedback_chunk(
        self,
        project_id: str,
        chunk_type: str,
    ) -> str | None:
        """Fetch feedback chunk for a project."""
        if not project_id or not chunk_type:
            return None
        if chunk_type not in ("reward", "learning"):
            return None
        pool = self._require_pool()
        async with pool.acquire() as connection:
            row = await connection.fetchrow(
                "SELECT chunk_content FROM project_feedback_chunks"
                " WHERE project_id = $1 AND chunk_type = $2",
                project_id,
                chunk_type,
            )
        if row is None:
            return None
        return row.get("chunk_content")

    async def fetch_all_feedback_chunks(
        self,
        project_id: str,
    ) -> dict[str, str]:
        """Fetch both feedback chunks for a project in a single query."""
        if not project_id:
            return {"reward": "", "learning": ""}
        pool = self._require_pool()
        async with pool.acquire() as connection:
            rows = await connection.fetch(
                "SELECT chunk_type, chunk_content FROM project_feedback_chunks"
                " WHERE project_id = $1",
                project_id,
            )
        result = {"reward": "", "learning": ""}
        for row in rows:
            chunk_type = row.get("chunk_type")
            if chunk_type in result:
                result[chunk_type] = row.get("chunk_content") or ""
        return result

    async def upsert_feedback_chunk(
        self,
        project_id: str,
        chunk_type: str,
        chunk_content: str,
    ) -> None:
        """Insert or update feedback chunk for a project."""
        if not project_id or not chunk_type:
            return
        if chunk_type not in ("reward", "learning"):
            return
        pool = self._require_pool()
        async with pool.acquire() as connection:
            await connection.execute(
                "INSERT INTO project_feedback_chunks(project_id, chunk_type, chunk_content)"
                " VALUES ($1, $2, $3)"
                " ON CONFLICT (project_id, chunk_type) DO UPDATE SET"
                " chunk_content = EXCLUDED.chunk_content,"
                " version = project_feedback_chunks.version + 1,"
                " updated_at = NOW()",
                project_id,
                chunk_type,
                chunk_content or "",
            )

    async def log_feedback_history(
        self,
        project_id: str,
        feedback_type: str,
        context_data: Dict[str, Any],
        user_feedback: str,
        chunk_before: str | None,
        chunk_after: str | None,
    ) -> None:
        """Log feedback history for audit trail."""
        if not project_id or not feedback_type:
            return
        pool = self._require_pool()
        async with pool.acquire() as connection:
            await connection.execute(
                "INSERT INTO feedback_history("
                "project_id, feedback_type, context_data, user_feedback, chunk_before, chunk_after"
                ") VALUES ($1, $2, $3, $4, $5, $6)",
                project_id,
                feedback_type,
                self._serialize_json(context_data),
                user_feedback,
                chunk_before,
                chunk_after,
            )

    @staticmethod
    def _aggregate_reward_baseline(
        entries: Iterable[Dict[str, Any]],
        *,
        window: int,
    ) -> dict[str, Any]:
        snapshots = list(entries)
        sample_count = len(snapshots)
        score_values: list[float] = []
        uncertainty_values: list[float] = []
        best_uncertainties: list[float] = []
        for snapshot in snapshots:
            score_value = Database._coerce_float(
                snapshot.get("score_mean", snapshot.get("score"))
            )
            if score_value is not None:
                score_values.append(score_value)
            uncertainty_mean = Database._coerce_float(snapshot.get("uncertainty_mean"))
            if uncertainty_mean is not None:
                uncertainty_values.append(uncertainty_mean)
            best_uncertainty = Database._coerce_float(
                snapshot.get("best_uncertainty", snapshot.get("min_uncertainty"))
            )
            if best_uncertainty is not None:
                best_uncertainties.append(best_uncertainty)
        baseline: dict[str, Any] = {
            "window": window,
            "sample_count": sample_count,
            "score_mean": fmean(score_values) if score_values else None,
            "score_median": median(score_values) if score_values else None,
            "score_stddev": pstdev(score_values) if len(score_values) > 1 else (0.0 if score_values else None),
            "uncertainty_mean": fmean(uncertainty_values) if uncertainty_values else None,
            "uncertainty_median": median(uncertainty_values) if uncertainty_values else None,
            "uncertainty_stddev": pstdev(uncertainty_values) if len(uncertainty_values) > 1 else (0.0 if uncertainty_values else None),
            "best_uncertainty_mean": fmean(best_uncertainties) if best_uncertainties else None,
            "best_uncertainty_median": median(best_uncertainties) if best_uncertainties else None,
            "best_uncertainty_stddev": pstdev(best_uncertainties) if len(best_uncertainties) > 1 else (0.0 if best_uncertainties else None),
            "scores": score_values,
            "uncertainties": uncertainty_values,
            "best_uncertainties": best_uncertainties,
        }
        return baseline

    @staticmethod
    def _coerce_float(value: Any) -> float | None:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    def _require_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("Database connection has not been established")
        return self._pool

    @staticmethod
    def _coerce_event_payload(event: Any) -> Dict[str, Any]:
        if hasattr(event, "to_dict"):
            payload = event.to_dict()
        elif hasattr(event, "model_dump"):
            payload = event.model_dump()
        elif isinstance(event, dict):
            payload = event
        else:
            payload = getattr(event, "__dict__", {})
        return dict(payload) if isinstance(payload, dict) else {}

    @staticmethod
    def _is_agent_definition_event(payload: Dict[str, Any]) -> bool:
        event_type = payload.get("event_type") or payload.get("type")
        return event_type == "agent_definition"

    @staticmethod
    def _serialize_json(data: Any) -> str | None:
        """Convert data to JSON string for asyncpg JSONB columns."""
        if data is None:
            return None
        try:
            return json.dumps(data, default=str)
        except (TypeError, ValueError):
            return json.dumps(str(data))

    @staticmethod
    def _deserialize_json(data: Any) -> Any:
        """Convert JSON payloads retrieved from the database into Python objects."""
        if data is None or isinstance(data, (dict, list)):
            return data
        try:
            return json.loads(data)
        except (TypeError, ValueError):
            return data


async def process_reward_jobs(config: StorageConfig, *, limit: int = 10) -> int:
    database = Database(config)
    await database.connect()
    processed = 0
    try:
        jobs = await database.fetch_pending_reward_job(limit=limit)
        for job in jobs:
            session_id = job.get("session_id")
            task_id = job.get("task_id")
            scope = job.get("scope")
            agent_id = job.get("agent_id")
            project_id = job.get("project_id")
            if not isinstance(session_id, int) or not isinstance(task_id, int) or not isinstance(scope, str) or not scope:
                continue
            if not isinstance(project_id, str) or not project_id.strip():
                continue
            claimed = await database.mark_reward_job_running(session_id, task_id, scope, agent_id)
            if not claimed:
                continue
            await _process_reward_job(database, session_id, task_id, scope, agent_id, project_id)
            processed += 1
    except Exception as exc:
        logger.warning("Failed while processing reward jobs: %s", exc, exc_info=True)
    finally:
        await database.disconnect()
    return processed


async def _process_reward_job(
    database: Database,
    session_id: int,
    task_id: int | None,
    scope: str,
    agent_id: str | None,
    project_id: str | None,
) -> None:
    if not isinstance(project_id, str) or not project_id.strip():
        await database.mark_reward_job_failed(session_id, task_id, scope, agent_id, "project_id_missing")
        return
    project_id = project_id.strip()
    session = await database.fetch_session(session_id, project_id=project_id)
    if session is None:
        await database.mark_reward_job_failed(session_id, task_id, scope, agent_id, "session_not_found")
        return
    if not isinstance(task_id, int):
        await database.mark_reward_job_failed(session_id, task_id, scope, agent_id, "task_id_missing")
        return
    task_row = await database.fetch_task(task_id, project_id=project_id)
    if task_row is None:
        await database.mark_reward_job_failed(session_id, task_id, scope, agent_id, "task_not_found")
        return

    session_metadata = database._deserialize_json(session.get("metadata")) or {}
    if not isinstance(session_metadata, dict):
        session_metadata = {}
    task_metadata = database._deserialize_json(task_row.get("metadata")) or {}
    if not isinstance(task_metadata, dict):
        task_metadata = {}
    if "learning_key" not in task_metadata and session_metadata.get("learning_key"):
        task_metadata["learning_key"] = session_metadata.get("learning_key")
    project_id = task_row.get("project_id") or session.get("project_id")
    org_id = task_row.get("org_id") or session.get("org_id")
    user_id = task_row.get("user_id") or session.get("user_id")

    task_text = task_row.get("task") or ""
    final_answer = task_row.get("final_answer") or ""

    events_rows = await database.fetch_trajectory_events(session_id, task_id=task_id, limit=None)
    events = normalize_events(events_rows, deserialize=database._deserialize_json)
    use_memory = _estimate_event_tokens(events) > 100000
    agents = await database.fetch_session_agents(session_id)
    agents_by_id = {agent["agent_id"]: agent for agent in agents if isinstance(agent.get("agent_id"), str)}
    agent_ids_ordered = [agent["agent_id"] for agent in agents if isinstance(agent.get("agent_id"), str)]

    root_agent_id, parent_map, children_map = resolve_agent_tree(agent_ids_ordered, agents_by_id, events)

    trajectory_context: dict[str, Any] | None = None
    agent_context: dict[str, Any] | None = None
    if scope == "task":
        if not use_memory:
            trajectory_context = build_task_trajectory_context(
                root_agent_id,
                events,
                agents_by_id,
                parent_map,
                children_map,
                task_id=task_id,
                task=task_text,
            )
        if root_agent_id and root_agent_id in agents_by_id:
            root_events = filter_events_by_agents(events, {root_agent_id})
            agent_context = build_agent_context(agents_by_id[root_agent_id], root_events)
    elif scope == "agent":
        if not isinstance(agent_id, str) or not agent_id:
            error_message = "agent_scope_missing_agent_id"
            await database.mark_reward_job_failed(session_id, task_id, scope, agent_id, error_message)
            return
        if agent_id not in agents_by_id:
            error_message = "agent_not_found"
            await database.log_agent_reward(session_id, task_id, agent_id, error=error_message)
            await database.mark_reward_job_failed(session_id, task_id, scope, agent_id, error_message)
            return
        subtree_ids = collect_subtree_ids(agent_id, children_map)
        subtree_events = filter_events_by_agents(events, subtree_ids)
        if not use_memory:
            trajectory_context = build_agent_trajectory_context(
                agent_id,
                subtree_ids,
                subtree_events,
                agents_by_id,
                parent_map,
                children_map,
            )
        agent_context = build_agent_context(agents_by_id[agent_id], subtree_events)
    else:
        await database.mark_reward_job_failed(session_id, task_id, scope, agent_id, "invalid_scope")
        return

    context = ExecutionContext.get()
    previous_metadata = context.metadata
    try:
        context.metadata = {
            "session_metadata": session_metadata,
            "task_metadata": task_metadata,
            "session_id": session_id,
            "task_id": task_id,
        }
        if "learning_state" in session_metadata:
            context.metadata["learning_state"] = session_metadata.get("learning_state")

        if use_memory and not task_metadata.get("context_memory_state"):
            try:
                manager = MarloContextManager([TraceMemoryProvider()])
                await manager.get_context(task_text, trace_history=events, metadata={"task_metadata": task_metadata})
            except Exception as exc:
                task_metadata["context_memory_error"] = {"message": str(exc)[:500]}

        reward_result = await evaluate_session(
            task_text,
            str(final_answer),
            context,
            agent_context=agent_context,
            trajectory_context=trajectory_context,
            user_id=user_id,
            project_id=project_id,
        )
        if not reward_result:
            reward_error = task_metadata.get("reward_error")
            if reward_error is None:
                reward_error = {"message": "Reward evaluation returned no result."}
                task_metadata["reward_error"] = reward_error
            error_message = _format_reward_error(reward_error)
            if scope == "task":
                await database.update_task_metadata(task_id, task_metadata)
            else:
                if isinstance(agent_id, str) and agent_id:
                    await database.log_agent_reward(session_id, task_id, agent_id, error=error_message)
            await database.mark_reward_job_failed(session_id, task_id, scope, agent_id, error_message)
            return

        score = reward_result.get("score") if isinstance(reward_result, dict) else None
        if scope == "task":
            reward_stats = None
            if score is not None:
                reward_stats = {
                    "score": score,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            reward_audit = context.metadata.get("task_reward_audit")
            await database.log_task_reward(
                task_id,
                reward_result,
                context.metadata.get("task_learning"),
                reward_stats if isinstance(reward_stats, dict) else None,
                reward_audit if isinstance(reward_audit, list) else None,
            )
            context.metadata["task_reward"] = reward_result
            if reward_stats:
                context.metadata["task_reward_stats"] = reward_stats
            task_metadata.pop("reward_error", None)
            await process_learning_update(
                database,
                session_id=session_id,
                task_id=task_id,
                reward_result=reward_result,
                task_metadata=task_metadata,
                project_id=project_id,
                org_id=org_id,
                user_id=user_id,
            )
            await database.update_task_metadata(task_id, task_metadata)
        else:
            if isinstance(agent_id, str) and agent_id:
                await database.log_agent_reward(
                    session_id,
                    task_id,
                    agent_id,
                    score=score if isinstance(score, (int, float)) else None,
                    rationale=reward_result.get("rationale"),
                    principles=reward_result.get("principles"),
                    error=None,
                )
        await database.mark_reward_job_succeeded(session_id, task_id, scope, agent_id)
    except Exception as exc:
        error_message = str(exc)[:500]
        if scope == "task":
            task_metadata["reward_error"] = {"message": error_message}
            try:
                await database.update_task_metadata(task_id, task_metadata)
            except Exception:
                pass
        else:
            if isinstance(agent_id, str) and agent_id:
                try:
                    await database.log_agent_reward(session_id, task_id, agent_id, error=error_message)
                except Exception:
                    pass
        logger.warning(
            "Reward job for task %s scope %s failed: %s",
            task_id,
            scope,
            error_message,
            exc_info=True,
        )
        await database.mark_reward_job_failed(session_id, task_id, scope, agent_id, error_message)
    finally:
        context.metadata = previous_metadata


def _estimate_event_tokens(events: Sequence[Any]) -> float:
    try:
        return len(json.dumps(events, default=str)) / 4
    except (TypeError, ValueError):
        return float(len(str(events))) / 4


def _format_reward_error(payload: Any) -> str:
    if isinstance(payload, dict):
        message = payload.get("message") or payload.get("detail") or str(payload)
    else:
        message = str(payload)
    return message[:500] if message else "reward_evaluation_failed"

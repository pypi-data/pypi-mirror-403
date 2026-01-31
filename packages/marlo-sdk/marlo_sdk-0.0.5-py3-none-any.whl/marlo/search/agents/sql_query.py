"""SQL Query Agent for deep search - uses dynamic schema introspection."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any

from marlo.search.schema.search_state import SearchPlan, SubQuery
from marlo.search.prompts.sql_query import build_sql_generation_prompt
from marlo.search.sql_validator import validate_sql
from marlo.search.schema_introspection import get_schema_introspector

logger = logging.getLogger(__name__)


@dataclass
class SQLQueryResult:
    """Result from SQL query generation."""

    query: str
    params: list[Any]
    description: str
    is_safe: bool
    validation_errors: list[str]
    sub_query_description: str = ""
    sub_query_hint: str = ""
    raw_llm_response: str = ""


class SQLQueryAgent:
    """Agent that generates and executes SQL queries for trajectory search."""

    def __init__(self, llm_client: Any, pool: Any):
        self.llm_client = llm_client
        self.pool = pool
        self._schema_context_cache: dict[str, str] = {}

    async def _get_schema_context(self, project_id: str) -> str:
        """Get dynamic schema context for a project."""
        if project_id in self._schema_context_cache:
            return self._schema_context_cache[project_id]

        try:
            introspector = get_schema_introspector(self.pool)
            schema = await introspector.get_schema(project_id)
            context = schema.to_prompt_context()
            self._schema_context_cache[project_id] = context
            logger.info(f"Generated schema context for project {project_id}: {len(context)} chars")
            return context
        except Exception as e:
            logger.warning(f"Failed to introspect schema: {e}")
            return "Schema introspection failed. Generate safe generic queries."

    async def generate_query(
        self,
        search_plan: SearchPlan,
        sub_query: SubQuery,
        project_id: str,
    ) -> SQLQueryResult:
        """Generate a SQL query from search plan and sub-query using dynamic schema."""
        schema_context = await self._get_schema_context(project_id)

        search_plan_json = json.dumps({
            "intent": search_plan.intent,
            "search_strategy": search_plan.search_strategy,
            "filters": search_plan.filters,
            "priority_fields": search_plan.priority_fields,
        }, indent=2)

        sub_query_text = f"Description: {sub_query.description}\nSQL Hint: {sub_query.sql_hint}"

        prompt = build_sql_generation_prompt(
            schema_context=schema_context,
            search_plan_json=search_plan_json,
            sub_query=sub_query_text,
        )

        try:
            logger.debug(f"Generating SQL for: {sub_query.description}")
            response = await self.llm_client.acomplete(
                messages=[{"role": "user", "content": prompt}],
            )
            result = self._parse_sql_response(response.content, project_id)
            result.sub_query_description = sub_query.description
            result.sub_query_hint = sub_query.sql_hint
            result.raw_llm_response = response.content
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            result = SQLQueryResult(
                query="",
                params=[project_id],
                description="",
                is_safe=False,
                validation_errors=[f"Generation failed: {str(e)}"],
                sub_query_description=sub_query.description,
                sub_query_hint=sub_query.sql_hint,
            )

        return result

    def _parse_sql_response(self, response: str, project_id: str) -> SQLQueryResult:
        """Parse LLM response and validate the generated SQL."""
        try:
            json_match = re.search(r"\{[\s\S]*\}", response)
            if not json_match:
                return SQLQueryResult(
                    query="",
                    params=[project_id],
                    description="",
                    is_safe=False,
                    validation_errors=["No JSON found in response"],
                )

            data = json.loads(json_match.group())
            query = data.get("query", "")
            params = data.get("params", [])
            description = data.get("description", "")

            if not params or params[0] != project_id:
                params = [project_id] + [p for p in params if p != project_id]

            is_safe, errors = self.validate_sql(query, params)

            return SQLQueryResult(
                query=query,
                params=params,
                description=description,
                is_safe=is_safe,
                validation_errors=errors,
            )
        except json.JSONDecodeError as e:
            return SQLQueryResult(
                query="",
                params=[project_id],
                description="",
                is_safe=False,
                validation_errors=[f"JSON parse error: {str(e)}"],
            )

    def validate_sql(self, query: str, params: list[Any]) -> tuple[bool, list[str]]:
        """Validate generated SQL for safety using AST-based validation."""
        result = validate_sql(query)
        return (result.is_valid, result.errors)

    async def execute_query(
        self,
        query_result: SQLQueryResult,
    ) -> tuple[list[dict[str, Any]], str | None, float]:
        """Execute a validated SQL query.

        Returns:
            Tuple of (results, error, execution_time_ms)
        """
        if not query_result.is_safe:
            return [], f"Query validation failed: {query_result.validation_errors}", 0.0

        import time
        start = time.perf_counter()
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query_result.query, *query_result.params)
            elapsed_ms = (time.perf_counter() - start) * 1000
            return [dict(row) for row in rows], None, elapsed_ms
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.error(f"Query execution failed: {e}")
            return [], str(e), elapsed_ms

    async def generate_and_execute(
        self,
        search_plan: SearchPlan,
        sub_query: SubQuery,
        project_id: str,
    ) -> tuple[list[dict[str, Any]], SQLQueryResult, float]:
        """Generate and execute a query in one step.

        Returns:
            Tuple of (results, query_result, execution_time_ms)
        """
        query_result = await self.generate_query(search_plan, sub_query, project_id)

        if not query_result.is_safe:
            return [], query_result, 0.0

        results, error, exec_time = await self.execute_query(query_result)
        if error:
            query_result.validation_errors.append(f"Execution error: {error}")
            query_result.is_safe = False

        return results, query_result, exec_time

    def clear_schema_cache(self) -> None:
        """Clear the schema context cache."""
        self._schema_context_cache.clear()

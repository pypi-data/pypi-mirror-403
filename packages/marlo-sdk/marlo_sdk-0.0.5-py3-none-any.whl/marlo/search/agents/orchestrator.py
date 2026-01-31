"""Orchestrator Agent for coordinating deep search - uses dynamic schema."""

from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any

from marlo.search.schema.search_state import SearchState, SearchPlan, SubQuery
from marlo.search.schema.findings import WeightedFact
from marlo.search.prompts.orchestrator import (
    build_query_understanding_prompt,
    build_synthesis_prompt,
)
from marlo.search.schema_introspection import get_schema_introspector

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """Agent that understands queries and coordinates the search pipeline."""

    def __init__(self, llm_client: Any, pool: Any | None = None):
        self.llm_client = llm_client
        self.pool = pool
        self._schema_context_cache: dict[str, str] = {}

    async def _get_schema_context(self, project_id: str) -> str:
        """Get dynamic schema context for a project."""
        if not self.pool:
            return "No database connection available for schema introspection."

        if project_id in self._schema_context_cache:
            return self._schema_context_cache[project_id]

        try:
            introspector = get_schema_introspector(self.pool)
            schema = await introspector.get_schema(project_id)
            context = schema.to_prompt_context()
            self._schema_context_cache[project_id] = context
            logger.info(f"Orchestrator: Generated schema context for project {project_id}")
            return context
        except Exception as e:
            logger.warning(f"Failed to introspect schema: {e}")
            return "Schema introspection failed."

    async def create_search_state(
        self,
        query: str,
        project_id: str,
    ) -> SearchState:
        """
        Initialize search state by understanding the user query.

        Args:
            query: User's natural language query
            project_id: Project scope for the search

        Returns:
            Initialized SearchState with search plan
        """
        search_id = str(uuid.uuid4())[:8]

        schema_context = await self._get_schema_context(project_id)
        prompt = build_query_understanding_prompt(query, schema_context)

        try:
            logger.debug(f"Understanding query: {query[:100]}...")
            response = await self.llm_client.acomplete(
                messages=[{"role": "user", "content": prompt}],
            )
            search_plan = self._parse_search_plan(response.content)
        except Exception as e:
            logger.error(f"Query understanding failed: {e}")
            search_plan = self._default_search_plan(query)

        return SearchState(
            search_id=search_id,
            original_query=query,
            project_id=project_id,
            search_plan=search_plan,
            status="planning",
        )

    def _parse_search_plan(self, response: str) -> SearchPlan:
        """Parse LLM response into SearchPlan."""
        try:
            json_match = re.search(r"\{[\s\S]*\}", response)
            if not json_match:
                raise ValueError("No JSON found")

            data = json.loads(json_match.group())

            sub_queries = []
            for sq in data.get("sub_queries", []):
                sub_queries.append(SubQuery(
                    description=sq.get("description", ""),
                    sql_hint=sq.get("sql_hint", ""),
                ))

            return SearchPlan(
                intent=data.get("intent", ""),
                filters=data.get("filters", {}),
                search_strategy=data.get("search_strategy", "focused"),
                priority_fields=data.get("priority_fields", []),
                sub_queries=sub_queries,
            )
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse search plan: {e}")
            return self._default_search_plan("")

    def _default_search_plan(self, query: str) -> SearchPlan:
        """Create a default search plan when parsing fails."""
        return SearchPlan(
            intent=f"Find information related to: {query}",
            filters={"time_range": "last_7_days", "status": "all"},
            search_strategy="broad",
            priority_fields=["task", "final_answer", "event"],
            sub_queries=[
                SubQuery(
                    description="Search sessions and tasks",
                    sql_hint="Find sessions matching the query terms",
                ),
                SubQuery(
                    description="Search trajectory events",
                    sql_hint="Find relevant events in trajectory_events",
                ),
            ],
        )

    async def evaluate_coverage(
        self,
        state: SearchState,
        facts: list[WeightedFact],
        patterns: list[str],
    ) -> tuple[float, bool, list[str]]:
        """
        Evaluate how well current findings answer the query.

        Returns:
            Tuple of (coverage_score, should_continue, refinement_suggestions)
        """
        if not facts:
            return 0.0, True, ["No facts found yet, broaden search"]

        facts_count = len(facts)
        if facts_count >= 10:
            return 0.8, False, []
        if facts_count >= 5:
            return 0.6, True, ["Continue to find more supporting evidence"]

        return 0.3, True, ["Few facts found, try different search terms"]

    def _summarize_facts(self, facts: list[WeightedFact]) -> str:
        """Create a summary of facts for evaluation."""
        lines = []
        for f in facts:
            lines.append(f"[{f.importance:.1f}] {f.content[:150]}...")
        return "\n".join(lines)

    def update_state_with_results(
        self,
        state: SearchState,
        events_count: int,
        sessions_count: int,
        facts_count: int,
        coverage_score: float,
    ) -> SearchState:
        """Update search state with results from current iteration."""
        state.total_events_searched += events_count
        state.total_sessions_searched += sessions_count
        state.total_facts_extracted += facts_count
        state.coverage_score = coverage_score
        state.increment_iteration()
        return state

    def clear_schema_cache(self) -> None:
        """Clear the schema context cache."""
        self._schema_context_cache.clear()

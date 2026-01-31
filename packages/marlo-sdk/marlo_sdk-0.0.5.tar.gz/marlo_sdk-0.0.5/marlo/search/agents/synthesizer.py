"""Synthesizer Agent for generating final search answers."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from marlo.search.schema.findings import WeightedFact, SynthesisResult
from marlo.search.schema.search_state import SearchState
from marlo.search.prompts.synthesizer import SYNTHESIS_PROMPT

logger = logging.getLogger(__name__)

MAX_FACTS_FOR_SYNTHESIS = 50
MAX_TOKENS_FOR_FACTS = 40_000


class SynthesizerAgent:
    """Agent that synthesizes findings into a coherent answer."""

    def __init__(self, llm_client: Any):
        self.llm_client = llm_client

    async def synthesize(
        self,
        search_state: SearchState,
        facts: list[WeightedFact],
        patterns: list[str],
    ) -> SynthesisResult:
        """
        Synthesize collected facts into a final answer.

        Args:
            search_state: Current search state with query and stats
            facts: Weighted facts from analysis (should be pre-sorted by importance)
            patterns: Patterns discovered during analysis

        Returns:
            SynthesisResult with answer and citations
        """
        # Limit facts to fit in context
        limited_facts = self._limit_facts(facts)

        prompt = SYNTHESIS_PROMPT.format(
            original_query=search_state.original_query,
            session_count=search_state.total_sessions_searched,
            event_count=search_state.total_events_searched,
            time_range=self._format_time_range(search_state),
            findings_json=self._format_facts(limited_facts),
            patterns=self._format_patterns(patterns),
        )

        try:
            response = await self.llm_client.acomplete(
                messages=[{"role": "user", "content": prompt}],
            )
            return self._parse_synthesis_response(response.content, search_state)
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return SynthesisResult(
                answer=f"Synthesis failed: {str(e)}",
                confidence=0.0,
                limitations=str(e),
            )

    def _limit_facts(self, facts: list[WeightedFact]) -> list[WeightedFact]:
        """Limit facts to fit within token budget."""
        limited = []
        total_chars = 0
        max_chars = MAX_TOKENS_FOR_FACTS * 4  # ~4 chars per token

        for fact in facts[:MAX_FACTS_FOR_SYNTHESIS]:
            fact_chars = len(fact.content) + 100  # Extra for metadata
            if total_chars + fact_chars > max_chars:
                break
            limited.append(fact)
            total_chars += fact_chars

        return limited

    def _format_facts(self, facts: list[WeightedFact]) -> str:
        """Format facts as JSON for the prompt."""
        formatted = []
        for f in facts:
            formatted.append({
                "content": f.content,
                "importance": f.importance,
                "source": {
                    "session_id": f.source_session_id,
                    "event_id": f.source_event_id,
                    "event_type": f.event_type,
                    "agent_id": f.agent_id,
                },
            })
        return json.dumps(formatted, indent=2)

    def _format_patterns(self, patterns: list[str]) -> str:
        """Format patterns for the prompt."""
        if not patterns:
            return "No clear patterns identified."
        return "\n".join(f"- {p}" for p in patterns[:10])

    def _format_time_range(self, state: SearchState) -> str:
        """Format time range from search state."""
        filters = state.search_plan.filters if state.search_plan else {}
        start = filters.get("start_time", "N/A")
        end = filters.get("end_time", "N/A")
        if start == "N/A" and end == "N/A":
            return "All available data"
        return f"{start} to {end}"

    def _parse_synthesis_response(
        self,
        response: str,
        search_state: SearchState,
    ) -> SynthesisResult:
        """Parse LLM response into SynthesisResult."""
        try:
            json_match = re.search(r"\{[\s\S]*\}", response)
            if not json_match:
                return SynthesisResult(
                    answer=response,  # Use raw response if no JSON
                    confidence=0.5,
                    limitations="Could not parse structured response",
                )

            data = json.loads(json_match.group())

            return SynthesisResult(
                answer=data.get("answer", "No answer generated"),
                confidence=float(data.get("confidence", 0.5)),
                key_findings=data.get("key_findings", []),
                evidence_citations=data.get("evidence_citations", []),
                patterns_discovered=data.get("patterns_discovered", []),
                data_coverage=data.get("data_coverage", {
                    "sessions_analyzed": search_state.total_sessions_searched,
                    "events_analyzed": search_state.total_events_searched,
                }),
                limitations=data.get("limitations"),
                suggested_follow_ups=data.get("suggested_follow_ups", []),
            )
        except json.JSONDecodeError:
            return SynthesisResult(
                answer=response,
                confidence=0.5,
                limitations="Could not parse structured response",
            )

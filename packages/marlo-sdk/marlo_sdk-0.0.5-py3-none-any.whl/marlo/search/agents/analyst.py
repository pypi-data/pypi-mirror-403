"""Analyst Agent for deep trajectory analysis."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, AsyncIterator

from marlo.search.schema.findings import WeightedFact, AnalysisResult
from marlo.search.storage.hot_storage import HotStorageManager
from marlo.search.prompts.analyst import ANALYSIS_PROMPT

logger = logging.getLogger(__name__)

CHUNK_SIZE_TOKENS = 100_000
RELEVANCE_THRESHOLD = 0.3
MAX_FACTS_PER_CHUNK = 50


class AnalystAgent:
    """Agent that analyzes trajectory events in chunks."""

    def __init__(self, llm_client: Any, hot_storage: HotStorageManager):
        self.llm_client = llm_client
        self.hot_storage = hot_storage

    async def analyze_search_results(
        self,
        search_id: str,
        search_context: str,
    ) -> AsyncIterator[AnalysisResult]:
        """
        Analyze all results in hot storage, yielding results per chunk.

        Args:
            search_id: ID of the search in hot storage
            search_context: Description of what we're searching for

        Yields:
            AnalysisResult for each processed chunk
        """
        all_facts: list[WeightedFact] = []
        offset = 0

        while True:
            chunk, next_offset = await self.hot_storage.get_chunk(
                search_id=search_id,
                offset=offset,
                token_limit=CHUNK_SIZE_TOKENS,
            )

            if not chunk:
                break

            result = await self._analyze_chunk(
                events=chunk,
                search_context=search_context,
                existing_facts=all_facts[-20:],  # Pass recent facts for context
            )

            # Filter by relevance threshold
            result.facts = [f for f in result.facts if f.importance >= RELEVANCE_THRESHOLD]

            # Add to accumulated facts
            all_facts.extend(result.facts)

            yield result

            if next_offset == offset:
                break
            offset = next_offset

    async def _analyze_chunk(
        self,
        events: list[dict[str, Any]],
        search_context: str,
        existing_facts: list[WeightedFact],
    ) -> AnalysisResult:
        """Analyze a single chunk of events."""
        prompt = ANALYSIS_PROMPT.format(
            search_context=search_context,
            existing_facts=self._format_facts(existing_facts),
            events=self._format_events(events),
        )

        try:
            response = await self.llm_client.acomplete(
                messages=[{"role": "user", "content": prompt}],
            )
            return self._parse_analysis_response(response.content, len(events))
        except Exception as e:
            logger.error(f"Chunk analysis failed: {e}")
            return AnalysisResult(
                facts=[],
                patterns=[],
                suggested_refinements=[],
                events_processed=len(events),
                error=str(e),
            )

    def _format_facts(self, facts: list[WeightedFact]) -> str:
        """Format existing facts for prompt context."""
        if not facts:
            return "None yet."
        lines = []
        for f in facts[:10]:  # Limit to prevent prompt bloat
            lines.append(f"- [{f.importance:.1f}] {f.content[:100]}...")
        return "\n".join(lines)

    def _format_events(self, events: list[dict[str, Any]]) -> str:
        """Format events for analysis prompt."""
        formatted = []
        for i, event in enumerate(events[:100]):  # Limit events per chunk for prompt
            event_data = event.get("event", event)
            formatted.append(json.dumps({
                "index": i,
                "id": event.get("id"),
                "session_id": event.get("session_id"),
                "event_type": event_data.get("event_type") if isinstance(event_data, dict) else None,
                "agent_id": event_data.get("agent_id") if isinstance(event_data, dict) else None,
                "task_id": event_data.get("task_id") if isinstance(event_data, dict) else None,
                "payload": event_data.get("payload") if isinstance(event_data, dict) else event_data,
                "created_at": str(event.get("created_at", "")),
            }, default=str, indent=2))
        return "\n---\n".join(formatted)

    def _parse_analysis_response(self, response: str, events_count: int) -> AnalysisResult:
        """Parse LLM analysis response into AnalysisResult."""
        try:
            json_match = re.search(r"\{[\s\S]*\}", response)
            if not json_match:
                return AnalysisResult(
                    events_processed=events_count,
                    error="No JSON found in response",
                )

            data = json.loads(json_match.group())
            facts = []
            for f in data.get("facts", [])[:MAX_FACTS_PER_CHUNK]:
                try:
                    facts.append(WeightedFact(
                        content=f.get("content", ""),
                        importance=float(f.get("importance", 0.5)),
                        source_session_id=int(f.get("source_session_id", 0)),
                        source_event_id=f.get("source_event_id", ""),
                        event_type=f.get("event_type", "unknown"),
                        agent_id=f.get("agent_id"),
                    ))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse fact: {e}")
                    continue

            return AnalysisResult(
                facts=facts,
                patterns=data.get("patterns", []),
                suggested_refinements=data.get("suggested_refinements", []),
                events_processed=events_count,
            )
        except json.JSONDecodeError as e:
            return AnalysisResult(
                events_processed=events_count,
                error=f"JSON parse error: {str(e)}",
            )

    def merge_facts(
        self,
        all_facts: list[WeightedFact],
        max_facts: int = 100,
    ) -> list[WeightedFact]:
        """
        Merge and deduplicate facts, keeping top by importance.

        Uses simple content similarity to detect duplicates.
        """
        if not all_facts:
            return []

        # Sort by importance descending
        sorted_facts = sorted(all_facts, key=lambda f: f.importance, reverse=True)

        # Deduplicate by content similarity
        unique_facts: list[WeightedFact] = []
        seen_content: set[str] = set()

        for fact in sorted_facts:
            # Simple dedup: normalize content and check
            normalized = fact.content.lower().strip()[:100]
            if normalized not in seen_content:
                seen_content.add(normalized)
                unique_facts.append(fact)
                if len(unique_facts) >= max_facts:
                    break

        return unique_facts

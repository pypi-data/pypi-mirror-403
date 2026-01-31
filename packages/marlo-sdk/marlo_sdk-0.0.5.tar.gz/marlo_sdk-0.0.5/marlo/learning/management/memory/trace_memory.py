"""Tracer-based context provider implementing Memory-Augmented Architecture."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

from marlo.learning.management.memory.base import ContextProvider, ContextRequest
from marlo.learning.management.memory.schema import StructuredPlan, WeightedFact
from marlo.learning.management.learning_history import aggregate_learning_history
from marlo.runtime.llm_client import LLMClient
from marlo.trajectories.capture.context import ExecutionContext

logger = logging.getLogger(__name__)

CHUNK_SIZE_TOKENS = 100000
CHARS_PER_TOKEN = 4
DEFAULT_PLAN = "Identify all entities and state changes related to the core task."
DEFAULT_MODEL = "gemini-3-flash-preview"


@dataclass
class MemoryState:
    facts: List[WeightedFact] = field(default_factory=list)
    plan: StructuredPlan = field(default_factory=lambda: StructuredPlan(objective=DEFAULT_PLAN))
    summary: str = ""
    processed_index: int = 0
    last_updated: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any] | None) -> "MemoryState":
        if not data:
            return cls()

        facts_data = data.get("facts", [])
        facts = [WeightedFact(**f) for f in facts_data if isinstance(f, dict)]

        plan_data = data.get("plan")
        if isinstance(plan_data, dict):
            plan = StructuredPlan(**plan_data)
        elif isinstance(plan_data, str):
            plan = StructuredPlan(objective=plan_data)
        else:
            plan = StructuredPlan(objective=DEFAULT_PLAN)

        summary = data.get("summary", "")
        if summary and not facts:
            facts = [WeightedFact(content=summary, importance=1.0, source_event_id="legacy")]

        return cls(
            facts=facts,
            plan=plan,
            summary=summary,
            processed_index=int(data.get("processed_index", 0)),
            last_updated=float(data.get("last_updated", 0.0)),
        )


class TraceMemoryProvider(ContextProvider):
    """Builds compact context from recent trace events."""

    def __init__(self, *, model: str = DEFAULT_MODEL, max_history: int = 100) -> None:
        self.max_history = max_history
        try:
            self.client = LLMClient(model=model)
        except RuntimeError:
            self.client = None

    async def provide(self, request: ContextRequest) -> Dict[str, Any]:
        task_meta = request.metadata.get("task_metadata")
        if task_meta is None:
            try:
                task_meta = ExecutionContext.get().metadata.get("task_metadata", {})
            except Exception:
                task_meta = {}
        if task_meta is None:
            task_meta = {}

        memory_data = task_meta.get("context_memory_state")
        state = MemoryState.from_dict(memory_data if isinstance(memory_data, dict) else None)

        learning_summary_str = ""
        history = task_meta.get("learning_history")
        if isinstance(history, dict):
            entries = history.get("entries")
            if isinstance(entries, list) and entries:
                agg = aggregate_learning_history(entries, limit=5)
                learning_summary_str = self._format_learning_summary(agg)

        full_history = request.trace_history or []
        start_index = state.processed_index
        new_events = full_history[start_index:]
        if not new_events:
            task_meta["context_memory_state"] = state.to_dict()
            return self._build_context_payload(state)

        current_chunk_events: List[Any] = []
        current_chunk_tokens = 0

        for event in new_events:
            event_tokens = len(str(event)) // CHARS_PER_TOKEN
            if current_chunk_tokens + event_tokens > CHUNK_SIZE_TOKENS:
                state = await self._process_chunk(state, current_chunk_events, learning_summary_str)
                current_chunk_events = []
                current_chunk_tokens = 0
            current_chunk_events.append(event)
            current_chunk_tokens += event_tokens
            state.processed_index += 1

        if current_chunk_events:
            state = await self._process_chunk(state, current_chunk_events, learning_summary_str)

        task_meta["context_memory_state"] = state.to_dict()
        return self._build_context_payload(state)

    async def _process_chunk(
        self,
        state: MemoryState,
        events: List[Any],
        learning_context: str = "",
    ) -> MemoryState:
        if not self.client:
            self._record_memory_error(
                stage="missing_llm_client",
                message="Context memory requires an LLM client; no fallback is available.",
            )
            return state

        chunk_text = self._format_events(events)
        current_facts = "\n".join([f"- [Imp={f.importance}] {f.content}" for f in state.facts])
        current_plan_str = (
            f"Objective: {state.plan.objective}\n"
            f"Targets: {state.plan.search_targets}\n"
            f"Ignore: {state.plan.ignore_patterns}"
        )

        learning_section = ""
        if learning_context:
            learning_section = f"\n- Recent Reward History:\n{learning_context}"

        prompt_content = f"""
You are a Context Manager Agent. Maintain a "Weighted Fact Memory" and a "Structured Plan".

Current State:
- Task: (User Objective)
- Previous Facts:
{current_facts}
- Previous Plan:
{current_plan_str}{learning_section}

New Execution Chunk (32k token window):
{chunk_text}

Instructions:
1. Update Facts: Extract new facts. Assign importance (0.0-1.0). Merge with old facts. Keep high-importance items.
2. Update Plan: Refine objective, add specific search targets, list patterns to ignore.
3. Adaptive Planning: If 'Recent Reward History' shows repeated failures (low scores), change the plan.

Output Format (JSON):
{{
  "updated_facts": [
    {{ "content": "...", "importance": 0.9, "source_event_id": "..." }}
  ],
  "updated_plan": {{
    "objective": "...",
    "search_targets": ["..."],
    "ignore_patterns": ["..."]
  }}
}}
"""
        try:
            response = await self.client.acomplete(
                messages=[{"role": "user", "content": prompt_content}],
                response_format={"type": "json_object"},
            )
            content = response.content
            data = json.loads(content)

            fact_list = data.get("updated_facts", [])
            new_facts = [WeightedFact(**f) for f in fact_list if isinstance(f, dict)]

            plan_data = data.get("updated_plan", {})
            if isinstance(plan_data, dict):
                new_plan = StructuredPlan(**plan_data)
            elif isinstance(plan_data, str):
                new_plan = StructuredPlan(objective=plan_data)
            else:
                new_plan = state.plan

            state.facts = new_facts or state.facts
            state.plan = new_plan or state.plan
        except Exception as exc:
            self._record_memory_error(stage="processing_error", message=str(exc)[:500])

        return state

    def _build_context_payload(self, state: MemoryState) -> Dict[str, Any]:
        return {
            "summary": state.summary,
            "plan": state.plan.__dict__,
            "facts": [asdict(fact) for fact in state.facts],
        }

    def _format_events(self, events: List[Any]) -> str:
        return "\n".join([json.dumps(event, default=str) for event in events])

    def _format_learning_summary(self, agg: Dict[str, Any]) -> str:
        entries = agg.get("entries", [])
        if not isinstance(entries, list):
            return ""
        lines = []
        for entry in entries:
            reward = entry.get("reward") if isinstance(entry, dict) else None
            score = reward.get("score") if isinstance(reward, dict) else None
            learning = entry.get("learning") if isinstance(entry, dict) else None
            if learning:
                lines.append(f"- score={score}: {learning}")
        return "\n".join(lines)

    def _record_memory_error(self, *, stage: str, message: str) -> None:
        try:
            task_meta = ExecutionContext.get().metadata.setdefault("task_metadata", {})
        except Exception:
            return
        task_meta["context_memory_error"] = {"stage": stage, "message": message}


__all__ = ["TraceMemoryProvider", "MemoryState"]

"""LangGraph-based copilot pipeline with checkpointing."""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncIterator, Literal, TypedDict

try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    _LANGGRAPH_ERROR = None
except ModuleNotFoundError as exc:
    StateGraph = None  # type: ignore[assignment, misc]
    END = None  # type: ignore[assignment]
    AsyncPostgresSaver = None  # type: ignore[assignment, misc]
    _LANGGRAPH_ERROR = exc

from marlo.search.agents.orchestrator import OrchestratorAgent
from marlo.search.agents.sql_query import SQLQueryAgent
from marlo.search.agents.analyst import AnalystAgent
from marlo.search.agents.synthesizer import SynthesizerAgent
from marlo.search.schema.findings import WeightedFact
from marlo.search.storage.hot_storage import HotStorageManager, get_hot_storage_manager
from marlo.billing import BillingLLMClient, USAGE_TYPE_COPILOT

try:
    import tiktoken
    _TIKTOKEN_AVAILABLE = True
except ImportError:
    tiktoken = None  # type: ignore[assignment]
    _TIKTOKEN_AVAILABLE = False

logger = logging.getLogger(__name__)

MAX_CONVERSATION_CONTEXT_TOKENS = 15000
MAX_FACTS_TOKENS = 50000
MAX_DEEP_ITERATIONS = 5
CHARS_PER_TOKEN_ESTIMATE = 4


def _make_json_serializable(obj: Any) -> Any:
    """Convert an object to be JSON serializable.

    Handles datetime objects, bytes, and nested structures.
    """
    if obj is None:
        return None
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    if isinstance(obj, dict):
        return {k: _make_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_make_json_serializable(item) for item in obj]
    if hasattr(obj, "__dict__"):
        return _make_json_serializable(obj.__dict__)
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


def estimate_tokens(text: str) -> int:
    """Estimate token count for text.

    Uses tiktoken if available, otherwise falls back to character-based estimation.
    """
    if not text:
        return 0

    if _TIKTOKEN_AVAILABLE:
        try:
            encoding = tiktoken.encoding_for_model("gpt-4")
            return len(encoding.encode(text))
        except Exception:
            pass

    return len(text) // CHARS_PER_TOKEN_ESTIMATE


@dataclass
class StreamEvent:
    """Event emitted during copilot pipeline execution."""

    type: Literal[
        "status",
        "progress",
        "finding",
        "answer",
        "done",
        "error",
        "planning_detail",
        "query_executing",
        "query_result",
        "analyzing_progress",
        "thinking",
        "writing_sql",
        "sql_generated",
        "reading_results",
        "analyzing_chunk",
        "synthesizing",
    ]
    stage: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "stage": self.stage,
            **self.data,
        }


@dataclass
class QueryExecutionDetail:
    """Details about a single query execution for streaming."""

    index: int
    total: int
    description: str
    sql_hint: str
    sql_query: str
    params: list[Any]
    result_count: int
    execution_time_ms: float
    sample_results: list[dict[str, Any]]
    is_safe: bool
    errors: list[str]


class CopilotState(TypedDict, total=False):
    """State for copilot pipeline."""

    thread_id: str
    project_id: str
    user_id: str
    query: str
    conversation_history: list[dict[str, str]]
    facts: list[dict[str, Any]]
    patterns: list[str]
    search_id: str
    iteration_count: int
    previous_facts_count: int
    status: str
    answer: str
    error: str | None
    sql_query: str
    sql_results: list[dict[str, Any]]
    findings: list[str]
    total_events_searched: int
    total_sessions_searched: int
    plan_intent: str
    plan_strategy: str
    plan_sub_query_count: int
    plan_sub_queries: list[dict[str, str]]
    query_index: int
    total_queries: int
    current_query_results: int
    analysis_chunk_index: int
    analysis_total_chunks: int
    query_execution_details: list[dict[str, Any]]


class CopilotPipeline:
    """LangGraph-based copilot pipeline with checkpointing support."""

    def __init__(
        self,
        llm_client: Any,
        pool: Any,
        checkpointer: AsyncPostgresSaver | None = None,
        hot_storage: HotStorageManager | None = None,
    ):
        if StateGraph is None:
            raise RuntimeError("langgraph is required for CopilotPipeline") from _LANGGRAPH_ERROR

        self.llm_client = llm_client
        self.pool = pool
        self.checkpointer = checkpointer
        self.hot_storage = hot_storage or get_hot_storage_manager()

        self.orchestrator = OrchestratorAgent(llm_client, pool)
        self.sql_agent = SQLQueryAgent(llm_client, pool)
        self.analyst = AnalystAgent(llm_client, self.hot_storage)
        self.synthesizer = SynthesizerAgent(llm_client)

        self._graph = self._build_graph()

    def _create_billing_agents(self, user_id: str, project_id: str) -> None:
        """Create agents with billing-aware LLM client."""
        billing_client = BillingLLMClient(
            self.llm_client,
            user_id=user_id,
            project_id=project_id,
            usage_type=USAGE_TYPE_COPILOT,
        )
        self.orchestrator = OrchestratorAgent(billing_client, self.pool)
        self.sql_agent = SQLQueryAgent(billing_client, self.pool)
        self.analyst = AnalystAgent(billing_client, self.hot_storage)
        self.synthesizer = SynthesizerAgent(billing_client)

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine."""
        graph = StateGraph(CopilotState)

        graph.add_node("init", self._init)
        graph.add_node("plan", self._plan)
        graph.add_node("query", self._query)
        graph.add_node("analyze", self._analyze)
        graph.add_node("evaluate", self._evaluate)
        graph.add_node("synthesize", self._synthesize)

        graph.set_entry_point("init")

        graph.add_edge("init", "plan")
        graph.add_edge("plan", "query")
        graph.add_edge("query", "analyze")
        graph.add_edge("analyze", "evaluate")

        graph.add_conditional_edges(
            "evaluate",
            self._should_continue,
            {
                "continue": "query",
                "synthesize": "synthesize",
            },
        )

        graph.add_edge("synthesize", END)

        return graph.compile(checkpointer=self.checkpointer)

    def _should_continue(self, state: CopilotState) -> str:
        """Decide whether to continue iterating or synthesize.

        Termination conditions (in order):
        1. Max iterations reached (safety limit)
        2. No new facts found in this iteration
        3. No facts at all after first iteration
        """
        iteration_count = state.get("iteration_count", 0)
        current_facts_count = len(state.get("facts", []))
        previous_facts_count = state.get("previous_facts_count", 0)

        if iteration_count >= MAX_DEEP_ITERATIONS:
            logger.info("Stopping: max iterations (%d) reached", MAX_DEEP_ITERATIONS)
            return "synthesize"

        if iteration_count > 0 and current_facts_count == previous_facts_count:
            logger.info("Stopping: no new facts found (count=%d)", current_facts_count)
            return "synthesize"

        if iteration_count > 0 and current_facts_count == 0:
            logger.info("Stopping: no facts found after %d iterations", iteration_count)
            return "synthesize"

        return "continue"

    async def _init(self, state: CopilotState) -> CopilotState:
        """Initialize state for the search pipeline."""
        search_id = state.get("search_id") or str(uuid.uuid4())[:8]
        return {
            **state,
            "search_id": search_id,
            "status": "initializing",
            "iteration_count": 0,
            "previous_facts_count": 0,
            "facts": [],
            "patterns": [],
            "findings": [],
            "total_events_searched": 0,
            "total_sessions_searched": 0,
        }

    async def _plan(self, state: CopilotState) -> CopilotState:
        """Create search plan."""
        query = state.get("query", "")
        project_id = state.get("project_id", "")
        conversation_history = state.get("conversation_history", [])

        context_query = self._build_context_query(query, conversation_history)

        search_state = await self.orchestrator.create_search_state(context_query, project_id)

        plan_intent = ""
        plan_strategy = ""
        plan_sub_query_count = 0
        plan_sub_queries: list[dict[str, str]] = []

        if search_state.search_plan:
            plan_intent = getattr(search_state.search_plan, "intent", "") or query[:100]
            plan_strategy = getattr(search_state.search_plan, "search_strategy", "focused")
            if search_state.search_plan.sub_queries:
                plan_sub_query_count = len(search_state.search_plan.sub_queries)
                for sq in search_state.search_plan.sub_queries:
                    plan_sub_queries.append({
                        "description": sq.description,
                        "sql_hint": sq.sql_hint,
                    })

        return {
            **state,
            "status": "planned",
            "search_id": search_state.search_id,
            "plan_intent": plan_intent,
            "plan_strategy": plan_strategy,
            "plan_sub_query_count": plan_sub_query_count,
            "plan_sub_queries": plan_sub_queries,
            "total_queries": plan_sub_query_count,
        }

    async def _query(self, state: CopilotState) -> CopilotState:
        """Execute queries for search."""
        query = state.get("query", "")
        project_id = state.get("project_id", "")
        search_id = state.get("search_id", "")
        conversation_history = state.get("conversation_history", [])

        context_query = self._build_context_query(query, conversation_history)
        search_state = await self.orchestrator.create_search_state(context_query, project_id)

        all_results: list[dict[str, Any]] = []
        query_execution_details: list[dict[str, Any]] = []
        total_queries = 0
        executed_queries = 0

        if search_state.search_plan and search_state.search_plan.sub_queries:
            total_queries = len(search_state.search_plan.sub_queries)
            for idx, sub_query in enumerate(search_state.search_plan.sub_queries):
                executed_queries = idx + 1
                results, query_result, exec_time = await self.sql_agent.generate_and_execute(
                    search_state.search_plan,
                    sub_query,
                    project_id,
                )
                all_results.extend(results)

                sample_results = _make_json_serializable(results[:3]) if results else []
                query_execution_details.append({
                    "index": idx + 1,
                    "total": total_queries,
                    "description": sub_query.description,
                    "sql_hint": sub_query.sql_hint,
                    "sql_query": query_result.query,
                    "params": [str(p) for p in query_result.params],
                    "result_count": len(results),
                    "execution_time_ms": round(exec_time, 2),
                    "sample_results": sample_results,
                    "is_safe": query_result.is_safe,
                    "errors": query_result.validation_errors,
                })

        if all_results:
            await self.hot_storage.store(
                search_id=search_id,
                results=all_results,
                metadata={"query": context_query, "iteration": state.get("iteration_count", 0)},
            )

        total_sessions = len({r.get("session_id") for r in all_results if r.get("session_id")})

        return {
            **state,
            "status": "queried",
            "sql_results": all_results,
            "total_events_searched": state.get("total_events_searched", 0) + len(all_results),
            "total_sessions_searched": state.get("total_sessions_searched", 0) + total_sessions,
            "query_index": executed_queries,
            "total_queries": total_queries,
            "current_query_results": len(all_results),
            "query_execution_details": query_execution_details,
        }

    async def _analyze(self, state: CopilotState) -> CopilotState:
        """Analyze query results."""
        search_id = state.get("search_id", "")
        query = state.get("query", "")
        existing_facts = state.get("facts", [])
        existing_patterns = state.get("patterns", [])

        all_facts: list[dict[str, Any]] = list(existing_facts)
        all_patterns: list[str] = list(existing_patterns)
        findings: list[str] = list(state.get("findings", []))
        chunk_index = 0

        try:
            async for result in self.analyst.analyze_search_results(
                search_id=search_id,
                search_context=query,
            ):
                chunk_index += 1
                for fact in result.facts:
                    all_facts.append(fact.to_dict())
                    if fact.importance >= 0.7 and len(findings) < 10:
                        findings.append(fact.content[:200])
                all_patterns.extend(result.patterns)
        except Exception as e:
            logger.warning("Analysis failed: %s", e)

        return {
            **state,
            "status": "analyzed",
            "facts": all_facts,
            "patterns": list(set(all_patterns)),
            "findings": findings,
            "analysis_chunk_index": chunk_index,
            "analysis_total_chunks": chunk_index,
        }

    async def _evaluate(self, state: CopilotState) -> CopilotState:
        """Evaluate progress and prepare for next iteration or synthesis.

        Tracks previous_facts_count to enable "no new facts" termination.
        """
        current_facts_count = len(state.get("facts", []))
        previous_facts_count = state.get("previous_facts_count", 0)
        iteration_count = state.get("iteration_count", 0) + 1

        new_facts_found = current_facts_count - previous_facts_count
        logger.info(
            "Evaluation: iteration=%d, total_facts=%d, new_facts=%d",
            iteration_count,
            current_facts_count,
            new_facts_found,
        )

        return {
            **state,
            "status": "evaluated",
            "iteration_count": iteration_count,
            "previous_facts_count": current_facts_count,
        }

    async def _synthesize(self, state: CopilotState) -> CopilotState:
        """Synthesize final answer."""
        facts_data = state.get("facts", [])
        patterns = state.get("patterns", [])
        query = state.get("query", "")
        project_id = state.get("project_id", "")

        facts = [WeightedFact.from_dict(f) for f in facts_data]

        search_state = await self.orchestrator.create_search_state(query, project_id)
        search_state.total_events_searched = state.get("total_events_searched", 0)
        search_state.total_sessions_searched = state.get("total_sessions_searched", 0)
        search_state.total_facts_extracted = len(facts)

        synthesis = await self.synthesizer.synthesize(search_state, facts, patterns)

        search_id = state.get("search_id", "")
        if search_id:
            try:
                await self.hot_storage.delete(search_id)
            except Exception:
                pass

        return {
            **state,
            "status": "complete",
            "answer": synthesis.answer,
        }

    def _build_context_query(
        self,
        query: str,
        conversation_history: list[dict[str, str]],
    ) -> str:
        """Build query with conversation context.

        Uses token-based truncation to stay within MAX_CONVERSATION_CONTEXT_TOKENS.
        """
        if not conversation_history:
            return query

        context_parts: list[str] = []
        total_tokens = 0

        for msg in reversed(conversation_history[-10:]):
            msg_text = f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            msg_tokens = estimate_tokens(msg_text)
            if total_tokens + msg_tokens > MAX_CONVERSATION_CONTEXT_TOKENS:
                break
            context_parts.insert(0, msg_text)
            total_tokens += msg_tokens

        if context_parts:
            context = "\n".join(context_parts)
            return f"Previous conversation:\n{context}\n\nCurrent question: {query}"

        return query

    async def execute(
        self,
        thread_id: str,
        project_id: str,
        user_id: str,
        query: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> AsyncIterator[StreamEvent]:
        """
        Execute the copilot pipeline with streaming events.

        Args:
            thread_id: UUID of the conversation thread
            project_id: Project scope for the search
            user_id: User identifier
            query: User's natural language query
            conversation_history: Previous messages for context

        Yields:
            StreamEvent objects for real-time updates
        """
        self._create_billing_agents(user_id, project_id)

        initial_state: CopilotState = {
            "thread_id": thread_id,
            "project_id": project_id,
            "user_id": user_id,
            "query": query,
            "conversation_history": conversation_history or [],
            "facts": [],
            "patterns": [],
            "findings": [],
            "status": "starting",
            "answer": "",
            "error": None,
            "search_id": "",
            "iteration_count": 0,
            "previous_facts_count": 0,
            "sql_query": "",
            "sql_results": [],
            "total_events_searched": 0,
            "total_sessions_searched": 0,
        }

        config = {"configurable": {"thread_id": thread_id}}

        yield StreamEvent(
            type="status",
            stage="starting",
            data={"message": "Starting search..."},
        )

        try:
            previous_status = ""
            final_state: CopilotState = initial_state
            emitted_planning_detail = False
            emitted_query_result = False
            emitted_analysis_progress = False

            async for event in self._graph.astream(initial_state, config=config):
                for node_name, state in event.items():
                    final_state = state
                    status = state.get("status", "")

                    if status != previous_status:
                        previous_status = status
                        yield StreamEvent(
                            type="status",
                            stage=status,
                            data={"message": f"Stage: {status}"},
                        )

                        emitted_planning_detail = False
                        emitted_query_result = False
                        emitted_analysis_progress = False

                    if status == "planned" and not emitted_planning_detail:
                        emitted_planning_detail = True
                        plan_intent = state.get("plan_intent", "")
                        plan_strategy = state.get("plan_strategy", "")
                        sub_query_count = state.get("plan_sub_query_count", 0)
                        plan_sub_queries = state.get("plan_sub_queries", [])

                        yield StreamEvent(
                            type="thinking",
                            stage="planning",
                            data={
                                "content": f"Understanding query and creating search plan...",
                                "action": "planning",
                            },
                        )

                        if plan_intent or sub_query_count:
                            yield StreamEvent(
                                type="planning_detail",
                                stage="planning",
                                data={
                                    "intent": plan_intent,
                                    "strategy": plan_strategy,
                                    "sub_query_count": sub_query_count,
                                    "sub_queries": plan_sub_queries,
                                },
                            )

                    if status == "queried" and not emitted_query_result:
                        emitted_query_result = True
                        query_index = state.get("query_index", 0)
                        total_queries = state.get("total_queries", 0)
                        result_count = state.get("current_query_results", 0)
                        query_execution_details = state.get("query_execution_details", [])

                        for detail in query_execution_details:
                            yield StreamEvent(
                                type="writing_sql",
                                stage="querying",
                                data={
                                    "query_index": detail.get("index", 0),
                                    "total_queries": detail.get("total", 0),
                                    "description": detail.get("description", ""),
                                    "sql_hint": detail.get("sql_hint", ""),
                                },
                            )

                            yield StreamEvent(
                                type="sql_generated",
                                stage="querying",
                                data={
                                    "query_index": detail.get("index", 0),
                                    "sql_query": detail.get("sql_query", ""),
                                    "params": detail.get("params", []),
                                    "is_safe": detail.get("is_safe", False),
                                    "errors": detail.get("errors", []),
                                },
                            )

                            yield StreamEvent(
                                type="reading_results",
                                stage="querying",
                                data={
                                    "query_index": detail.get("index", 0),
                                    "result_count": detail.get("result_count", 0),
                                    "execution_time_ms": detail.get("execution_time_ms", 0),
                                    "sample_results": detail.get("sample_results", []),
                                },
                            )

                        if total_queries > 0:
                            yield StreamEvent(
                                type="query_executing",
                                stage="querying",
                                data={
                                    "query_index": query_index,
                                    "total_queries": total_queries,
                                },
                            )
                        yield StreamEvent(
                            type="query_result",
                            stage="querying",
                            data={
                                "result_count": result_count,
                                "total_events": state.get("total_events_searched", 0),
                            },
                        )

                    if status == "analyzed":
                        if not emitted_analysis_progress:
                            emitted_analysis_progress = True
                            chunk_index = state.get("analysis_chunk_index", 0)
                            facts_count = len(state.get("facts", []))

                            yield StreamEvent(
                                type="thinking",
                                stage="analyzing",
                                data={
                                    "content": f"Analyzing {state.get('current_query_results', 0)} results to extract insights...",
                                    "action": "analyzing",
                                },
                            )

                            yield StreamEvent(
                                type="analyzing_progress",
                                stage="analyzing",
                                data={
                                    "chunk_progress": f"{chunk_index} chunks processed",
                                    "facts_extracted": facts_count,
                                },
                            )

                        findings = state.get("findings", [])
                        for finding in findings[-3:]:
                            yield StreamEvent(
                                type="finding",
                                stage="analyzing",
                                data={"content": finding},
                            )

                    if status == "evaluated":
                        current_facts = len(state.get("facts", []))
                        previous_facts = state.get("previous_facts_count", 0)
                        yield StreamEvent(
                            type="progress",
                            stage="evaluating",
                            data={
                                "iteration": state.get("iteration_count", 0),
                                "facts_count": current_facts,
                                "new_facts": current_facts - previous_facts,
                            },
                        )

                    if status == "complete":
                        yield StreamEvent(
                            type="synthesizing",
                            stage="synthesizing",
                            data={
                                "content": f"Synthesizing {len(state.get('facts', []))} facts into a comprehensive answer...",
                                "facts_count": len(state.get("facts", [])),
                                "events_searched": state.get("total_events_searched", 0),
                            },
                        )

                        answer = state.get("answer", "")
                        if answer:
                            yield StreamEvent(
                                type="answer",
                                stage="complete",
                                data={
                                    "answer": answer,
                                    "key_findings": state.get("findings", []),
                                },
                            )

            yield StreamEvent(
                type="done",
                stage="complete",
                data={
                    "thread_id": thread_id,
                    "events_searched": final_state.get("total_events_searched", 0),
                    "facts_extracted": len(final_state.get("facts", [])),
                },
            )

        except Exception as e:
            logger.exception("Copilot pipeline failed")
            yield StreamEvent(
                type="error",
                stage="pipeline",
                data={"message": str(e)},
            )

    async def resume(
        self,
        thread_id: str,
        query: str,
    ) -> AsyncIterator[StreamEvent]:
        """
        Resume a previous conversation with a new query.

        Args:
            thread_id: UUID of the existing conversation thread
            query: New user query

        Yields:
            StreamEvent objects for real-time updates
        """
        if self.checkpointer is None:
            yield StreamEvent(
                type="error",
                stage="resume",
                data={"message": "Checkpointing not available"},
            )
            return

        config = {"configurable": {"thread_id": thread_id}}

        try:
            checkpoint = await self.checkpointer.aget(config)
            if checkpoint is None:
                yield StreamEvent(
                    type="error",
                    stage="resume",
                    data={"message": f"No checkpoint found for thread {thread_id}"},
                )
                return

            state = checkpoint.get("channel_values", {})

            history = state.get("conversation_history", [])
            if state.get("query"):
                history.append({"role": "user", "content": state["query"]})
            if state.get("answer"):
                history.append({"role": "assistant", "content": state["answer"]})

            async for event in self.execute(
                thread_id=thread_id,
                project_id=state.get("project_id", ""),
                user_id=state.get("user_id", ""),
                query=query,
                conversation_history=history,
            ):
                yield event

        except Exception as e:
            logger.exception("Failed to resume conversation")
            yield StreamEvent(
                type="error",
                stage="resume",
                data={"message": str(e)},
            )

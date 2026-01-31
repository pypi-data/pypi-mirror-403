
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Sequence


@dataclass
class DecisionPoint:
    """Represents a single turn where the model acts, followed by a tool result."""
    input_messages: List[Dict[str, Any]]
    production_thinking: Dict[str, Any]
    production_response: str
    production_tool_call: Optional[Dict[str, Any]]
    static_tool_result: Optional[Dict[str, Any]]


@dataclass
class Scenario:
    """A reconstructed episode from production data."""
    id: str
    task: str
    agent_config: Dict[str, Any]
    decision_points: List[DecisionPoint]
    production_final_answer: str
    production_reward: Dict[str, Any]


@dataclass
class TestRun:
    """Result of running a test model through a scenario."""
    model_name: str
    scenario_id: str
    test_final_answer: str
    tool_calls_made: List[Dict[str, Any]]
    total_tokens: int
    runtime_ms: float
    error: Optional[str] = None


class SimulationMode(str, Enum):
    PRODUCTION_PARITY = "Production Parity"
    ACCURACY = "Accuracy"
    EFFICIENCY = "Efficiency"
    TOOL_ACCESS = "Tool Access"
    CONSISTENCY = "Consistency"


@dataclass
class ComparisonResult:
    """Score and details comparing test run vs production."""
    scenario_id: str
    model_name: str
    simulation_mode: SimulationMode
    score: float
    details: Dict[str, Any]


@dataclass
class ModelSummary:
    """Aggregated stats for a model across all scenarios."""
    model: str
    projected_success: float
    access_success: float
    avg_runtime_ms: float
    avg_tokens: float
    estimated_cost: float
    note: str = ""


@dataclass
class SimulationConfig:
    """Configuration for a full simulation run."""
    db_url: str
    simulation_mode: SimulationMode
    candidate_models: List[LLMParameters]
    subagent_id: Optional[str] = None
    limit: int = 10


class TelemetryEmitterProtocol(Protocol):
    def emit(self, event_type: str, payload: Dict[str, Any] | None = None) -> None:
        ...


@dataclass(frozen=True, slots=True)
class DiscoveryContext:
    task: str
    step_index: int
    observation: Any | None = None
    reward: float | None = None
    done: bool | None = None
    info: Dict[str, Any] | None = None


class MarloEnvironmentProtocol(Protocol):
    def reset(self, task: str | None = None) -> Any:
        ...

    def step(self, action: Any, submit: bool = False) -> tuple[Any, float, bool, Dict[str, Any]]:
        ...

    def close(self) -> None:
        ...


class MarloAgentProtocol(Protocol):
    def plan(
        self,
        task: str,
        observation: Any,
        *,
        emit_event: TelemetryEmitterProtocol | None = None,
    ) -> Dict[str, Any]:
        ...

    def act(
        self,
        context: DiscoveryContext,
        *,
        emit_event: TelemetryEmitterProtocol | None = None,
    ) -> Any:
        ...

    def summarize(
        self,
        context: DiscoveryContext,
        *,
        history: Sequence[Any] | None = None,
        emit_event: TelemetryEmitterProtocol | None = None,
    ) -> str:
        ...
@dataclass(slots=True)
class LLMParameters:
    model: str
    temperature: float = 0.0
    max_tokens: int | None = None
    provider: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ToolDefinition:
    name: str
    description: str | None = None
    parameters: Dict[str, Any] | None = None

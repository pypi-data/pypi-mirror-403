"""Simulation interfaces used by environment/agent integrations.

These are intentionally lightweight Protocols used in examples, tests, and
adapter glue. They are not tied to any concrete runtime implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Protocol, Sequence

from marlo.simulation.runner.decorators import agent
from marlo.simulation.schemas import (
    Scenario,
    TestRun,
    TelemetryEmitterProtocol,
    DiscoveryContext,
    MarloEnvironmentProtocol,
    MarloAgentProtocol
)
from marlo.runtime.llm_client import LLMClient
from marlo.simulation.schemas import LLMParameters


class ReplayEnvironment(MarloEnvironmentProtocol):
    """
    Simulates an environment by replaying static tool results from a scenario.
    """

    def __init__(self, scenario: Scenario):
        self._scenario = scenario
        self._step_index = 0
        self._max_steps = len(scenario.decision_points)
        self._done = False

    def reset(self, task: str | None = None) -> Any:
        self._step_index = 0
        self._done = False
        
        return {
            "task": self._scenario.task,
            "system_prompt": self._scenario.agent_config.get("system_prompt", ""),
            "tools": self._scenario.agent_config.get("tool_definitions", []),
        }

    def step(self, action: Any, submit: bool = False) -> tuple[Any, float, bool, Dict[str, Any]]:
        """
        Action is typically a tool call request (dict with name/input).
        We compare it (optionally) but primarily just return the STATIC result
        associated with the current decision point.
        """
        if self._done:
            return None, 0.0, True, {"error": "Environment already done"}

        if submit:
            self._done = True
            return "Submitted", 0.0, True, {}

        if self._step_index >= self._max_steps:
            self._done = True
            return None, 0.0, True, {"warning": "Scenario steps exhausted"}
        dp = self._scenario.decision_points[self._step_index]
        self._step_index += 1
        
        static_result = dp.static_tool_result or {"output": "No result recorded"}
        
        return static_result.get("output"), 0.0, False, {}

    def close(self) -> None:
        self._done = True


@agent
class TestModelAgent(MarloAgentProtocol):
    """
    Wraps an LLMClient to act as a test subject in the simulation.
    Captures its own actions for TestRun report.
    """

    def __init__(self, params: LLMParameters, scenario_id: str, system_prompt: str = "", tools: list = None):
        client_params = {
            "temperature": params.temperature,
            "max_tokens": params.max_tokens,
        }
        self.client = LLMClient(model=params.model, params=client_params)
        self.model_name = params.model
        self.scenario_id = scenario_id
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.conversation_history: List[Dict[str, Any]] = []
        
        self.tool_calls_made: List[Dict[str, Any]] = []
        self.total_tokens = 0
        self.final_answer = ""
    
    def plan(
        self,
        task: str,
        observation: Any,
        *,
        emit_event: TelemetryEmitterProtocol | None = None,
    ) -> Dict[str, Any]:
        return {}

    def act(
        self,
        context: DiscoveryContext,
        *,
        emit_event: TelemetryEmitterProtocol | None = None,
    ) -> Any:
        if context.step_index == 0:
            self.conversation_history.append({"role": "user", "content": context.task})
        elif context.observation is not None:
             content = str(context.observation)
             last_msg = self.conversation_history[-1] if self.conversation_history else {}
             
             if last_msg.get("role") == "assistant" and "tool_calls" in last_msg:
                 for tc in last_msg["tool_calls"]:
                     self.conversation_history.append({
                         "role": "tool", 
                         "tool_call_id": tc.get("id", "call_null"),
                         "content": content
                     })
             else:
                 self.conversation_history.append({"role": "user", "content": content})

        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.extend(self.conversation_history)
        
        try:
            response = self.client.complete(
                messages=messages,
                tools=self.tools if self.tools else None
            )
            
            if response.raw and hasattr(response.raw, "usage"):
                u = response.raw.usage
                self.total_tokens += (u.prompt_tokens + u.completion_tokens)
            
            content = response.content or ""
            
            tool_calls = []
            
            if response.raw and hasattr(response.raw, "choices"):
                choice = response.raw.choices[0]
                if hasattr(choice, "message") and hasattr(choice.message, "tool_calls"):
                     if choice.message.tool_calls:
                         for tc in choice.message.tool_calls:
                             tool_calls.append({
                                 "id": tc.id,
                                 "type": tc.type,
                                 "function": {
                                     "name": tc.function.name,
                                     "arguments": tc.function.arguments
                                 }
                             })

            if not tool_calls and content.strip().startswith("[") and "function" in content:
                return "Error: Model returned raw JSON as no proper tool is called"

            assistant_msg = {"role": "assistant", "content": content}
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls
            self.conversation_history.append(assistant_msg)

            if tool_calls:
                self.tool_calls_made.extend(tool_calls)
                return tool_calls[0] 

            self.final_answer = content
            return content

        except Exception as exc:
            return f"Error: {exc}"

    def summarize(
        self,
        context: DiscoveryContext,
        *,
        history: Sequence[Any] | None = None,
        emit_event: TelemetryEmitterProtocol | None = None,
    ) -> str:
        return self.final_answer

    def get_test_run(self) -> TestRun:
        return TestRun(
            model_name=self.model_name,
            scenario_id=self.scenario_id,
            test_final_answer=self.final_answer,
            tool_calls_made=self.tool_calls_made,
            total_tokens=self.total_tokens,
            runtime_ms=0.0
        )

__all__ = [
    "ReplayEnvironment",
    "TestModelAgent",
]

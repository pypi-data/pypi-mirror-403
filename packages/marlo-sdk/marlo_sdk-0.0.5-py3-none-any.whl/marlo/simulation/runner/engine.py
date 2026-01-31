
from __future__ import annotations

import asyncio
from typing import List, Dict, Any, Optional

from marlo.trajectories.schema.traces import MarloSessionTrace
from marlo.learning.rewards.runner import evaluate_session
from marlo.trajectories.capture.context import ExecutionContext
from marlo.core.config.models import StorageConfig
from marlo.storage.postgres.database import Database

from marlo.simulation.schemas import (
    SimulationConfig,
    Scenario,
    TestRun,
    ComparisonResult,
    ModelSummary,
    SimulationMode,
    DiscoveryContext
)
from marlo.simulation.scenarios.extractor import extract_scenario
from marlo.simulation.interfaces import (
    ReplayEnvironment,
    TestModelAgent
)


async def load_trajectories(
    DATABASE_URL: str, subagent_id: Optional[str] = None, limit: int = 10
) -> List[MarloSessionTrace]:
    """Load sessions from DB to be used as scenarios."""
    database = Database(StorageConfig(database_url=DATABASE_URL))
    await database.connect()
    try:
        sessions = await database.fetch_sessions(limit=limit, offset=0)
        traces: List[MarloSessionTrace] = []
        for session in sessions:
            session_id = session.get("id")
            if not isinstance(session_id, int):
                continue
            events = await database.fetch_trajectory_events(session_id, limit=None)
            metadata = database._deserialize_json(session.get("metadata")) or {}
            if not isinstance(metadata, dict):
                metadata = {}
            metadata.setdefault("session_id", session_id)
            reward = database._deserialize_json(session.get("reward"))
            traces.append(
                MarloSessionTrace(
                    task=str(session.get("task") or ""),
                    final_answer=str(session.get("final_answer") or ""),
                    plan=None,
                    steps=[],
                    session_metadata=metadata,
                    session_reward=reward if isinstance(reward, dict) else None,
                    trajectory_events=[dict(row) for row in events],
                    learning=session.get("learning"),
                )
            )
        return traces
    finally:
        await database.disconnect()


async def run_episode(env: ReplayEnvironment, agent: TestModelAgent) -> TestRun:
    """Run a single agent through a single scenario environment."""
    
    initial_obs = env.reset()
    
    context = DiscoveryContext(
        task=initial_obs["task"],
        step_index=0,
        observation=initial_obs,
        done=False
    )
    
    while not context.done:
        action = agent.act(context)
        
        is_tool = isinstance(action, dict) and "function" in action
        submit = not is_tool
        
        obs, reward, done, info = env.step(action, submit=submit)
        
        context = DiscoveryContext(
            task=initial_obs["task"],
            step_index=context.step_index + 1,
            observation=obs,
            reward=reward,
            done=done,
            info=info
        )
        
        if context.step_index > 50:
            break

    test_run = agent.get_test_run()
    
    env.close()
    return test_run


async def compare(
    scenario: Scenario, test_run: TestRun, mode: SimulationMode
) -> ComparisonResult:
    """Score the test run against production data based on simulation mode."""
    
    score = 0.0
    details = {}
    
    if mode == SimulationMode.PRODUCTION_PARITY:
        match = (scenario.production_final_answer.strip() == test_run.test_final_answer.strip())
        score = 1.0 if match else 0.0
        details["match"] = match

    elif mode == SimulationMode.ACCURACY:
        
        ctx = ExecutionContext.get()
        ctx.metadata["session_metadata"] = {"execution_mode": "simulation"}
        
        reward = await evaluate_session(
            task=scenario.task,
            final_answer=test_run.test_final_answer,
            execution_context=ctx
        )
        score = reward.score if reward.score is not None else 0.0
        details["rationale"] = reward.rationale
    
    elif mode == SimulationMode.TOOL_ACCESS:
        prod_tools = {dp.production_tool_call.get("name") for dp in scenario.decision_points if dp.production_tool_call}
        test_tools = {t.get("function", {}).get("name") for t in test_run.tool_calls_made}
        
        overlap = prod_tools.intersection(test_tools)
        if prod_tools:
            score = len(overlap) / len(prod_tools)
        else:
            score = 1.0 if not test_tools else 0.0
            
        details["missing_tools"] = list(prod_tools - test_tools)
        details["extra_tools"] = list(test_tools - prod_tools)

    return ComparisonResult(
        scenario_id=scenario.id,
        model_name=test_run.model_name,
        simulation_mode=mode,
        score=score,
        details=details
    )


def aggregate(results: List[ComparisonResult], model_name: str) -> ModelSummary:
    if not results:
        return ModelSummary(model_name, 0, 0, 0, 0, 0)
        
    scores = [r.score for r in results]
    avg_score = sum(scores) / len(scores)
    
    return ModelSummary(
        model=model_name,
        projected_success=avg_score,
        access_success=0.0,
        avg_runtime_ms=0.0,
        avg_tokens=0.0,
        estimated_cost=0.0
    )


async def run_simulation(config: SimulationConfig) -> List[ModelSummary]:
    """
    Main entry point for running a simulation campaign.
    """
    traces = await load_trajectories(config.db_url, config.subagent_id, config.limit)
    
    scenarios = []
    for trace in traces:
        s = extract_scenario(trace, config.subagent_id)
        if s:
            scenarios.append(s)
            
    if not scenarios:
        return []

    all_summaries = []
    
    for model_params in config.candidate_models:
        model_results = []
        for scenario in scenarios:
            agent = TestModelAgent(
                model_params,
                scenario.id,
                system_prompt=scenario.agent_config.get("system_prompt", ""),
                tools=scenario.agent_config.get("tool_definitions", [])
            )
            env = ReplayEnvironment(scenario)
            
            try:
                test_run = await run_episode(env, agent)
                
                result = await compare(scenario, test_run, config.simulation_mode)
                model_results.append(result)
            except Exception as e:
                print(f"Simulation failed for {model_params.model} on {scenario.id}: {e}")
                
        summary = aggregate(model_results, model_params.model)
        all_summaries.append(summary)

    return all_summaries

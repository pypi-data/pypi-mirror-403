
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from marlo.trajectories.schema.traces import MarloSessionTrace
from marlo.trajectories.schema.events import TrajectoryEventType
from marlo.simulation.schemas import Scenario, DecisionPoint


def _parse_event(raw_data: Any) -> Dict[str, Any]:
    """Helper to robustly extract event dict from DB row or raw data."""
    if isinstance(raw_data, dict):
        if "event" in raw_data:
            candidate = raw_data["event"]
            if isinstance(candidate, str):
                try:
                    return json.loads(candidate)
                except Exception:
                    pass
            elif isinstance(candidate, dict):
                return candidate
    return raw_data if isinstance(raw_data, dict) else {}

def extract_scenario(trace: MarloSessionTrace, subagent_id: Optional[str] = None) -> Optional[Scenario]:
    """
    Reconstructs a Scenario from a production session trace.
    """
    if not trace.trajectory_events:
        return None

    parsed_events = [_parse_event(e) for e in trace.trajectory_events]
    parsed_events.reverse()

    agent_config: Dict[str, Any] = {}
    target_agent_id = subagent_id
    
    if not target_agent_id:
        for event in parsed_events:
            evt_type = event.get("event_type")
            if evt_type == TrajectoryEventType.AGENT_DEFINITION:
                payload = event.get("payload", {})
                target_agent_id = payload.get("agent_id")
                agent_config = payload
                break
    else:
        for event in parsed_events:
            if event.get("event_type") == TrajectoryEventType.AGENT_DEFINITION:
                payload = event.get("payload", {})
                if payload.get("agent_id") == target_agent_id:
                    agent_config = payload
                    break

    if not target_agent_id:
        return None

    decision_points: List[DecisionPoint] = []
    
    events = parsed_events
    i = 0
    while i < len(events):
        event = events[i]
        
        if event.get("agent_id") != target_agent_id and event.get("agent_id") is not None:
             i += 1
             continue

        if event.get("event_type") == TrajectoryEventType.LLM_CALL:
            payload = event.get("payload", {})
            messages = payload.get("messages", [])
            response = str(payload.get("response", ""))
            reasoning = payload.get("reasoning", {})
            
            prod_tool_call: Optional[Dict[str, Any]] = None
            static_result: Optional[Dict[str, Any]] = None
            
            j = i + 1
            while j < len(events):
                next_evt = events[j]
                
                if next_evt.get("event_type") == TrajectoryEventType.LOG:
                    j += 1
                    continue
                if next_evt.get("agent_id") != target_agent_id and next_evt.get("agent_id") is not None:
                    j += 1
                    continue
                
                if next_evt.get("event_type") == TrajectoryEventType.TOOL_CALL:
                    tool_payload = next_evt.get("payload", {})
                    prod_tool_call = {
                        "name": tool_payload.get("tool_name"),
                        "input": tool_payload.get("input")
                    }
                    static_result = {
                        "output": tool_payload.get("output"),
                        "error": tool_payload.get("error")
                    }
                
                break
            
            dp = DecisionPoint(
                input_messages=messages,
                production_thinking=reasoning,
                production_response=response,
                production_tool_call=prod_tool_call,
                static_tool_result=static_result
            )
            decision_points.append(dp)
            
        i += 1

    if not decision_points:
        return None

    return Scenario(
        id=str(trace.session_metadata.get("session_id", "unknown")),
        task=trace.task,
        agent_config=agent_config,
        decision_points=decision_points,
        production_final_answer=trace.final_answer,
        production_reward=trace.session_reward or {}
    )

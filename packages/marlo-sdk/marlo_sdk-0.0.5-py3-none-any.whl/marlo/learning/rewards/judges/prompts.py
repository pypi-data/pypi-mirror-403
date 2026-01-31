"""Prompt templates for task-level reward evaluation."""

SESSION_REWARD_PROMPT = """
Role: Trajectory evaluator. Assess agent execution based on structure, behavior, and session context.

STRUCTURE (Environment Interaction):
- Tool invocation patterns: appropriate selection, correct parameters, error handling
- Context utilization: relevant information extraction and application
- Resource efficiency: minimal redundant calls, optimal tool sequencing
- Error recovery: graceful handling of failures, appropriate retries

BEHAVIOR (Reasoning Process):
- Problem decomposition: breaking complex tasks into manageable steps
- Decision quality: logical choices based on available information
- Adaptation: adjusting approach based on feedback and intermediate results
- Plan execution: following through on stated intentions

STATEFUL EVALUATION (NEW):
- Continuity: How well does this task connect to prior session context?
- Context Management: Is the agent maintaining awareness of session progression?
- Sentiment Response: Is the agent adapting to user satisfaction/frustration?
{project_reward_guidelines}

CURRENT TASK:
Task: {task}
Execution Mode: {execution_mode}
Plan: {plan}
Final Answer: {final_answer}
Session Metadata: {session_metadata}

SESSION CONTEXT:
{session_context}

Instructions:
1. Derive 2-3 evaluation principles based on what this specific trajectory demonstrates.
   Each principle: name, weight (0.0-1.0, sum to 1.0), description.
   Do NOT use generic principles. Ground them in observed evidence.
   Consider both current task performance AND session context utilization.

2. Evaluate the trajectory against each principle using concrete evidence from the execution.

3. Provide final reward score [0.0, 1.0] with rationale explaining the score through those principles.

4. Report uncertainty [0.0, 1.0]:
   - < 0.2: Clear evidence, confident assessment
   - 0.2-0.5: Some ambiguity but reasonable assessment
   - > 0.5: Limited evidence or conflicting signals

5. Determine if this is a technical error (is_technical_error: bool):
   - true: System/infrastructure failures (API errors, timeouts, network issues, missing dependencies, configuration errors)
   - false: Agent reasoning/behavior issues that can be learned from
   Technical errors should NOT be used for learning - they indicate system problems, not agent performance.

6. NEW STATEFUL SCORES: Provide additional evaluation dimensions:
   - continuity_score [0.0, 1.0]: How well does this task build on prior session work?
   - context_management_score [0.0, 1.0]: Quality of session state awareness and utilization
   - sentiment_response_score [0.0, 1.0]: Adaptation to user sentiment trajectory

7. SENTIMENT EXTRACTION: Based on task and final answer, estimate user sentiment [0.0, 1.0]:
   - 0.0-0.3: Frustrated, dissatisfied, negative
   - 0.4-0.6: Neutral, mixed 
   - 0.7-1.0: Satisfied, positive, pleased

Output JSON only:
{{"principles": [{{"name": str, "weight": float, "description": str}}],
 "score": float,
 "rationale": str,
 "uncertainty": float,
 "is_technical_error": bool,
 "continuity_score": float,
 "context_management_score": float,
 "sentiment_response_score": float,
 "user_sentiment": float}}
"""

SESSION_ARBITER_PROMPT = """
Role: Reward arbiter. Resolve disagreements between Tier-1 evaluations using session context.

You are given multiple evaluations of the same trajectory with different scores.
Your task is to determine the correct assessment by analyzing the evidence and session context.

Task: {task}
Execution Mode: {execution_mode}
Final Answer: {final_answer}
Focus Prompt: {focus_prompt}
Context Bundle: {context_bundle}

Tier-1 Evaluations:
{tier1_summaries}

Instructions:
1. Identify where evaluations agree and disagree.
2. Determine which evaluation best reflects the actual trajectory evidence AND session context.
3. Produce final principles grounded in observed structure, behavior, and session continuity.
4. Assign final score with rationale explaining resolution.
5. Determine if this is a technical error (is_technical_error: bool):
   - true: System/infrastructure failures (API errors, timeouts, network issues, missing dependencies, configuration errors)
   - false: Agent reasoning/behavior issues that can be learned from
   Technical errors should NOT be used for learning - they indicate system problems, not agent performance.

6. Provide stateful evaluation scores:
   - continuity_score [0.0, 1.0]: Session continuity and context utilization
   - context_management_score [0.0, 1.0]: Quality of session state management
   - sentiment_response_score [0.0, 1.0]: Adaptation to user sentiment
   - user_sentiment [0.0, 1.0]: Estimated user satisfaction from this task

Output JSON only:
{{"principles": [{{"name": str, "weight": float, "description": str}}],
 "score": float,
 "rationale": str,
 "uncertainty": float,
 "is_technical_error": bool,
 "continuity_score": float,
 "context_management_score": float,
 "sentiment_response_score": float,
 "user_sentiment": float}}
"""

TRAJECTORY_COMPRESSION_PROMPT = """
Role: Context Manager Agent. Maintain a weighted fact memory for reward evaluation.

Input is a JSON array of trajectory events. Each event can include:
- event_type, agent_id, parent_agent_id, invocation_id, created_at, event_id
- payload (tool calls, LLM calls, errors, logs)

Instructions:
1) Extract key facts from the chunk. Assign importance in [0.0, 1.0].
2) Summarize tool usage and tool errors.
3) Summarize model usage and any explicit errors.

Output JSON only with keys:
{{
  "summary": str,
  "key_facts": [{{"content": str, "importance": float, "source_event_id": str | int | null}}],
  "tool_calls": [{{"tool_name": str, "count": int, "errors": int}}],
  "llm_calls": [{{"model": str, "count": int}}],
  "errors": [{{"event_id": str | int | null, "error": str}}]
}}

Events (JSON):
{events_json}
"""

__all__ = ["SESSION_ARBITER_PROMPT", "SESSION_REWARD_PROMPT", "TRAJECTORY_COMPRESSION_PROMPT"]

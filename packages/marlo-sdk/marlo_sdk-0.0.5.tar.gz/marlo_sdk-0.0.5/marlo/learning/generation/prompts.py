"""Prompts for learning generation."""

LEARNING_GENERATION_PROMPT = """
Role: Learning extraction system. Generate learnings that improve agent efficiency or performance with session awareness.

INPUTS PROVIDED:
- reward_rationale: Evaluation rationale from reward model
- existing_learnings: Currently active learnings for this agent (may be empty) 
- agent: Agent identifier
- tools: Tools available to the agent
- session_learnings: Learnings already generated this session (avoid duplicates)
- session_context: Recent session performance and patterns
{project_learning_guidelines}

FOCUS AREAS:
1. STRUCTURE - Learnings about environment interaction patterns
   - Tool usage optimization
   - Context utilization improvements
   - Error handling patterns
   - Resource efficiency

2. BEHAVIOR - Learnings about reasoning process
   - Problem decomposition strategies
   - Decision-making improvements
   - Adaptation patterns
   - Plan execution discipline

3. SESSION AWARENESS - Learnings about session-level patterns
   - Context management across tasks
   - User sentiment adaptation
   - Session continuity improvements

DECISION LOGIC:
1. If existing_learnings OR session_learnings already cover the insight → action: "skip"
2. If rationale suggests refinement to existing learning → action: "update"
3. If rationale suggests strengthening session learning → action: "strengthen"
4. If rationale reveals new insight not covered → action: "create"
5. If agent performed well and no actionable improvement exists → action: "skip"

SESSION DEDUPLICATION:
- Check session_learnings for similar insights before creating new ones
- If similar learning exists in session, consider "strengthen" action instead
- Avoid redundant learnings within the same session

QUALITY GATE:
Only generate learnings that would make the agent:
- More EFFICIENT (fewer steps, less tokens, faster completion)
- More PERFORMANT (better outcomes, fewer errors, higher success rate)
- Better at SESSION MANAGEMENT (context awareness, user satisfaction)

OUTPUT JSON:
{{
  "action": "skip" | "update" | "create" | "strengthen",
  "reason": "Brief explanation of why this action was chosen",
  "update_learning_id": "learning_id to update (only if action=update/strengthen)",
  "learnings": [
    {{
      "learning": "Concise statement of what to do or avoid",
      "expected_outcome": "How this improves efficiency or performance",
      "basis": "Evidence from rationale supporting this learning",
      "confidence": 0.0-1.0,
      "session_relevance": 0.0-1.0
    }}
  ]
}}

For action="skip", learnings array should be empty.
For action="update"/"strengthen", learnings array contains the updated learning content.
For action="create", learnings array contains new learning(s).
"""

__all__ = ["LEARNING_GENERATION_PROMPT"]

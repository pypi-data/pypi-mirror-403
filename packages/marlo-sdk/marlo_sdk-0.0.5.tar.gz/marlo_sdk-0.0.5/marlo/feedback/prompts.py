"""Prompts for feedback chunk updating."""

from __future__ import annotations

REWARD_CHUNK_UPDATE_PROMPT = """
You are a reward evaluation guidelines manager. Your job is to maintain a list of guidelines that tell the reward system what NOT to do when evaluating agent performance.

CURRENT GUIDELINES:
{current_chunk}

CONTEXT - The reward system generated this rationale:
{rationale}

USER FEEDBACK - The user disagrees with the evaluation and provided this feedback:
{user_feedback}

INSTRUCTIONS:
1. Analyze the user feedback to understand what the reward system did wrong
2. Extract a clear, actionable guideline about what the reward system should NOT do
3. Update the guidelines list by:
   - Adding a new guideline if this is a new type of issue
   - Merging with an existing guideline if it's similar to one already present
   - Keeping the list concise and non-redundant

OUTPUT FORMAT:
Return ONLY the updated guidelines as a bullet-point list. Each guideline should:
- Start with "Do not" or "Avoid"
- Be specific and actionable
- Reference the type of behavior to avoid

Example format:
- Do not penalize the agent for asking clarifying questions before taking action
- Avoid marking as failure when external API returns timeout errors
- Do not consider multi-step reasoning as inefficient if it leads to correct outcomes

Return the complete updated guidelines list:
"""

LEARNING_CHUNK_UPDATE_PROMPT = """
You are a learning generation guidelines manager. Your job is to maintain a list of guidelines that tell the learning system what NOT to generate.

CURRENT GUIDELINES:
{current_chunk}

{context_section}

INSTRUCTIONS:
1. Analyze the user action to understand what kind of learnings are unwanted
2. Extract a clear, actionable guideline about what the learning system should NOT generate
3. Update the guidelines list by:
   - Adding a new guideline if this is a new type of issue
   - Merging with an existing guideline if it's similar to one already present
   - Keeping the list concise and non-redundant

OUTPUT FORMAT:
Return ONLY the updated guidelines as a bullet-point list. Each guideline should:
- Start with "Do not" or "Avoid"
- Be specific and actionable
- Reference the type of learning to avoid generating

Example format:
- Do not generate learnings about basic error handling that any developer knows
- Avoid creating learnings that are too generic and not actionable
- Do not suggest learnings that contradict standard best practices

Return the complete updated guidelines list:
"""

LEARNING_EDIT_CONTEXT = """
CONTEXT - The learning system generated this learning:
Original: {original_learning}

USER EDIT - The user modified it to:
Edited: {edited_learning}

The difference shows what kind of learnings the user prefers. Derive guidelines about what NOT to generate.
"""

LEARNING_REJECT_CONTEXT = """
CONTEXT - The learning system generated this learning:
{rejected_learning}

USER REJECTION - The user rejected it with this reason:
{rejection_reason}

Derive guidelines about what kind of learnings should NOT be generated.
"""

__all__ = [
    "REWARD_CHUNK_UPDATE_PROMPT",
    "LEARNING_CHUNK_UPDATE_PROMPT",
    "LEARNING_EDIT_CONTEXT",
    "LEARNING_REJECT_CONTEXT",
]

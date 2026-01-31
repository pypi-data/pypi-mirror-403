"""Session state management for stateful reward evaluation."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SessionRewardState:
    """Session state for stateful reward evaluation and learning."""
    
    session_id: str
    task_count: int = 0
    task_summaries: List[Dict[str, Any]] = None  # Last 3 detailed task summaries
    trajectory_digest: Optional[str] = None  # Compressed rolling summary of older tasks
    reward_scores: List[float] = None  # Recent reward scores
    reward_trend: Optional[str] = None  # "improving", "stable", "declining"
    sentiment_scores: List[float] = None  # Recent sentiment scores (0.0-1.0)
    sentiment_trend: Optional[str] = None  # "improving", "stable", "declining"
    learnings_generated_this_session: List[Dict[str, Any]] = None  # Learnings created in this session
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.task_summaries is None:
            self.task_summaries = []
        if self.reward_scores is None:
            self.reward_scores = []
        if self.sentiment_scores is None:
            self.sentiment_scores = []
        if self.learnings_generated_this_session is None:
            self.learnings_generated_this_session = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        if self.updated_at:
            data['updated_at'] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionRewardState':
        """Create from dictionary loaded from JSON."""
        data = dict(data)  # Make a copy
        if 'updated_at' in data and data['updated_at']:
            if isinstance(data['updated_at'], str):
                data['updated_at'] = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
        return cls(**data)

    def get_recent_scores_summary(self) -> Dict[str, Any]:
        """Get summary of recent performance."""
        return {
            "task_count": self.task_count,
            "recent_reward_scores": self.reward_scores[-5:] if self.reward_scores else [],
            "reward_trend": self.reward_trend,
            "recent_sentiment_scores": self.sentiment_scores[-5:] if self.sentiment_scores else [],
            "sentiment_trend": self.sentiment_trend,
            "learnings_count": len(self.learnings_generated_this_session)
        }


async def get_session_state(database, session_id: str) -> Optional[SessionRewardState]:
    """Fetch session reward state from database."""
    from marlo.storage.postgres.database import Database
    
    if not isinstance(database, Database):
        logger.error("Database instance required for session state operations")
        return None
        
    try:
        pool = database._require_pool()
        async with pool.acquire() as connection:
            row = await connection.fetchrow(
                "SELECT * FROM session_reward_states WHERE session_id = $1",
                session_id
            )
            
            if row is None:
                return SessionRewardState(session_id=session_id)
                
            # Deserialize JSON fields
            data = dict(row)
            for json_field in ['task_summaries', 'reward_scores', 'sentiment_scores', 'learnings_generated_this_session']:
                if data.get(json_field):
                    data[json_field] = database._deserialize_json(data[json_field])
                    
            return SessionRewardState.from_dict(data)
            
    except Exception as exc:
        logger.warning(f"Failed to fetch session state for {session_id}: {exc}")
        return SessionRewardState(session_id=session_id)


async def update_session_state(
    database,
    session_state: SessionRewardState,
    task_summary: Optional[Dict[str, Any]] = None,
    reward_score: Optional[float] = None,
    sentiment_score: Optional[float] = None,
    new_learning: Optional[Dict[str, Any]] = None
) -> SessionRewardState:
    """Update session state with new task information."""
    from marlo.storage.postgres.database import Database
    
    if not isinstance(database, Database):
        logger.error("Database instance required for session state operations")
        return session_state

    # Update task count
    if task_summary is not None:
        session_state.task_count += 1
        
        # Add new task summary, keep only last 3
        session_state.task_summaries.append(task_summary)
        if len(session_state.task_summaries) > 3:
            # Compress older summaries into digest
            session_state.trajectory_digest = await _merge_into_digest(
                database, 
                session_state.trajectory_digest,
                session_state.task_summaries[:-3]
            )
            session_state.task_summaries = session_state.task_summaries[-3:]

    # Update reward scores and trend
    if reward_score is not None:
        session_state.reward_scores.append(reward_score)
        # Keep last 10 scores
        if len(session_state.reward_scores) > 10:
            session_state.reward_scores = session_state.reward_scores[-10:]
        session_state.reward_trend = _calculate_trend(session_state.reward_scores)

    # Update sentiment scores and trend  
    if sentiment_score is not None:
        session_state.sentiment_scores.append(sentiment_score)
        # Keep last 10 scores
        if len(session_state.sentiment_scores) > 10:
            session_state.sentiment_scores = session_state.sentiment_scores[-10:]
        session_state.sentiment_trend = _calculate_trend(session_state.sentiment_scores)

    # Add new learning
    if new_learning is not None:
        session_state.learnings_generated_this_session.append(new_learning)

    session_state.updated_at = datetime.now(timezone.utc)

    # Persist to database
    await _persist_session_state(database, session_state)
    
    return session_state


async def compress_task_to_summary(
    database, 
    task_text: str, 
    final_answer: str, 
    reward_result: Dict[str, Any],
    task_metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """Compress a task trajectory into a summary using Gemini Flash."""
    from marlo.runtime.llm_client import LLMClient
    from marlo.billing import BillingLLMClient, USAGE_TYPE_REWARD_FLASH
    
    # Extract key information
    score = reward_result.get('score', 0.0)
    rationale = reward_result.get('rationale', '')
    principles = reward_result.get('principles', [])
    
    # Build compression prompt
    prompt = f"""
Role: Task Summarizer. Compress this task execution into key insights for session context.

Task: {task_text}
Final Answer: {final_answer}
Score: {score}
Rationale: {rationale}

Instructions:
Create a compressed summary focusing on:
1. Task type and complexity 
2. Agent performance (strengths/weaknesses)
3. Key learnings or patterns
4. Context that might matter for future tasks

Output JSON only:
{{
  "task_type": "brief task categorization",
  "score": {score},
  "key_insights": "3-4 sentence summary of what happened and why",
  "patterns": ["pattern1", "pattern2"],
  "context_value": 0.0-1.0
}}
"""

    try:
        # Use Gemini Flash for cheap compression
        client = LLMClient(model="gemini/gemini-3-flash-preview", params={"temperature": 0.0})
        
        # TODO: Add billing if user_id/project_id available
        # For now, use base client
        
        response = await client.acomplete(
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        content = response.content
        if not content:
            raise ValueError("Empty response from compression model")
            
        summary = json.loads(content)
        
        # Add metadata
        summary.update({
            "task_id": task_metadata.get("task_id"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "original_score": score
        })
        
        return summary
        
    except Exception as exc:
        logger.warning(f"Task compression failed: {exc}")
        # Fallback summary
        return {
            "task_type": "unknown",
            "score": score,
            "key_insights": f"Task completed with score {score}. {rationale[:100]}",
            "patterns": [],
            "context_value": 0.3,
            "task_id": task_metadata.get("task_id"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "original_score": score,
            "compression_error": str(exc)
        }


async def _merge_into_digest(
    database, 
    current_digest: Optional[str], 
    summaries_to_compress: List[Dict[str, Any]]
) -> str:
    """Merge task summaries into a rolling digest."""
    from marlo.runtime.llm_client import LLMClient
    
    if not summaries_to_compress:
        return current_digest or ""
    
    # Build merge prompt
    summaries_text = json.dumps(summaries_to_compress, indent=2)
    
    prompt = f"""
Role: Session Digest Manager. Merge task summaries into a rolling session digest.

Current Digest: {current_digest or "None"}

New Summaries to Merge:
{summaries_text}

Instructions:
Create a compressed digest that preserves:
1. Overall session trajectory and evolution
2. Key patterns across tasks
3. Important context for future evaluation
4. Performance trends

Keep it concise (2-3 sentences). Focus on what matters for understanding agent behavior over time.

Output just the digest text, no JSON.
"""

    try:
        client = LLMClient(model="gemini/gemini-3-flash-preview", params={"temperature": 0.0})
        
        response = await client.acomplete(
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content.strip() if response.content else current_digest or ""
        
    except Exception as exc:
        logger.warning(f"Digest merge failed: {exc}")
        # Fallback: append summaries
        new_content = "; ".join([s.get("key_insights", "") for s in summaries_to_compress])
        if current_digest:
            return f"{current_digest}; {new_content}"
        return new_content


def _calculate_trend(scores: List[float]) -> str:
    """Calculate trend from recent scores."""
    if len(scores) < 3:
        return "insufficient_data"
    
    recent = scores[-3:]
    if len(recent) < 3:
        return "insufficient_data"
        
    # Simple trend calculation
    if recent[-1] > recent[0] + 0.05:  # Improving
        return "improving"
    elif recent[-1] < recent[0] - 0.05:  # Declining  
        return "declining"
    else:
        return "stable"


async def _persist_session_state(database, session_state: SessionRewardState) -> None:
    """Persist session state to database."""
    try:
        pool = database._require_pool()
        async with pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO session_reward_states (
                    session_id, task_count, trajectory_digest, task_summaries, 
                    reward_scores, sentiment_scores, learnings_generated_this_session, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (session_id) DO UPDATE SET
                    task_count = EXCLUDED.task_count,
                    trajectory_digest = EXCLUDED.trajectory_digest,
                    task_summaries = EXCLUDED.task_summaries,
                    reward_scores = EXCLUDED.reward_scores,
                    sentiment_scores = EXCLUDED.sentiment_scores, 
                    learnings_generated_this_session = EXCLUDED.learnings_generated_this_session,
                    updated_at = EXCLUDED.updated_at
                """,
                session_state.session_id,
                session_state.task_count,
                session_state.trajectory_digest,
                database._serialize_json(session_state.task_summaries),
                database._serialize_json(session_state.reward_scores),
                database._serialize_json(session_state.sentiment_scores),
                database._serialize_json(session_state.learnings_generated_this_session),
                session_state.updated_at
            )
    except Exception as exc:
        logger.error(f"Failed to persist session state: {exc}")


__all__ = [
    "SessionRewardState",
    "get_session_state", 
    "update_session_state",
    "compress_task_to_summary"
]
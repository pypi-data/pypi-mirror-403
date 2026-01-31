"""Progressive compression utilities for session state management."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


async def compress_task_to_summary(
    task_text: str,
    final_answer: str, 
    reward_result: Dict[str, Any],
    task_metadata: Dict[str, Any],
    *,
    user_id: Optional[str] = None,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compress a task trajectory into a concise summary using Gemini Flash.
    
    Args:
        task_text: The original task/request
        final_answer: Agent's final response
        reward_result: Reward evaluation result with score, rationale, etc.
        task_metadata: Additional task context
        user_id: User ID for billing (optional)
        project_id: Project ID for billing (optional)
        
    Returns:
        Dictionary containing compressed task summary
    """
    from marlo.runtime.llm_client import LLMClient
    from marlo.billing import BillingLLMClient, USAGE_TYPE_REWARD_FLASH
    
    # Extract key information
    score = reward_result.get('score', 0.0)
    rationale = reward_result.get('rationale', '')
    principles = reward_result.get('principles', [])
    is_technical_error = reward_result.get('is_technical_error', False)
    
    # Build compression prompt
    prompt = f"""
Role: Task Trajectory Compressor. Create a concise summary for session state tracking.

INPUTS:
Task: {task_text[:500]}
Final Answer: {final_answer[:300]}
Score: {score}
Rationale: {rationale[:400]}
Is Technical Error: {is_technical_error}

Instructions:
Compress this task execution into essential information for session context tracking.

Focus on:
1. Task type/category (e.g., "code_debugging", "data_analysis", "creative_writing")
2. Performance quality and key issues
3. Notable patterns in agent behavior
4. Context that might impact future tasks

Output JSON only:
{{
  "task_type": "brief_category",
  "score": {score},
  "performance_summary": "2-3 sentence summary of how the agent performed",
  "key_patterns": ["pattern1", "pattern2"],
  "issues_noted": ["issue1", "issue2"], 
  "context_relevance": 0.0-1.0,
  "technical_error": {str(is_technical_error).lower()}
}}
"""

    try:
        # Create client
        base_client = LLMClient(
            model="gemini/gemini-3-flash-preview", 
            params={"temperature": 0.0}
        )
        
        # Use billing client if credentials provided
        if user_id:
            client = BillingLLMClient(
                base_client,
                user_id=user_id,
                project_id=project_id,
                usage_type=USAGE_TYPE_REWARD_FLASH,
            )
        else:
            client = base_client
        
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
            "timestamp": task_metadata.get("timestamp"),
            "original_score": score,
            "compression_model": "gemini-3-flash-preview"
        })
        
        return summary
        
    except Exception as exc:
        logger.warning(f"Task compression failed: {exc}")
        # Fallback summary
        return {
            "task_type": "unknown",
            "score": score,
            "performance_summary": f"Task completed with score {score:.2f}. {rationale[:150]}...",
            "key_patterns": [],
            "issues_noted": ["compression_failed"],
            "context_relevance": 0.3,
            "technical_error": is_technical_error,
            "task_id": task_metadata.get("task_id"),
            "timestamp": task_metadata.get("timestamp"), 
            "original_score": score,
            "compression_error": str(exc)[:200]
        }


async def merge_into_digest(
    current_digest: Optional[str],
    summaries_to_compress: List[Dict[str, Any]],
    *,
    user_id: Optional[str] = None,
    project_id: Optional[str] = None
) -> str:
    """
    Merge multiple task summaries into a rolling session digest.
    
    Args:
        current_digest: Existing digest text (if any)
        summaries_to_compress: List of task summaries to merge in
        user_id: User ID for billing (optional)
        project_id: Project ID for billing (optional)
        
    Returns:
        Updated digest string
    """
    from marlo.runtime.llm_client import LLMClient
    from marlo.billing import BillingLLMClient, USAGE_TYPE_REWARD_FLASH
    
    if not summaries_to_compress:
        return current_digest or ""
    
    # Extract key information from summaries
    summary_data = []
    for summary in summaries_to_compress:
        summary_data.append({
            "task_type": summary.get("task_type", "unknown"),
            "score": summary.get("score", 0.0),
            "performance_summary": summary.get("performance_summary", ""),
            "key_patterns": summary.get("key_patterns", []),
            "issues_noted": summary.get("issues_noted", [])
        })
    
    summaries_json = json.dumps(summary_data, indent=2)
    
    prompt = f"""
Role: Session Digest Manager. Merge task summaries into a rolling session context.

Current Session Digest:
{current_digest or "[No prior digest]"}

New Task Summaries to Merge:
{summaries_json}

Instructions:
Create an updated session digest that captures:
1. Overall progression and evolution of the session
2. Recurring patterns across tasks
3. Performance trends and trajectory
4. Key context that affects agent behavior

Keep digest concise (3-4 sentences max). Focus on session-level insights, not individual task details.

Output just the digest text (no JSON wrapper).
"""

    try:
        # Create client
        base_client = LLMClient(
            model="gemini/gemini-3-flash-preview",
            params={"temperature": 0.0}
        )
        
        # Use billing client if credentials provided
        if user_id:
            client = BillingLLMClient(
                base_client,
                user_id=user_id,
                project_id=project_id,
                usage_type=USAGE_TYPE_REWARD_FLASH,
            )
        else:
            client = base_client
        
        response = await client.acomplete(
            messages=[{"role": "user", "content": prompt}]
        )
        
        new_digest = response.content.strip() if response.content else ""
        
        # Ensure digest isn't too long
        if len(new_digest) > 800:
            new_digest = new_digest[:797] + "..."
            
        return new_digest
        
    except Exception as exc:
        logger.warning(f"Digest merge failed: {exc}")
        
        # Fallback: create simple merged digest
        try:
            performance_texts = []
            for summary in summaries_to_compress:
                perf = summary.get("performance_summary", "")
                if perf:
                    performance_texts.append(perf[:100])
            
            new_content = "; ".join(performance_texts)
            
            if current_digest:
                combined = f"{current_digest}; Recent tasks: {new_content}"
            else:
                combined = f"Session summary: {new_content}"
                
            # Truncate if too long
            if len(combined) > 800:
                combined = combined[:797] + "..."
                
            return combined
            
        except Exception:
            return current_digest or "Session tracking failed"


def estimate_compression_value(summaries: List[Dict[str, Any]]) -> float:
    """
    Estimate the value of compressing summaries vs keeping them detailed.
    
    Args:
        summaries: List of task summaries to evaluate
        
    Returns:
        Value score 0.0-1.0 (higher = more valuable to compress)
    """
    if not summaries:
        return 0.0
    
    # Factors that increase compression value:
    # - High number of summaries
    # - Lower context relevance scores
    # - Older timestamps
    # - Technical errors (less valuable for learning)
    
    try:
        count_factor = min(len(summaries) / 5.0, 1.0)  # More summaries = more compression value
        
        relevance_scores = []
        error_count = 0
        
        for summary in summaries:
            relevance = summary.get("context_relevance", 0.5)
            relevance_scores.append(relevance)
            
            if summary.get("technical_error", False):
                error_count += 1
        
        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.5
        relevance_factor = 1.0 - avg_relevance  # Lower relevance = higher compression value
        
        error_factor = min(error_count / len(summaries), 0.5)  # Technical errors add compression value
        
        # Weighted combination
        compression_value = (
            count_factor * 0.4 + 
            relevance_factor * 0.4 + 
            error_factor * 0.2
        )
        
        return min(max(compression_value, 0.0), 1.0)
        
    except Exception as exc:
        logger.debug(f"Compression value estimation failed: {exc}")
        return 0.5  # Default moderate compression value


__all__ = [
    "compress_task_to_summary",
    "merge_into_digest", 
    "estimate_compression_value"
]
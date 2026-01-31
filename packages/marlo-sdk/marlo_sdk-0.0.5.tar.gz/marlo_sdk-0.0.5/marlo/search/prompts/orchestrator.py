"""Orchestrator prompts - dynamically constructed from live schema."""

from __future__ import annotations


def build_query_understanding_prompt(query: str, schema_context: str) -> str:
    """Build the query understanding prompt with dynamic schema context.

    Args:
        query: The user's natural language query
        schema_context: Auto-generated schema description from SchemaIntrospector

    Returns:
        Complete prompt for query understanding
    """
    return f"""You are an expert search planner for an AI agent observability platform.

## Available Data (from live database)

{schema_context}

## Your Task
Analyze the user's query and create a search plan to find the most relevant data.

## User Query
"{query}"

## Output Format
Return a JSON object with this structure:
```json
{{
    "intent": "Clear description of what the user wants to find",
    "search_strategy": "focused|broad|aggregation",
    "filters": {{
        "time_range": "last_24_hours|last_7_days|last_30_days|all",
        "status": null or specific status value from sample values above,
        "event_types": null or array of event types from sample values above,
        "agent_id": null or specific agent,
        "tool_name": null or specific tool
    }},
    "priority_fields": ["list", "of", "important", "columns", "to", "return"],
    "sub_queries": [
        {{
            "description": "What this query should find",
            "sql_hint": "Brief hint about which table and conditions to use",
            "priority": 1
        }}
    ]
}}
```

## Guidelines

1. **Use actual table/column names** from the schema above
2. **Use actual status/type values** from the sample values shown
3. **Create focused sub-queries** - each should target a specific aspect
4. **Prioritize by relevance** - priority 1 is most important
5. **Consider relationships** - use foreign keys to join related data
6. **Limit sub-queries** - maximum 4 sub-queries

## Search Strategies

- **focused**: User wants specific records (e.g., "show me failed tasks")
- **broad**: User wants to explore patterns (e.g., "what's happening with my agents")
- **aggregation**: User wants statistics (e.g., "success rate by agent")

Generate the search plan now:"""


def build_synthesis_prompt(
    query: str,
    facts: list[str],
    patterns: list[str],
    stats: dict[str, int],
) -> str:
    """Build the synthesis prompt for generating the final answer.

    Args:
        query: Original user query
        facts: List of extracted facts
        patterns: List of discovered patterns
        stats: Statistics about the search (sessions_analyzed, events_analyzed, etc.)

    Returns:
        Complete prompt for synthesis
    """
    facts_text = "\n".join(f"- {f}" for f in facts) if facts else "No facts extracted."
    patterns_text = "\n".join(f"- {p}" for p in patterns) if patterns else "No patterns found."

    return f"""You are an expert analyst for an AI agent observability platform.

## User Query
"{query}"

## Search Statistics
- Sessions analyzed: {stats.get('sessions_analyzed', 0)}
- Events analyzed: {stats.get('events_analyzed', 0)}
- Facts extracted: {stats.get('facts_extracted', 0)}

## Extracted Facts
{facts_text}

## Discovered Patterns
{patterns_text}

## Your Task
Synthesize the findings into a clear, actionable answer for the user.

## Output Format
Return a JSON object:
```json
{{
    "answer": "Clear, comprehensive answer to the user's query. Use markdown formatting.",
    "confidence": 0.0 to 1.0,
    "key_findings": ["Most important finding 1", "Finding 2", "Finding 3"],
    "evidence_citations": ["Specific data points that support the findings"],
    "patterns_discovered": ["Any patterns or trends noticed"],
    "data_coverage": {{
        "sessions_analyzed": number,
        "events_analyzed": number,
        "time_range": "description of time range covered",
        "completeness": "Assessment of data completeness"
    }},
    "limitations": "Any caveats or limitations of the analysis",
    "suggested_follow_ups": ["Suggested next questions or actions"]
}}
```

## Guidelines

1. **Be specific** - Reference actual data when possible
2. **Be actionable** - Provide concrete recommendations
3. **Be honest** - If data is limited, say so
4. **Use markdown** - Format the answer for readability

Generate the synthesis now:"""

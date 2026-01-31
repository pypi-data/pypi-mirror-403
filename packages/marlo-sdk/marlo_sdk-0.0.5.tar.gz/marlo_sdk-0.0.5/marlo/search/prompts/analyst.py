"""Prompts for Analyst Agent - Fact Extraction and Pattern Recognition."""

ANALYSIS_PROMPT = """You are an expert analyst extracting insights from AI agent execution traces. Your job is to find facts that answer the user's question.

## Search Context
**User's Question**: {search_context}

## Previously Found Facts (maintain continuity, avoid duplicates)
{existing_facts}

## Events to Analyze
```json
{events}
```

## Your Task
Extract relevant facts from these events that help answer the user's question. Focus on actionable insights, not raw data dumps.

## Fact Quality Guidelines

### Importance Scoring (0.0 - 1.0)
- **0.9 - 1.0**: Directly answers the user's question. Smoking gun evidence.
  - Example: "Browser tool failed with 'element not found' error on login page" (if user asked about browser failures)
- **0.7 - 0.8**: Strongly related, provides key context or supporting evidence.
  - Example: "Session took 45 seconds, 80% spent waiting for browser responses"
- **0.5 - 0.6**: Moderately relevant, useful background information.
  - Example: "Agent made 12 tool calls before the failure occurred"
- **0.3 - 0.4**: Tangentially related, might be useful for complete picture.
  - Example: "Session was initiated at 3 AM UTC"
- **Below 0.3**: Not relevant - DO NOT INCLUDE these facts.

### What Makes a Good Fact
✅ Specific and concrete (includes numbers, error messages, tool names)
✅ Answers "what", "why", or "how"
✅ Can be cited back to source (session_id, event_id)
✅ Not a duplicate of existing facts
✅ Actionable or diagnostic value

### What to Avoid
❌ Vague statements ("something went wrong")
❌ Raw data without interpretation ("event_type was tool_call")
❌ Duplicates of existing facts
❌ Irrelevant details that don't help answer the question
❌ Facts below 0.3 importance

## Output Format
```json
{{
    "facts": [
        {{
            "content": "Clear, specific description of the finding",
            "importance": 0.85,
            "source_session_id": 12345,
            "source_event_id": 67890,
            "event_type": "tool_call",
            "agent_id": "customer_support"
        }}
    ],
    "patterns": [
        "Pattern observed across multiple events"
    ],
    "suggested_refinements": [
        "Specific follow-up query if gaps exist"
    ]
}}
```

## Examples

### Example 1: Error Investigation
**Search Context**: "Why did browser tools fail yesterday?"

**Events**:
```json
[
    {{"id": 101, "session_id": 500, "event": {{"event_type": "tool_call", "agent_id": "web_agent", "payload": {{"tool_name": "browser_click", "tool_input": {{"selector": "#login-btn"}}, "error": "Element not found: #login-btn", "duration_ms": 5000}}}}}},
    {{"id": 102, "session_id": 500, "event": {{"event_type": "tool_call", "agent_id": "web_agent", "payload": {{"tool_name": "browser_navigate", "tool_input": {{"url": "https://app.example.com"}}, "tool_output": "Page loaded", "duration_ms": 3500}}}}}},
    {{"id": 103, "session_id": 501, "event": {{"event_type": "tool_call", "agent_id": "web_agent", "payload": {{"tool_name": "browser_click", "error": "Timeout waiting for element", "duration_ms": 30000}}}}}}
]
```

**Output**:
```json
{{
    "facts": [
        {{
            "content": "browser_click failed with 'Element not found: #login-btn' after 5 seconds - selector may have changed or page not fully loaded",
            "importance": 0.95,
            "source_session_id": 500,
            "source_event_id": 101,
            "event_type": "tool_call",
            "agent_id": "web_agent"
        }},
        {{
            "content": "browser_click timed out after 30 seconds waiting for element - indicates slow page load or missing element",
            "importance": 0.9,
            "source_session_id": 501,
            "source_event_id": 103,
            "event_type": "tool_call",
            "agent_id": "web_agent"
        }},
        {{
            "content": "browser_navigate succeeded (3.5s load time) before the click failure - page loaded but element was missing",
            "importance": 0.7,
            "source_session_id": 500,
            "source_event_id": 102,
            "event_type": "tool_call",
            "agent_id": "web_agent"
        }}
    ],
    "patterns": [
        "Browser click operations are failing after successful page navigation - suggests element selector issues rather than connectivity",
        "Failure modes include both 'element not found' and 'timeout' - may indicate inconsistent page loading"
    ],
    "suggested_refinements": [
        "Search for successful browser_click events to compare selectors used"
    ]
}}
```

### Example 2: Performance Analysis
**Search Context**: "Which agents are slowest?"

**Events**:
```json
[
    {{"id": 201, "session_id": 600, "event": {{"event_type": "agent_end", "agent_id": "data_processor", "payload": {{"duration_ms": 45000, "status": "success"}}}}}},
    {{"id": 202, "session_id": 600, "event": {{"event_type": "agent_end", "agent_id": "report_generator", "payload": {{"duration_ms": 12000, "status": "success"}}}}}},
    {{"id": 203, "session_id": 601, "event": {{"event_type": "agent_end", "agent_id": "data_processor", "payload": {{"duration_ms": 52000, "status": "success"}}}}}},
    {{"id": 204, "session_id": 601, "event": {{"event_type": "llm_call", "agent_id": "data_processor", "payload": {{"model": "gpt-4", "usage": {{"total_tokens": 8500}}, "duration_ms": 15000}}}}}}
]
```

**Output**:
```json
{{
    "facts": [
        {{
            "content": "data_processor agent consistently takes 45-52 seconds per execution - significantly slower than other agents",
            "importance": 0.95,
            "source_session_id": 600,
            "source_event_id": 201,
            "event_type": "agent_end",
            "agent_id": "data_processor"
        }},
        {{
            "content": "data_processor spends ~15 seconds (30%) on a single LLM call using 8,500 tokens - large context may be causing slowdown",
            "importance": 0.85,
            "source_session_id": 601,
            "source_event_id": 204,
            "event_type": "llm_call",
            "agent_id": "data_processor"
        }},
        {{
            "content": "report_generator completes in 12 seconds - 4x faster than data_processor",
            "importance": 0.7,
            "source_session_id": 600,
            "source_event_id": 202,
            "event_type": "agent_end",
            "agent_id": "report_generator"
        }}
    ],
    "patterns": [
        "data_processor is consistently the slowest agent, with LLM calls consuming significant time",
        "High token usage (8500 tokens) correlates with longer execution time"
    ],
    "suggested_refinements": [
        "Analyze data_processor's LLM prompts to identify optimization opportunities"
    ]
}}
```

### Example 3: Success Pattern Analysis
**Search Context**: "What do successful sessions have in common?"

**Events**:
```json
[
    {{"id": 301, "session_id": 700, "event": {{"event_type": "agent_end", "agent_id": "assistant", "payload": {{"status": "success", "tool_calls": 3, "llm_calls": 2}}}}}},
    {{"id": 302, "session_id": 701, "event": {{"event_type": "agent_end", "agent_id": "assistant", "payload": {{"status": "success", "tool_calls": 4, "llm_calls": 2}}}}}},
    {{"id": 303, "session_id": 702, "event": {{"event_type": "agent_end", "agent_id": "assistant", "payload": {{"status": "failed", "tool_calls": 8, "llm_calls": 5}}}}}}
]
```

**Output**:
```json
{{
    "facts": [
        {{
            "content": "Successful sessions used 3-4 tool calls and 2 LLM calls on average - efficient execution pattern",
            "importance": 0.9,
            "source_session_id": 700,
            "source_event_id": 301,
            "event_type": "agent_end",
            "agent_id": "assistant"
        }},
        {{
            "content": "Failed session had 2x more tool calls (8) and 2.5x more LLM calls (5) than successful ones - suggests thrashing or retry loops",
            "importance": 0.85,
            "source_session_id": 702,
            "source_event_id": 303,
            "event_type": "agent_end",
            "agent_id": "assistant"
        }}
    ],
    "patterns": [
        "Successful sessions complete with fewer iterations - 3-4 tool calls vs 8+ for failures",
        "Lower LLM call count correlates with success - may indicate clearer task understanding"
    ],
    "suggested_refinements": [
        "Examine the specific tool calls in failed sessions to identify retry patterns"
    ]
}}
```

### Example 4: No Relevant Data
**Search Context**: "Show me Slack integration errors"

**Events**:
```json
[
    {{"id": 401, "session_id": 800, "event": {{"event_type": "tool_call", "agent_id": "assistant", "payload": {{"tool_name": "browser_navigate", "tool_output": "Success"}}}}}},
    {{"id": 402, "session_id": 800, "event": {{"event_type": "llm_call", "agent_id": "assistant", "payload": {{"model": "gpt-4", "response": {{"content": "I'll help you..."}}}}}}}}
]
```

**Output**:
```json
{{
    "facts": [],
    "patterns": [],
    "suggested_refinements": [
        "No Slack-related events found in this batch - try searching for tool_name containing 'slack'",
        "Verify Slack integration is configured and has been used recently"
    ]
}}
```

## Guidelines
1. **Be specific** - Include exact error messages, numbers, durations
2. **Interpret, don't just report** - "Failed after 30s timeout" is better than "duration_ms was 30000"
3. **Connect to the question** - Every fact should help answer the user's query
4. **Identify patterns** - Look for commonalities across events
5. **Avoid duplicates** - Check existing_facts before adding similar facts
6. **Suggest next steps** - If data is incomplete, suggest what to search for

Return ONLY the JSON object, no additional text.
"""

CHUNK_SUMMARY_PROMPT = """Summarize the analysis of this chunk of trajectory events.

## Context
**Search Question**: {search_context}
**Events Analyzed**: {event_count}
**Facts Extracted**: {fact_count}

## Key Facts Found
{facts_summary}

## Patterns Identified
{patterns}

## Your Task
Provide a 2-3 sentence summary of what was found in this chunk that helps answer the user's question.

## Guidelines
- Focus on the most important findings
- Note any patterns or trends
- Mention data gaps if relevant
- Keep it concise and actionable

## Example Summaries

**Good**: "Found 3 browser timeout errors, all occurring on the checkout page with >30s wait times. Pattern suggests the checkout page has performance issues or changed selectors."

**Good**: "Analyzed 50 successful sessions - average completion time was 12s with 3 tool calls. No errors found in this batch."

**Good**: "No relevant data found for Slack integration in this chunk. Events were primarily browser and LLM calls."

**Bad**: "Processed 50 events and found some facts." (Too vague)

**Bad**: "Event IDs 101-150 were analyzed." (Not useful)

Return ONLY a brief summary paragraph, no JSON.
"""

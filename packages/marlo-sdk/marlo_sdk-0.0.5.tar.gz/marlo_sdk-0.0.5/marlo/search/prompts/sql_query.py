"""SQL query generation prompts - dynamically constructed from live schema."""

from __future__ import annotations


def build_sql_generation_prompt(schema_context: str, search_plan_json: str, sub_query: str) -> str:
    """Build the SQL generation prompt with dynamic schema context.

    Args:
        schema_context: Auto-generated schema description from SchemaIntrospector
        search_plan_json: JSON string of the search plan
        sub_query: The specific sub-query to generate SQL for

    Returns:
        Complete prompt for SQL generation
    """
    return f"""You are an expert PostgreSQL query generator for an AI agent observability system.

{schema_context}

## Critical Rules

1. **ALWAYS filter by project_id**: Every query MUST include `WHERE project_id = $1`
2. **Use exact column names**: Only use columns that exist in the schema above
3. **Use actual values**: When filtering by status, event_type, etc., use the sample values shown above
4. **Parameter placeholders**: Use $1 for project_id, $2, $3, etc. for additional parameters
5. **Safe queries only**: SELECT only, no writes, no DROP, no TRUNCATE
6. **Limit results**: Always include LIMIT (max 1000) to prevent huge result sets
7. **JSONB access**: For JSONB columns like `event`, use `->` for objects and `->>` for text values

## Search Plan
```json
{search_plan_json}
```

## Sub-Query to Generate SQL For
{sub_query}

## Output Format
Return a JSON object with exactly this structure:
```json
{{
    "query": "SELECT ... FROM ... WHERE project_id = $1 ...",
    "params": [],
    "description": "Brief description of what this query finds"
}}
```

Notes:
- `params` array contains values for $2, $3, etc. (NOT $1 which is always project_id)
- Keep queries simple and focused on the sub-query's intent
- Use appropriate JOINs when data spans multiple tables
- For JSONB fields, extract relevant nested values

Generate the SQL query now:"""


def build_sql_validation_prompt(query: str, schema_context: str) -> str:
    """Build prompt to validate a SQL query against the schema."""
    return f"""Validate this SQL query against the schema.

{schema_context}

## Query to Validate
```sql
{query}
```

## Check for:
1. All column names exist in the referenced tables
2. project_id filter is present
3. Query is SELECT only (no writes)
4. LIMIT clause is present
5. JSONB access syntax is correct

Return JSON:
```json
{{
    "is_valid": true/false,
    "errors": ["list of issues if any"],
    "suggestions": ["improvements if any"]
}}
```"""

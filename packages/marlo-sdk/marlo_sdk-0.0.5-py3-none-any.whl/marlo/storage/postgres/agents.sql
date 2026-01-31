CREATE TABLE IF NOT EXISTS agent_registry (
    definition_hash TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    tool_definitions JSONB NOT NULL,
    mcp_definitions JSONB,
    model_config JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS session_agents (
    session_id BIGINT REFERENCES sessions(id) ON DELETE CASCADE,
    agent_id TEXT NOT NULL,
    parent_agent_id TEXT,
    invocation_id TEXT,
    definition_hash TEXT REFERENCES agent_registry(definition_hash) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (session_id, agent_id)
);

CREATE TABLE IF NOT EXISTS agent_rewards (
    session_id BIGINT REFERENCES sessions(id) ON DELETE CASCADE,
    task_id BIGINT REFERENCES session_tasks(id) ON DELETE CASCADE,
    agent_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    org_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    score FLOAT,
    rationale JSONB,
    principles JSONB,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (session_id, task_id, agent_id)
);

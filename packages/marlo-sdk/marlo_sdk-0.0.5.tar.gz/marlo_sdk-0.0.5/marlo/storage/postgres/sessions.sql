CREATE TABLE IF NOT EXISTS sessions (
    id BIGSERIAL PRIMARY KEY,
    task TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    project_id TEXT NOT NULL,
    org_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    metadata JSONB,
    final_answer TEXT,
    reward JSONB,
    reward_stats JSONB,
    reward_audit JSONB,
    learning TEXT,
    review_status TEXT NOT NULL DEFAULT 'pending',
    review_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS discovery_runs (
    id BIGSERIAL PRIMARY KEY,
    project_root TEXT NOT NULL,
    task TEXT,
    source TEXT NOT NULL DEFAULT 'discovery',
    payload JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS sessions_learning_key_idx
    ON sessions ((metadata ->> 'learning_key'));

CREATE INDEX IF NOT EXISTS sessions_reward_score_idx
    ON sessions(((reward_stats->>'score')::float))
    WHERE reward_stats IS NOT NULL;

CREATE INDEX IF NOT EXISTS sessions_created_at_idx
    ON sessions(created_at DESC);

CREATE INDEX IF NOT EXISTS sessions_metadata_gin_idx
    ON sessions USING gin(metadata);

CREATE INDEX IF NOT EXISTS sessions_project_id_idx
    ON sessions(project_id);

-- Session reward states table for stateful evaluation
CREATE TABLE IF NOT EXISTS session_reward_states (
    session_id TEXT PRIMARY KEY,
    task_count INTEGER NOT NULL DEFAULT 0,
    trajectory_digest TEXT,
    task_summaries JSONB NOT NULL DEFAULT '[]'::jsonb,
    reward_scores JSONB NOT NULL DEFAULT '[]'::jsonb,
    sentiment_scores JSONB NOT NULL DEFAULT '[]'::jsonb,
    learnings_generated_this_session JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS session_reward_states_updated_at_idx
    ON session_reward_states(updated_at DESC);

CREATE INDEX IF NOT EXISTS session_reward_states_task_count_idx
    ON session_reward_states(task_count);

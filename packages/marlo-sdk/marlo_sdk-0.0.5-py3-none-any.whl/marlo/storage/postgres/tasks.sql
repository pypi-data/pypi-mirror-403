CREATE TABLE IF NOT EXISTS session_tasks (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT REFERENCES sessions(id) ON DELETE CASCADE,
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
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS session_tasks_session_id_idx
    ON session_tasks(session_id);

CREATE INDEX IF NOT EXISTS session_tasks_learning_key_idx
    ON session_tasks ((metadata ->> 'learning_key'));

CREATE INDEX IF NOT EXISTS session_tasks_created_at_idx
    ON session_tasks(created_at DESC);

CREATE INDEX IF NOT EXISTS session_tasks_project_id_idx
    ON session_tasks(project_id);

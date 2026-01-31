CREATE TABLE IF NOT EXISTS reward_jobs (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT REFERENCES sessions(id) ON DELETE CASCADE,
    task_id BIGINT REFERENCES session_tasks(id) ON DELETE CASCADE,
    scope TEXT NOT NULL DEFAULT 'task',
    agent_id TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    project_id TEXT NOT NULL,
    org_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS reward_jobs_status_idx
    ON reward_jobs(status);

CREATE UNIQUE INDEX IF NOT EXISTS reward_jobs_session_scope_agent_idx
    ON reward_jobs(session_id, task_id, scope, COALESCE(agent_id, ''));

CREATE INDEX IF NOT EXISTS reward_jobs_project_id_idx
    ON reward_jobs(project_id);

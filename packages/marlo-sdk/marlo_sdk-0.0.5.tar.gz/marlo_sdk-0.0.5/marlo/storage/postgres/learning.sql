CREATE TABLE IF NOT EXISTS learning_objects (
    learning_id TEXT PRIMARY KEY,
    learning_key TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    org_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    learning TEXT NOT NULL,
    expected_outcome TEXT NOT NULL,
    basis TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS learning_objects_key_idx
    ON learning_objects(learning_key);

CREATE INDEX IF NOT EXISTS learning_objects_status_idx
    ON learning_objects(status);

CREATE INDEX IF NOT EXISTS learning_objects_project_id_idx
    ON learning_objects(project_id);

CREATE TABLE IF NOT EXISTS learning_reviews (
    id BIGSERIAL PRIMARY KEY,
    learning_id TEXT NOT NULL REFERENCES learning_objects(learning_id) ON DELETE CASCADE,
    project_id TEXT NOT NULL,
    org_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    reason TEXT,
    edited_learning TEXT,
    edited_expected_outcome TEXT,
    edited_basis TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS learning_reviews_learning_id_idx
    ON learning_reviews(learning_id);

CREATE TABLE IF NOT EXISTS learning_evidence (
    id BIGSERIAL PRIMARY KEY,
    learning_id TEXT NOT NULL REFERENCES learning_objects(learning_id) ON DELETE CASCADE,
    task_id BIGINT NOT NULL REFERENCES session_tasks(id) ON DELETE CASCADE,
    project_id TEXT NOT NULL,
    org_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    rationale_snippet TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (learning_id, task_id)
);

CREATE INDEX IF NOT EXISTS learning_evidence_learning_id_idx
    ON learning_evidence(learning_id);

CREATE INDEX IF NOT EXISTS learning_evidence_project_id_idx
    ON learning_evidence(project_id);

CREATE TABLE IF NOT EXISTS learning_usage (
    id BIGSERIAL PRIMARY KEY,
    learning_id TEXT NOT NULL REFERENCES learning_objects(learning_id) ON DELETE CASCADE,
    task_id BIGINT NOT NULL REFERENCES session_tasks(id) ON DELETE CASCADE,
    project_id TEXT NOT NULL,
    org_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    reward_score DOUBLE PRECISION,
    token_total DOUBLE PRECISION,
    failure_flag BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (learning_id, task_id)
);

CREATE INDEX IF NOT EXISTS learning_usage_learning_id_idx
    ON learning_usage(learning_id);

CREATE INDEX IF NOT EXISTS learning_usage_project_id_idx
    ON learning_usage(project_id);

CREATE TABLE IF NOT EXISTS learning_rollouts (
    id BIGSERIAL PRIMARY KEY,
    learning_id TEXT NOT NULL REFERENCES learning_objects(learning_id) ON DELETE CASCADE,
    previous_status TEXT,
    new_status TEXT NOT NULL,
    reason TEXT NOT NULL,
    project_id TEXT NOT NULL,
    org_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS learning_rollouts_learning_id_idx
    ON learning_rollouts(learning_id);

CREATE INDEX IF NOT EXISTS learning_rollouts_project_id_idx
    ON learning_rollouts(project_id);

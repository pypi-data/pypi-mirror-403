-- Project feedback chunks for reward and learning guidance
CREATE TABLE IF NOT EXISTS project_feedback_chunks (
    id BIGSERIAL PRIMARY KEY,
    project_id TEXT NOT NULL,
    chunk_type TEXT NOT NULL CHECK (chunk_type IN ('reward', 'learning')),
    chunk_content TEXT NOT NULL DEFAULT '',
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (project_id, chunk_type)
);

CREATE INDEX IF NOT EXISTS project_feedback_chunks_project_id_idx
    ON project_feedback_chunks(project_id);

CREATE INDEX IF NOT EXISTS project_feedback_chunks_type_idx
    ON project_feedback_chunks(chunk_type);

-- Feedback history for audit trail
CREATE TABLE IF NOT EXISTS feedback_history (
    id BIGSERIAL PRIMARY KEY,
    project_id TEXT NOT NULL,
    feedback_type TEXT NOT NULL CHECK (feedback_type IN ('reward_feedback', 'learning_edit', 'learning_reject')),
    context_data JSONB NOT NULL,
    user_feedback TEXT NOT NULL,
    chunk_before TEXT,
    chunk_after TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS feedback_history_project_id_idx
    ON feedback_history(project_id);

CREATE INDEX IF NOT EXISTS feedback_history_type_idx
    ON feedback_history(feedback_type);

CREATE INDEX IF NOT EXISTS feedback_history_created_at_idx
    ON feedback_history(created_at DESC);

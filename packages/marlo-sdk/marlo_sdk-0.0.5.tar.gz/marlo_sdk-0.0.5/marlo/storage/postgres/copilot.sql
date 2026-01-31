-- Copilot thread and message tables for persistent conversational search

CREATE TABLE IF NOT EXISTS copilot_threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    title TEXT,
    mode VARCHAR(10) NOT NULL DEFAULT 'deep' CHECK (mode IN ('quick', 'deep')),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS copilot_threads_user_project_idx
    ON copilot_threads(user_id, project_id, created_at DESC);

CREATE INDEX IF NOT EXISTS copilot_threads_project_id_idx
    ON copilot_threads(project_id);

CREATE TABLE IF NOT EXISTS copilot_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id UUID NOT NULL REFERENCES copilot_threads(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS copilot_messages_thread_idx
    ON copilot_messages(thread_id, created_at ASC);

CREATE OR REPLACE FUNCTION update_copilot_thread_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS copilot_threads_updated ON copilot_threads;
CREATE TRIGGER copilot_threads_updated
    BEFORE UPDATE ON copilot_threads
    FOR EACH ROW
    EXECUTE FUNCTION update_copilot_thread_timestamp();

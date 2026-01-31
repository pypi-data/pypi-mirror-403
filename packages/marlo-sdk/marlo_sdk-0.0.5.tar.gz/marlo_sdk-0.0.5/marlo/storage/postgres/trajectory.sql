CREATE TABLE IF NOT EXISTS trajectory_events (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT REFERENCES sessions(id) ON DELETE CASCADE,
    project_id TEXT NOT NULL,
    org_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    event JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS trajectory_events_project_id_idx
    ON trajectory_events(project_id);

CREATE UNIQUE INDEX IF NOT EXISTS trajectory_events_event_id_unique_idx
    ON trajectory_events((event->>'event_id'))
    WHERE event->>'event_id' IS NOT NULL;

-- Full-text search schema for Marlo deep search functionality
-- Adds tsvector columns and GIN indexes for efficient text search

-- Add search vector column to sessions
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- Add search vector column to session_tasks
ALTER TABLE session_tasks ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- Add search vector column to learning_objects
ALTER TABLE learning_objects ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- Create GIN indexes for fast full-text search
CREATE INDEX IF NOT EXISTS sessions_search_idx ON sessions USING gin(search_vector);
CREATE INDEX IF NOT EXISTS session_tasks_search_idx ON session_tasks USING gin(search_vector);
CREATE INDEX IF NOT EXISTS learning_objects_search_idx ON learning_objects USING gin(search_vector);

-- Function to update session search vector
CREATE OR REPLACE FUNCTION update_session_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.task, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.final_answer, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.learning, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to update session_tasks search vector
CREATE OR REPLACE FUNCTION update_session_tasks_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.task, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.final_answer, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.learning, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to update learning_objects search vector
CREATE OR REPLACE FUNCTION update_learning_objects_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.learning, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.expected_outcome, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.basis, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing triggers if they exist (to allow re-running migration)
DROP TRIGGER IF EXISTS sessions_search_update ON sessions;
DROP TRIGGER IF EXISTS session_tasks_search_update ON session_tasks;
DROP TRIGGER IF EXISTS learning_objects_search_update ON learning_objects;

-- Create triggers to auto-update search vectors on INSERT/UPDATE
CREATE TRIGGER sessions_search_update
    BEFORE INSERT OR UPDATE OF task, final_answer, learning
    ON sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_session_search_vector();

CREATE TRIGGER session_tasks_search_update
    BEFORE INSERT OR UPDATE OF task, final_answer, learning
    ON session_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_session_tasks_search_vector();

CREATE TRIGGER learning_objects_search_update
    BEFORE INSERT OR UPDATE OF learning, expected_outcome, basis
    ON learning_objects
    FOR EACH ROW
    EXECUTE FUNCTION update_learning_objects_search_vector();

-- Backfill existing data (update search vectors for existing rows)
UPDATE sessions SET search_vector =
    setweight(to_tsvector('english', COALESCE(task, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(final_answer, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(learning, '')), 'C')
WHERE search_vector IS NULL;

UPDATE session_tasks SET search_vector =
    setweight(to_tsvector('english', COALESCE(task, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(final_answer, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(learning, '')), 'C')
WHERE search_vector IS NULL;

UPDATE learning_objects SET search_vector =
    setweight(to_tsvector('english', COALESCE(learning, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(expected_outcome, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(basis, '')), 'C')
WHERE search_vector IS NULL;

-- Migration: Add session compression columns to moments table
-- These columns support the moment builder's session compression feature

-- Add source_session_id for tracking which session a moment was extracted from
ALTER TABLE moments ADD COLUMN IF NOT EXISTS source_session_id VARCHAR(256);

-- Add previous_moment_keys for backwards chaining through moment history
ALTER TABLE moments ADD COLUMN IF NOT EXISTS previous_moment_keys TEXT[] DEFAULT ARRAY[]::TEXT[];

-- Index for efficient session-based moment lookups
CREATE INDEX IF NOT EXISTS idx_moments_source_session ON moments (source_session_id) WHERE source_session_id IS NOT NULL;

-- Index for user + session combination
CREATE INDEX IF NOT EXISTS idx_moments_user_session ON moments (user_id, source_session_id) WHERE source_session_id IS NOT NULL;

-- Add last_moment_message_idx to sessions table for tracking compression progress
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS last_moment_message_idx INTEGER DEFAULT 0;

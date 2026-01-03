-- Migration: Add next_run_time column to claude_tasks table
-- Date: 2025-12-30
-- Purpose: Enable database-based scheduling without Celery

-- Add next_run_time column (nullable, indexed for efficient polling)
ALTER TABLE claude_tasks ADD COLUMN IF NOT EXISTS next_run_time TIMESTAMP NULL;

-- Create index for efficient polling of scheduled tasks
CREATE INDEX IF NOT EXISTS idx_claude_tasks_next_run_time ON claude_tasks(next_run_time);

-- Update existing scheduled tasks to have a next_run_time
-- (This needs to be done manually or via Python script since cron parsing is complex)
-- For now, existing scheduled tasks will need to be recreated or manually updated

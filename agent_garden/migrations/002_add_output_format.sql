-- Migration: Add output_format column to claude_tasks table
-- Date: 2026-01-03
-- Purpose: Support CSV/XLSX output formats for Claude-generated reports

-- Add output_format column with default 'md' (markdown)
ALTER TABLE claude_tasks
ADD COLUMN output_format VARCHAR(10) DEFAULT 'md';

-- Supported values: 'md', 'csv', 'xlsx', 'json', 'multi'
-- 'multi' means generate multiple formats (md + csv + xlsx)

-- Update existing rows to have 'md' format
UPDATE claude_tasks
SET output_format = 'md'
WHERE output_format IS NULL;

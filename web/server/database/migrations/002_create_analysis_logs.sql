-- Migration: Create analysis_logs table to track AI generation usage
-- Date: 2025-11-09

CREATE TABLE IF NOT EXISTS analysis_logs (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  diagnosis TEXT,
  procedure TEXT,
  medication TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_analysis_logs_user_id ON analysis_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_logs_created_at ON analysis_logs(created_at);

-- Verify table creation
SELECT COUNT(*) as total_logs FROM analysis_logs;

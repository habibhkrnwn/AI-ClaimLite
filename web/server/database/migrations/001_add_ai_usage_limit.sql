-- Migration: Add AI usage limit tracking to users table
-- Date: 2025-11-11

-- Add AI usage limit columns
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS daily_ai_limit INTEGER DEFAULT 100,
ADD COLUMN IF NOT EXISTS ai_usage_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS ai_usage_date DATE DEFAULT CURRENT_DATE;

-- Add comment to columns
COMMENT ON COLUMN users.daily_ai_limit IS 'Maximum AI analysis requests allowed per day';
COMMENT ON COLUMN users.ai_usage_count IS 'Current AI usage count for today';
COMMENT ON COLUMN users.ai_usage_date IS 'Date of current usage count (resets daily)';

-- Create index for faster limit checking
CREATE INDEX IF NOT EXISTS idx_users_ai_usage ON users(ai_usage_date, ai_usage_count);

-- Create AI usage history table for detailed tracking
CREATE TABLE IF NOT EXISTS ai_usage_history (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  usage_date DATE NOT NULL DEFAULT CURRENT_DATE,
  request_count INTEGER DEFAULT 0,
  last_request_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create unique constraint on user_id and usage_date
CREATE UNIQUE INDEX IF NOT EXISTS idx_ai_usage_history_user_date 
ON ai_usage_history(user_id, usage_date);

-- Create trigger to update ai_usage_history updated_at
CREATE TRIGGER update_ai_usage_history_updated_at 
  BEFORE UPDATE ON ai_usage_history 
  FOR EACH ROW 
  EXECUTE FUNCTION update_updated_at_column();

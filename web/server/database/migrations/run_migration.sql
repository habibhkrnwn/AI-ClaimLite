-- Check if columns already exist
SELECT 
    column_name, 
    data_type, 
    column_default
FROM information_schema.columns
WHERE table_name = 'users' 
  AND column_name IN ('daily_ai_limit', 'ai_usage_count', 'ai_usage_date')
ORDER BY column_name;

-- Run migration if columns don't exist
\i 001_add_ai_usage_limit.sql

-- Verify columns were added
SELECT 
    column_name, 
    data_type, 
    column_default
FROM information_schema.columns
WHERE table_name = 'users' 
  AND column_name IN ('daily_ai_limit', 'ai_usage_count', 'ai_usage_date')
ORDER BY column_name;

-- Check current data
SELECT id, email, role, daily_ai_limit, ai_usage_count, ai_usage_date 
FROM users 
ORDER BY id;

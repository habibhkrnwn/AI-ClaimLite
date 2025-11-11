-- Script untuk update existing users table dengan AI limit columns
-- Jalankan ini di PostgreSQL untuk existing database

-- Check apakah kolom sudah ada
DO $$ 
BEGIN
    -- Add daily_ai_limit if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'daily_ai_limit'
    ) THEN
        ALTER TABLE users ADD COLUMN daily_ai_limit INTEGER DEFAULT 100;
        RAISE NOTICE 'Added column daily_ai_limit';
    ELSE
        RAISE NOTICE 'Column daily_ai_limit already exists';
    END IF;

    -- Add ai_usage_count if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'ai_usage_count'
    ) THEN
        ALTER TABLE users ADD COLUMN ai_usage_count INTEGER DEFAULT 0;
        RAISE NOTICE 'Added column ai_usage_count';
    ELSE
        RAISE NOTICE 'Column ai_usage_count already exists';
    END IF;

    -- Add ai_usage_date if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'ai_usage_date'
    ) THEN
        ALTER TABLE users ADD COLUMN ai_usage_date DATE DEFAULT CURRENT_DATE;
        RAISE NOTICE 'Added column ai_usage_date';
    ELSE
        RAISE NOTICE 'Column ai_usage_date already exists';
    END IF;
END $$;

-- Update existing users yang belum punya ai_usage_date
UPDATE users 
SET ai_usage_date = CURRENT_DATE 
WHERE ai_usage_date IS NULL;

-- Verify columns
SELECT 
    column_name, 
    data_type, 
    column_default,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'users' 
  AND column_name IN ('daily_ai_limit', 'ai_usage_count', 'ai_usage_date')
ORDER BY column_name;

-- Show current user data
SELECT 
    id, 
    email, 
    role,
    daily_ai_limit, 
    ai_usage_count, 
    ai_usage_date 
FROM users 
ORDER BY id;

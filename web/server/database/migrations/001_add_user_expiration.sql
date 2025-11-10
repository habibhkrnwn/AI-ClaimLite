-- Migration: Add active_until and created_by columns to users table
-- Date: 2025-11-09

-- Add active_until column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'active_until'
    ) THEN
        ALTER TABLE users ADD COLUMN active_until TIMESTAMP NULL;
        RAISE NOTICE 'Column active_until added successfully';
    ELSE
        RAISE NOTICE 'Column active_until already exists';
    END IF;
END $$;

-- Add created_by column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'created_by'
    ) THEN
        ALTER TABLE users ADD COLUMN created_by INTEGER REFERENCES users(id) ON DELETE SET NULL;
        RAISE NOTICE 'Column created_by added successfully';
    ELSE
        RAISE NOTICE 'Column created_by already exists';
    END IF;
END $$;

-- ICD-9 Smart Service - Database Index
-- Create index untuk faster exact search (case-insensitive)

-- Index untuk LOWER(name) search
CREATE INDEX IF NOT EXISTS idx_icd9cm_name_lower 
ON icd9cm_master(LOWER(name));

-- Index untuk code search (untuk validation)
CREATE INDEX IF NOT EXISTS idx_icd9cm_code 
ON icd9cm_master(code);

-- Verify indexes
SELECT 
    tablename, 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename = 'icd9cm_master';

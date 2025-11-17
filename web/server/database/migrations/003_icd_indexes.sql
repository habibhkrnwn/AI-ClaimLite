-- Performance indexes for ICD-10 and ICD-9 lookups
-- Postgres functional indexes for LOWER(name) so LIKE queries can benefit

-- ICD-10
CREATE INDEX IF NOT EXISTS idx_icd10_name_lower ON icd10_master ((LOWER(name)));
CREATE INDEX IF NOT EXISTS idx_icd10_code ON icd10_master (code);

-- ICD-9-CM
CREATE INDEX IF NOT EXISTS idx_icd9cm_name_lower ON icd9cm_master ((LOWER(name)));
CREATE INDEX IF NOT EXISTS idx_icd9cm_code ON icd9cm_master (code);

-- Quick stats (optional)
-- SELECT tablename, indexname FROM pg_indexes WHERE tablename IN ('icd10_master','icd9cm_master');

-- Migration: Enhance analysis_logs to store complete analysis results
-- Date: 2025-11-13

-- Add columns for storing complete analysis data
ALTER TABLE analysis_logs 
ADD COLUMN IF NOT EXISTS analysis_id VARCHAR(50) UNIQUE,
ADD COLUMN IF NOT EXISTS analysis_mode VARCHAR(20) DEFAULT 'lite',
ADD COLUMN IF NOT EXISTS input_data JSONB,
ADD COLUMN IF NOT EXISTS analysis_result JSONB,
ADD COLUMN IF NOT EXISTS icd10_code VARCHAR(20),
ADD COLUMN IF NOT EXISTS severity VARCHAR(20),
ADD COLUMN IF NOT EXISTS total_cost DECIMAL(15,2),
ADD COLUMN IF NOT EXISTS processing_time_ms INTEGER,
ADD COLUMN IF NOT EXISTS ai_calls_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'completed',
ADD COLUMN IF NOT EXISTS error_message TEXT;

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_analysis_logs_analysis_id ON analysis_logs(analysis_id);
CREATE INDEX IF NOT EXISTS idx_analysis_logs_mode ON analysis_logs(analysis_mode);
CREATE INDEX IF NOT EXISTS idx_analysis_logs_icd10 ON analysis_logs(icd10_code);
CREATE INDEX IF NOT EXISTS idx_analysis_logs_status ON analysis_logs(status);
CREATE INDEX IF NOT EXISTS idx_analysis_logs_user_created ON analysis_logs(user_id, created_at DESC);

-- Create function to search analysis logs
CREATE OR REPLACE FUNCTION search_analysis_logs(
  p_user_id INTEGER,
  p_search_text TEXT DEFAULT NULL,
  p_start_date TIMESTAMP DEFAULT NULL,
  p_end_date TIMESTAMP DEFAULT NULL,
  p_limit INTEGER DEFAULT 50,
  p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
  id INTEGER,
  analysis_id VARCHAR(50),
  user_id INTEGER,
  user_email VARCHAR(255),
  diagnosis TEXT,
  icd10_code VARCHAR(20),
  severity VARCHAR(20),
  total_cost DECIMAL(15,2),
  processing_time_ms INTEGER,
  ai_calls_count INTEGER,
  status VARCHAR(20),
  created_at TIMESTAMP
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    al.id,
    al.analysis_id,
    al.user_id,
    u.email as user_email,
    al.diagnosis,
    al.icd10_code,
    al.severity,
    al.total_cost,
    al.processing_time_ms,
    al.ai_calls_count,
    al.status,
    al.created_at
  FROM analysis_logs al
  LEFT JOIN users u ON al.user_id = u.id
  WHERE 
    (p_user_id IS NULL OR al.user_id = p_user_id)
    AND (p_search_text IS NULL OR 
         al.diagnosis ILIKE '%' || p_search_text || '%' OR
         al.procedure ILIKE '%' || p_search_text || '%' OR
         al.medication ILIKE '%' || p_search_text || '%')
    AND (p_start_date IS NULL OR al.created_at >= p_start_date)
    AND (p_end_date IS NULL OR al.created_at <= p_end_date)
  ORDER BY al.created_at DESC
  LIMIT p_limit
  OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- Create view for admin dashboard statistics
CREATE OR REPLACE VIEW analysis_statistics AS
SELECT 
  DATE(created_at) as analysis_date,
  COUNT(*) as total_analyses,
  COUNT(DISTINCT user_id) as unique_users,
  AVG(processing_time_ms) as avg_processing_time,
  SUM(ai_calls_count) as total_ai_calls,
  SUM(total_cost) as total_cost,
  COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count,
  COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_count
FROM analysis_logs
GROUP BY DATE(created_at)
ORDER BY analysis_date DESC;

-- Create view for user activity summary
CREATE OR REPLACE VIEW user_analysis_summary AS
SELECT 
  u.id as user_id,
  u.email,
  u.full_name,
  u.role,
  COUNT(al.id) as total_analyses,
  MAX(al.created_at) as last_analysis,
  AVG(al.processing_time_ms) as avg_processing_time,
  SUM(al.ai_calls_count) as total_ai_calls,
  SUM(al.total_cost) as total_cost
FROM users u
LEFT JOIN analysis_logs al ON u.id = al.user_id
GROUP BY u.id, u.email, u.full_name, u.role;

-- Add comment for documentation
COMMENT ON TABLE analysis_logs IS 'Stores complete analysis history with full results for audit and review';
COMMENT ON COLUMN analysis_logs.analysis_id IS 'Unique identifier from core_engine (e.g., LITE-20251113123456)';
COMMENT ON COLUMN analysis_logs.input_data IS 'Original input data (diagnosis, tindakan, obat) in JSON format';
COMMENT ON COLUMN analysis_logs.analysis_result IS 'Complete analysis result including ICD-10, Fornas, CP, etc. in JSON format';
COMMENT ON COLUMN analysis_logs.processing_time_ms IS 'Total processing time in milliseconds';
COMMENT ON COLUMN analysis_logs.ai_calls_count IS 'Number of AI API calls made during analysis';


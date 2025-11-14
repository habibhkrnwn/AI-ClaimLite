import { query } from '../config/database.js';

export interface AnalysisLog {
  id: number;
  user_id: number;
  analysis_id?: string;
  diagnosis: string;
  procedure: string;
  medication: string;
  analysis_mode?: string;
  input_data?: any;
  analysis_result?: any;
  icd10_code?: string;
  severity?: string;
  total_cost?: number;
  processing_time_ms?: number;
  ai_calls_count?: number;
  status?: string;
  error_message?: string;
  created_at: Date;
}

export interface AnalysisLogDetail extends AnalysisLog {
  user_email?: string;
  user_name?: string;
}

export interface UserAnalysisStats {
  user_id: number;
  email: string;
  full_name: string;
  role: string;
  total_analyses: number;
  last_analysis: Date | null;
  is_active: boolean;
  active_until: Date | null;
  avg_processing_time?: number;
  total_ai_calls?: number;
  total_cost?: number;
}

export const analysisService = {
  // Log a new analysis with complete data
  async logAnalysis(
    user_id: number, 
    diagnosis: string, 
    procedure: string, 
    medication: string,
    options?: {
      analysis_id?: string;
      analysis_mode?: string;
      input_data?: any;
      analysis_result?: any;
      icd10_code?: string;
      severity?: string;
      total_cost?: number;
      processing_time_ms?: number;
      ai_calls_count?: number;
      status?: string;
      error_message?: string;
    }
  ): Promise<AnalysisLog> {
    const result = await query(
      `INSERT INTO analysis_logs (
        user_id, diagnosis, procedure, medication,
        analysis_id, analysis_mode, input_data, analysis_result,
        icd10_code, severity, total_cost, processing_time_ms,
        ai_calls_count, status, error_message
      ) 
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15) 
       RETURNING *`,
      [
        user_id, 
        diagnosis, 
        procedure, 
        medication,
        options?.analysis_id || null,
        options?.analysis_mode || 'lite',
        options?.input_data ? JSON.stringify(options.input_data) : null,
        options?.analysis_result ? JSON.stringify(options.analysis_result) : null,
        options?.icd10_code || null,
        options?.severity || null,
        options?.total_cost || null,
        options?.processing_time_ms || null,
        options?.ai_calls_count || null,
        options?.status || 'completed',
        options?.error_message || null
      ]
    );

    return result.rows[0];
  },

  // Get analysis detail by ID
  async getAnalysisById(id: number): Promise<AnalysisLogDetail | null> {
    const result = await query(
      `SELECT 
        al.*,
        u.email as user_email,
        u.full_name as user_name
       FROM analysis_logs al
       LEFT JOIN users u ON al.user_id = u.id
       WHERE al.id = $1`,
      [id]
    );

    return result.rows[0] || null;
  },

  // Get analysis detail by analysis_id
  async getAnalysisByAnalysisId(analysis_id: string): Promise<AnalysisLogDetail | null> {
    const result = await query(
      `SELECT 
        al.*,
        u.email as user_email,
        u.full_name as user_name
       FROM analysis_logs al
       LEFT JOIN users u ON al.user_id = u.id
       WHERE al.analysis_id = $1`,
      [analysis_id]
    );

    return result.rows[0] || null;
  },

  // Get all analysis logs for a specific user
  async getUserAnalysisLogs(user_id: number, limit?: number): Promise<AnalysisLogDetail[]> {
    const queryText = limit
      ? `SELECT 
          al.*,
          u.email as user_email,
          u.full_name as user_name
         FROM analysis_logs al
         LEFT JOIN users u ON al.user_id = u.id
         WHERE al.user_id = $1 
         ORDER BY al.created_at DESC 
         LIMIT $2`
      : `SELECT 
          al.*,
          u.email as user_email,
          u.full_name as user_name
         FROM analysis_logs al
         LEFT JOIN users u ON al.user_id = u.id
         WHERE al.user_id = $1 
         ORDER BY al.created_at DESC`;
    
    const params = limit ? [user_id, limit] : [user_id];
    const result = await query(queryText, params);

    return result.rows;
  },

  // Search analysis logs with filters (for admin)
  async searchAnalysisLogs(filters: {
    user_id?: number;
    search_text?: string;
    start_date?: Date;
    end_date?: Date;
    limit?: number;
    offset?: number;
  }): Promise<AnalysisLogDetail[]> {
    const result = await query(
      `SELECT * FROM search_analysis_logs($1, $2, $3, $4, $5, $6)`,
      [
        filters.user_id || null,
        filters.search_text || null,
        filters.start_date || null,
        filters.end_date || null,
        filters.limit || 50,
        filters.offset || 0
      ]
    );

    return result.rows;
  },

  // Get analysis statistics per user (for Admin Meta dashboard)
  async getAnalysisStatsByUser(): Promise<UserAnalysisStats[]> {
    const result = await query(
      `SELECT 
        u.id as user_id,
        u.email,
        u.full_name,
        u.role,
        u.is_active,
        u.active_until,
        COUNT(al.id) as total_analyses,
        MAX(al.created_at) as last_analysis,
        AVG(al.processing_time_ms) as avg_processing_time,
        SUM(al.ai_calls_count) as total_ai_calls,
        SUM(al.total_cost) as total_cost
       FROM users u
       LEFT JOIN analysis_logs al ON u.id = al.user_id
       WHERE u.role = 'Admin RS'
       GROUP BY u.id, u.email, u.full_name, u.role, u.is_active, u.active_until
       ORDER BY total_analyses DESC, u.full_name ASC`
    );

    return result.rows.map(row => ({
      ...row,
      total_analyses: parseInt(row.total_analyses) || 0,
      avg_processing_time: parseFloat(row.avg_processing_time) || 0,
      total_ai_calls: parseInt(row.total_ai_calls) || 0,
      total_cost: parseFloat(row.total_cost) || 0,
    }));
  },

  // Get total analysis count for a user
  async getUserAnalysisCount(user_id: number): Promise<number> {
    const result = await query(
      'SELECT COUNT(*) as count FROM analysis_logs WHERE user_id = $1',
      [user_id]
    );

    return parseInt(result.rows[0].count);
  },

  // Get analysis statistics for date range
  async getAnalysisStatsByDateRange(start_date: Date, end_date: Date): Promise<UserAnalysisStats[]> {
    const result = await query(
      `SELECT 
        u.id as user_id,
        u.email,
        u.full_name,
        u.role,
        u.is_active,
        u.active_until,
        COUNT(al.id) as total_analyses,
        MAX(al.created_at) as last_analysis,
        AVG(al.processing_time_ms) as avg_processing_time,
        SUM(al.ai_calls_count) as total_ai_calls,
        SUM(al.total_cost) as total_cost
       FROM users u
       LEFT JOIN analysis_logs al ON u.id = al.user_id 
         AND al.created_at BETWEEN $1 AND $2
       WHERE u.role = 'Admin RS'
       GROUP BY u.id, u.email, u.full_name, u.role, u.is_active, u.active_until
       ORDER BY total_analyses DESC, u.full_name ASC`,
      [start_date, end_date]
    );

    return result.rows.map(row => ({
      ...row,
      total_analyses: parseInt(row.total_analyses) || 0,
      avg_processing_time: parseFloat(row.avg_processing_time) || 0,
      total_ai_calls: parseInt(row.total_ai_calls) || 0,
      total_cost: parseFloat(row.total_cost) || 0,
    }));
  },

  // Get overall statistics
  async getOverallStats(): Promise<{
    total_users: number;
    active_users: number;
    total_analyses: number;
    analyses_today: number;
    analyses_this_week: number;
    analyses_this_month: number;
  }> {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);

    const monthAgo = new Date();
    monthAgo.setMonth(monthAgo.getMonth() - 1);

    const [usersResult, totalAnalysesResult, todayResult, weekResult, monthResult] = await Promise.all([
      query(`SELECT 
        COUNT(*) as total_users,
        COUNT(CASE WHEN is_active = true THEN 1 END) as active_users
        FROM users WHERE role = 'Admin RS'`),
      query('SELECT COUNT(*) as count FROM analysis_logs'),
      query('SELECT COUNT(*) as count FROM analysis_logs WHERE created_at >= $1', [today]),
      query('SELECT COUNT(*) as count FROM analysis_logs WHERE created_at >= $1', [weekAgo]),
      query('SELECT COUNT(*) as count FROM analysis_logs WHERE created_at >= $1', [monthAgo]),
    ]);

    return {
      total_users: parseInt(usersResult.rows[0].total_users),
      active_users: parseInt(usersResult.rows[0].active_users),
      total_analyses: parseInt(totalAnalysesResult.rows[0].count),
      analyses_today: parseInt(todayResult.rows[0].count),
      analyses_this_week: parseInt(weekResult.rows[0].count),
      analyses_this_month: parseInt(monthResult.rows[0].count),
    };
  },
};

export default analysisService;

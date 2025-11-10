import { query } from '../config/database.js';

export interface AnalysisLog {
  id: number;
  user_id: number;
  diagnosis: string;
  procedure: string;
  medication: string;
  created_at: Date;
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
}

export const analysisService = {
  // Log a new analysis
  async logAnalysis(user_id: number, diagnosis: string, procedure: string, medication: string): Promise<AnalysisLog> {
    const result = await query(
      `INSERT INTO analysis_logs (user_id, diagnosis, procedure, medication) 
       VALUES ($1, $2, $3, $4) 
       RETURNING id, user_id, diagnosis, procedure, medication, created_at`,
      [user_id, diagnosis, procedure, medication]
    );

    return result.rows[0];
  },

  // Get all analysis logs for a specific user
  async getUserAnalysisLogs(user_id: number, limit?: number): Promise<AnalysisLog[]> {
    const queryText = limit
      ? `SELECT * FROM analysis_logs WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2`
      : `SELECT * FROM analysis_logs WHERE user_id = $1 ORDER BY created_at DESC`;
    
    const params = limit ? [user_id, limit] : [user_id];
    const result = await query(queryText, params);

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
        MAX(al.created_at) as last_analysis
       FROM users u
       LEFT JOIN analysis_logs al ON u.id = al.user_id
       WHERE u.role = 'Admin RS'
       GROUP BY u.id, u.email, u.full_name, u.role, u.is_active, u.active_until
       ORDER BY total_analyses DESC, u.full_name ASC`
    );

    return result.rows.map(row => ({
      ...row,
      total_analyses: parseInt(row.total_analyses),
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
        MAX(al.created_at) as last_analysis
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
      total_analyses: parseInt(row.total_analyses),
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

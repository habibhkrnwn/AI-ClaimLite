import bcrypt from 'bcrypt';
import { query } from '../config/database.js';

const SALT_ROUNDS = 10;

export interface CreateAdminRSData {
  email: string;
  password: string;
  full_name: string;
  tipe_rs: string;
  active_until?: Date | null;
  created_by: number;
  daily_ai_limit?: number;
}

export interface UpdateAccountStatusData {
  user_id: number;
  is_active?: boolean;
  active_until?: Date | null;
}

export interface AdminRSUser {
  id: number;
  email: string;
  full_name: string;
  tipe_rs: string;
  role: string;
  is_active: boolean;
  active_until: Date | null;
  created_at: Date;
  created_by: number | null;
  daily_ai_limit?: number;
  ai_usage_count?: number;
  ai_usage_date?: Date;
}

export const adminService = {
  // Create Admin RS account (only accessible by Admin Meta)
  async createAdminRS(data: CreateAdminRSData): Promise<AdminRSUser> {
    const { email, password, full_name, tipe_rs, active_until, created_by, daily_ai_limit = 100 } = data;

    // Check if user already exists
    const existingUser = await query(
      'SELECT id FROM users WHERE email = $1',
      [email]
    );

    if (existingUser.rows.length > 0) {
      throw new Error('Email already registered');
    }

    // Hash password
    const password_hash = await bcrypt.hash(password, SALT_ROUNDS);

    // Insert new Admin RS user with AI limit
    const result = await query(
      `INSERT INTO users (email, password_hash, full_name, tipe_rs, role, active_until, created_by, daily_ai_limit, ai_usage_count, ai_usage_date) 
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 0, CURRENT_DATE) 
       RETURNING id, email, full_name, tipe_rs, role, is_active, active_until, created_at, created_by`,
      [email, password_hash, full_name, tipe_rs, 'Admin RS', active_until, created_by, daily_ai_limit]
    );

    return result.rows[0];
  },

  // Get all Admin RS accounts
  async getAllAdminRS(): Promise<AdminRSUser[]> {
    const result = await query(
      `SELECT id, email, full_name, tipe_rs, role, is_active, active_until, created_at, created_by,
              daily_ai_limit, ai_usage_count, ai_usage_date
       FROM users 
       WHERE role = $1
       ORDER BY created_at DESC`,
      ['Admin RS']
    );

    return result.rows;
  },

  // Update account status (activate/deactivate or extend expiration)
  async updateAccountStatus(data: UpdateAccountStatusData): Promise<AdminRSUser> {
    const { user_id, is_active, active_until } = data;

    // Build dynamic update query
    const updates: string[] = [];
    const values: any[] = [];
    let paramIndex = 1;

    if (is_active !== undefined) {
      updates.push(`is_active = $${paramIndex}`);
      values.push(is_active);
      paramIndex++;
    }

    if (active_until !== undefined) {
      updates.push(`active_until = $${paramIndex}`);
      values.push(active_until);
      paramIndex++;
    }

    if (updates.length === 0) {
      throw new Error('No update fields provided');
    }

    values.push(user_id);

    const result = await query(
      `UPDATE users 
       SET ${updates.join(', ')}
       WHERE id = $${paramIndex} AND role = 'Admin RS'
       RETURNING id, email, full_name, tipe_rs, role, is_active, active_until, created_at, created_by`,
      values
    );

    if (result.rows.length === 0) {
      throw new Error('Admin RS user not found');
    }

    return result.rows[0];
  },

  // Delete Admin RS account
  async deleteAdminRS(user_id: number): Promise<void> {
    const result = await query(
      'DELETE FROM users WHERE id = $1 AND role = $2',
      [user_id, 'Admin RS']
    );

    if (result.rowCount === 0) {
      throw new Error('Admin RS user not found');
    }
  },

  // Check if account is still active based on active_until date
  async checkAccountExpiration(user_id: number): Promise<boolean> {
    const result = await query(
      `SELECT is_active, active_until 
       FROM users 
       WHERE id = $1`,
      [user_id]
    );

    if (result.rows.length === 0) {
      return false;
    }

    const user = result.rows[0];
    
    // If is_active is false, account is not active
    if (!user.is_active) {
      return false;
    }

    // If active_until is null, account never expires
    if (!user.active_until) {
      return true;
    }

    // Check if current date is before expiration
    return new Date() < new Date(user.active_until);
  },

  // Auto-deactivate expired accounts
  async deactivateExpiredAccounts(): Promise<number> {
    const result = await query(
      `UPDATE users 
       SET is_active = false 
       WHERE active_until IS NOT NULL 
       AND active_until < CURRENT_TIMESTAMP 
       AND is_active = true
       AND role = 'Admin RS'`
    );

    return result.rowCount || 0;
  },

  // Update user's daily AI limit
  async updateDailyAILimit(user_id: number, daily_ai_limit: number): Promise<void> {
    if (daily_ai_limit < 0) {
      throw new Error('Daily AI limit must be a positive number');
    }

    const result = await query(
      `UPDATE users 
       SET daily_ai_limit = $1 
       WHERE id = $2`,
      [daily_ai_limit, user_id]
    );

    if (result.rowCount === 0) {
      throw new Error('User not found');
    }
  },
};

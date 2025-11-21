import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import { query } from '../config/database.js';
import { jwtConfig } from '../config/jwt.js';

const SALT_ROUNDS = 10;

export interface User {
  id: number;
  email: string;
  full_name: string;
  tipe_rs: string;
  role: string;
  is_active: boolean;
  active_until?: Date | null;
  created_at: Date;
  daily_ai_limit?: number;
  ai_usage_count?: number;
  ai_usage_date?: Date;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
  tipe_rs: string;
  daily_ai_limit?: number;
}

export interface LoginData {
  email: string;
  password: string;
}

export const authService = {
  // Register new user
  async register(data: RegisterData): Promise<User> {
    const { email, password, full_name, tipe_rs, daily_ai_limit = 100 } = data;

    // Check if user already exists
    const existingUser = await query(
      'SELECT id FROM users WHERE email = $1',
      [email]
    );

    if (existingUser.rows.length > 0) {
      throw new Error('Email sudah terdaftar');
    }

    // Hash password
    const password_hash = await bcrypt.hash(password, SALT_ROUNDS);

    // Insert new user with AI limit
    const result = await query(
      `INSERT INTO users (email, password_hash, full_name, tipe_rs, daily_ai_limit, ai_usage_count, ai_usage_date) 
       VALUES ($1, $2, $3, $4, $5, 0, CURRENT_DATE) 
       RETURNING id, email, full_name, tipe_rs, role, is_active, created_at, daily_ai_limit, ai_usage_count, ai_usage_date`,
      [email, password_hash, full_name, tipe_rs, daily_ai_limit]
    );

    return result.rows[0];
  },

  // Login user
  async login(data: LoginData): Promise<{ user: User; accessToken: string; refreshToken: string }> {
    const { email, password } = data;

    // Get user by email
    const result = await query(
      `SELECT id, email, password_hash, full_name, tipe_rs, role, is_active, active_until 
       FROM users WHERE email = $1`,
      [email]
    );

    if (result.rows.length === 0) {
      throw new Error('Email atau password salah');
    }

    const user = result.rows[0];

    // Check if user is active
    if (!user.is_active) {
      throw new Error('Akun Anda tidak aktif');
    }

    // Check if account has expired
    if (user.active_until && new Date(user.active_until) < new Date()) {
      // Auto-deactivate expired account
      await query('UPDATE users SET is_active = false WHERE id = $1', [user.id]);
      throw new Error('Akun Anda sudah kadaluarsa');
    }

    // Verify password
    const isPasswordValid = await bcrypt.compare(password, user.password_hash);
    if (!isPasswordValid) {
      throw new Error('Email atau password salah');
    }

    // Update last login
    await query(
      'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = $1',
      [user.id]
    );

    // Generate tokens
    const accessToken = this.generateAccessToken(user);
    const refreshToken = await this.generateRefreshToken(user.id);

    // Remove password_hash from response
    delete user.password_hash;

    return { user, accessToken, refreshToken };
  },

  // Generate access token (short-lived)
  generateAccessToken(user: any): string {
    const payload = {
      userId: user.id,
      email: user.email,
      role: user.role,
    };

    return jwt.sign(payload, jwtConfig.secret, {
      expiresIn: jwtConfig.expiresIn,
    } as jwt.SignOptions);
  },

  // Generate refresh token (long-lived)
  async generateRefreshToken(userId: number): Promise<string> {
    const payload = { userId };
    const token = jwt.sign(payload, jwtConfig.secret, {
      expiresIn: jwtConfig.refreshExpiresIn,
    } as jwt.SignOptions);

    // Store refresh token in database
    const expiresAt = new Date();
    expiresAt.setDate(expiresAt.getDate() + 7); // 7 days

    await query(
      `INSERT INTO refresh_tokens (user_id, token, expires_at) 
       VALUES ($1, $2, $3)`,
      [userId, token, expiresAt]
    );

    return token;
  },

  // Verify token
  verifyToken(token: string): any {
    try {
      return jwt.verify(token, jwtConfig.secret);
    } catch (error) {
      throw new Error('Token tidak valid atau sudah kadaluarsa');
    }
  },

  // Refresh access token
  async refreshAccessToken(refreshToken: string): Promise<string> {
    // Verify refresh token
    const decoded = this.verifyToken(refreshToken);

    // Check if refresh token exists and not revoked
    const result = await query(
      `SELECT user_id FROM refresh_tokens 
       WHERE token = $1 AND revoked = false AND expires_at > CURRENT_TIMESTAMP`,
      [refreshToken]
    );

    if (result.rows.length === 0) {
      throw new Error('Refresh token tidak valid');
    }

    // Get user
    const userResult = await query(
      'SELECT id, email, role FROM users WHERE id = $1 AND is_active = true',
      [decoded.userId]
    );

    if (userResult.rows.length === 0) {
      throw new Error('User tidak ditemukan');
    }

    // Generate new access token
    return this.generateAccessToken(userResult.rows[0]);
  },

  // Logout (revoke refresh token)
  async logout(refreshToken: string): Promise<void> {
    await query(
      'UPDATE refresh_tokens SET revoked = true WHERE token = $1',
      [refreshToken]
    );
  },

  // Get user by ID
  async getUserById(userId: number): Promise<User | null> {
    const result = await query(
      `SELECT id, email, full_name, tipe_rs, role, is_active, active_until, created_at,
              daily_ai_limit, ai_usage_count, ai_usage_date
       FROM users WHERE id = $1`,
      [userId]
    );

    return result.rows.length > 0 ? result.rows[0] : null;
  },

  // Check AI usage limit (without incrementing)
  async checkAIUsageLimit(userId: number): Promise<{ allowed: boolean; remaining: number; limit: number; current: number }> {
    console.log(`[checkAIUsageLimit] Checking limit for userId: ${userId}`);
    
    // Get user's current usage with SQL date comparison
    const result = await query(
      `SELECT 
        daily_ai_limit, 
        ai_usage_count, 
        ai_usage_date,
        CASE 
          WHEN ai_usage_date = CURRENT_DATE THEN ai_usage_count 
          ELSE 0 
        END as current_count,
        (ai_usage_date = CURRENT_DATE) as is_today
       FROM users 
       WHERE id = $1`,
      [userId]
    );

    if (result.rows.length === 0) {
      throw new Error('User tidak ditemukan');
    }

    const { daily_ai_limit, ai_usage_date, current_count, is_today } = result.rows[0];

    console.log(`[checkAIUsageLimit] DB - count: ${current_count}, limit: ${daily_ai_limit}, date: ${ai_usage_date}, is_today: ${is_today}`);

    // Reset count in DB if date changed
    if (!is_today) {
      console.log(`[checkAIUsageLimit] Date changed, resetting count to 0`);
      await query(
        `UPDATE users SET ai_usage_count = 0, ai_usage_date = CURRENT_DATE WHERE id = $1`,
        [userId]
      );
    }

    // Check if limit exceeded
    const allowed = current_count < daily_ai_limit;
    
    const returnValue = {
      allowed,
      remaining: Math.max(0, daily_ai_limit - current_count),
      limit: daily_ai_limit,
      current: current_count,
    };
    
    console.log(`[checkAIUsageLimit] Returning:`, returnValue);

    return returnValue;
  },

  // Increment AI usage count (call after successful analysis)
  async incrementAIUsage(userId: number): Promise<{ used: number; remaining: number; limit: number }> {
    console.log(`[incrementAIUsage] Starting for userId: ${userId}`);
    
    // Increment usage count
    const result = await query(
      `UPDATE users 
       SET ai_usage_count = ai_usage_count + 1 
       WHERE id = $1
       RETURNING daily_ai_limit, ai_usage_count`,
      [userId]
    );

    if (result.rows.length === 0) {
      throw new Error('User tidak ditemukan');
    }

    const { daily_ai_limit, ai_usage_count } = result.rows[0];
    
    console.log(`[incrementAIUsage] After increment - count: ${ai_usage_count}, limit: ${daily_ai_limit}`);

    // Update usage history
    await query(
      `INSERT INTO ai_usage_history (user_id, usage_date, request_count, last_request_at)
       VALUES ($1, CURRENT_DATE, 1, CURRENT_TIMESTAMP)
       ON CONFLICT (user_id, usage_date) 
       DO UPDATE SET 
         request_count = ai_usage_history.request_count + 1,
         last_request_at = CURRENT_TIMESTAMP`,
      [userId]
    );

    const returnValue = {
      used: ai_usage_count,
      remaining: Math.max(0, daily_ai_limit - ai_usage_count),
      limit: daily_ai_limit,
    };
    
    console.log(`[incrementAIUsage] Returning:`, returnValue);

    return returnValue;
  },

  // Check and update AI usage (legacy - for backward compatibility)
  async checkAndIncrementAIUsage(userId: number): Promise<{ allowed: boolean; remaining: number; limit: number }> {
    // Get user's current usage
    const result = await query(
      `SELECT daily_ai_limit, ai_usage_count, ai_usage_date FROM users WHERE id = $1`,
      [userId]
    );

    if (result.rows.length === 0) {
      throw new Error('User tidak ditemukan');
    }

    const { daily_ai_limit, ai_usage_count, ai_usage_date } = result.rows[0];
    const today = new Date().toISOString().split('T')[0];
    const usageDate = ai_usage_date ? new Date(ai_usage_date).toISOString().split('T')[0] : null;

    let currentCount = ai_usage_count;

    // Reset count if date changed
    if (usageDate !== today) {
      currentCount = 0;
      await query(
        `UPDATE users SET ai_usage_count = 0, ai_usage_date = CURRENT_DATE WHERE id = $1`,
        [userId]
      );
    }

    // Check if limit exceeded
    if (currentCount >= daily_ai_limit) {
      return {
        allowed: false,
        remaining: 0,
        limit: daily_ai_limit,
      };
    }

    // Increment usage count
    await query(
      `UPDATE users SET ai_usage_count = ai_usage_count + 1 WHERE id = $1`,
      [userId]
    );

    // Update usage history
    await query(
      `INSERT INTO ai_usage_history (user_id, usage_date, request_count, last_request_at)
       VALUES ($1, CURRENT_DATE, 1, CURRENT_TIMESTAMP)
       ON CONFLICT (user_id, usage_date) 
       DO UPDATE SET 
         request_count = ai_usage_history.request_count + 1,
         last_request_at = CURRENT_TIMESTAMP`,
      [userId]
    );

    return {
      allowed: true,
      remaining: daily_ai_limit - currentCount - 1,
      limit: daily_ai_limit,
    };
  },

  // Get current AI usage status
  async getAIUsageStatus(userId: number): Promise<{ used: number; remaining: number; limit: number }> {
    console.log(`[getAIUsageStatus] Getting usage for userId: ${userId}`);
    
    const result = await query(
      `SELECT 
        daily_ai_limit, 
        ai_usage_count, 
        ai_usage_date,
        CASE 
          WHEN ai_usage_date = CURRENT_DATE THEN ai_usage_count 
          ELSE 0 
        END as current_count
       FROM users 
       WHERE id = $1`,
      [userId]
    );

    if (result.rows.length === 0) {
      throw new Error('User tidak ditemukan');
    }

    const { daily_ai_limit, ai_usage_date, current_count } = result.rows[0];

    console.log(`[getAIUsageStatus] DB values - current_count: ${current_count}, limit: ${daily_ai_limit}, date: ${ai_usage_date}`);

    const returnValue = {
      used: current_count,
      remaining: Math.max(0, daily_ai_limit - current_count),
      limit: daily_ai_limit,
    };
    
    console.log(`[getAIUsageStatus] Returning:`, returnValue);

    return returnValue;
  },
};

export default authService;

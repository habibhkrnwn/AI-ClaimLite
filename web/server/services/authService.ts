import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import { query } from '../config/database.js';
import { jwtConfig } from '../config/jwt.js';

const SALT_ROUNDS = 10;

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  active_until?: Date | null;
  created_at: Date;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export const authService = {
  // Register new user
  async register(data: RegisterData): Promise<User> {
    const { email, password, full_name } = data;

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

    // Insert new user
    const result = await query(
      `INSERT INTO users (email, password_hash, full_name) 
       VALUES ($1, $2, $3) 
       RETURNING id, email, full_name, role, is_active, created_at`,
      [email, password_hash, full_name]
    );

    return result.rows[0];
  },

  // Login user
  async login(data: LoginData): Promise<{ user: User; accessToken: string; refreshToken: string }> {
    const { email, password } = data;

    // Get user by email
    const result = await query(
      `SELECT id, email, password_hash, full_name, role, is_active, active_until 
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
      `SELECT id, email, full_name, role, is_active, active_until, created_at 
       FROM users WHERE id = $1`,
      [userId]
    );

    return result.rows.length > 0 ? result.rows[0] : null;
  },
};

export default authService;

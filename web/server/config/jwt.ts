import dotenv from 'dotenv';

dotenv.config();

export const jwtConfig = {
  secret: process.env.JWT_SECRET || 'your-secret-key-please-change-in-production',
  expiresIn: '24h',
  refreshExpiresIn: '7d',
};

export default jwtConfig;

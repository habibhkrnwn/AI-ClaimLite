import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import authRoutes from './routes/authRoutes.js';
import adminRoutes from './routes/adminRoutes.js';
import analysisRoutes from './routes/analysisRoutes.js';
import aiRoutes from './routes/aiRoutes.js';
import pool from './config/database.js';

// Load environment variables
dotenv.config();

const app = express();
const PORT = process.env.API_PORT || 3001;

// Middleware
app.use(cors({
  origin: function (origin, callback) {
    // Allow all origins including mobile browsers
    console.log('CORS Request from origin:', origin);
    callback(null, true);
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
}));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Request logging middleware
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
  next();
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ 
    success: true, 
    message: 'API Server is running',
    timestamp: new Date().toISOString()
  });
});

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/admin', adminRoutes);
app.use('/api/analysis', analysisRoutes);
app.use('/api/ai', aiRoutes);

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    message: 'Endpoint tidak ditemukan',
  });
});

// Error handler
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error('Error:', err);
  res.status(500).json({
    success: false,
    message: 'Terjadi kesalahan pada server',
    error: process.env.NODE_ENV === 'development' ? err.message : undefined,
  });
});

// Start server
export const startServer = async () => {
  try {
    // Test database connection (non-blocking)
    try {
      await pool.query('SELECT NOW()');
      console.log('✅ Connected to PostgreSQL database');
      console.log('✅ Database connection successful');
    } catch (dbError) {
      console.warn('⚠️  Database connection failed, but server will continue');
      console.warn('⚠️  Database error:', dbError);
      console.warn('⚠️  Some features may be unavailable');
    }

    const server = app.listen(PORT, () => {
      console.log(`🚀 API Server is running on port ${PORT}`);
      console.log(`📍 API URL: http://localhost:${PORT}`);
    });

    // Set timeout to 5 minutes for long-running AI analysis requests
    server.timeout = 300000; // 5 minutes (default is 120000 = 2 minutes)
    server.keepAliveTimeout = 310000; // Slightly higher than timeout
    server.headersTimeout = 320000; // Slightly higher than keepAliveTimeout
    
    console.log('⏱️  Server timeout configured: 5 minutes');
  } catch (error) {
    console.error('❌ Failed to start server:', error);
    process.exit(1);
  }
};

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM signal received: closing HTTP server');
  await pool.end();
  process.exit(0);
});

process.on('SIGINT', async () => {
  console.log('SIGINT signal received: closing HTTP server');
  await pool.end();
  process.exit(0);
});

// Auto-start server
startServer();

export default app;

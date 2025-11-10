import express, { Request, Response } from 'express';
import { authService } from '../services/authService.js';
import { authenticate, authorize } from '../middleware/authMiddleware.js';

const router = express.Router();

// Register endpoint - Disabled for public, only Admin Meta can create accounts via /api/admin/admin-rs
router.post('/register', authenticate, authorize('Admin Meta'), async (req: Request, res: Response): Promise<void> => {
  res.status(403).json({
    success: false,
    message: 'Public registration is disabled. Please contact Admin Meta to create an account.',
  });
});

// Login endpoint
router.post('/login', async (req: Request, res: Response): Promise<void> => {
  try {
    const { email, password } = req.body;

    // Validation
    if (!email || !password) {
      res.status(400).json({
        success: false,
        message: 'Email dan password harus diisi',
      });
      return;
    }

    const result = await authService.login({ email, password });

    res.json({
      success: true,
      message: 'Login berhasil',
      data: result,
    });
  } catch (error: any) {
    console.error('Login error:', error);
    res.status(401).json({
      success: false,
      message: error.message || 'Login gagal',
    });
  }
});

// Refresh token endpoint
router.post('/refresh', async (req: Request, res: Response): Promise<void> => {
  try {
    const { refreshToken } = req.body;

    if (!refreshToken) {
      res.status(400).json({
        success: false,
        message: 'Refresh token harus diisi',
      });
      return;
    }

    const accessToken = await authService.refreshAccessToken(refreshToken);

    res.json({
      success: true,
      data: { accessToken },
    });
  } catch (error: any) {
    console.error('Refresh token error:', error);
    res.status(401).json({
      success: false,
      message: error.message || 'Refresh token gagal',
    });
  }
});

// Logout endpoint
router.post('/logout', async (req: Request, res: Response): Promise<void> => {
  try {
    const { refreshToken } = req.body;

    if (refreshToken) {
      await authService.logout(refreshToken);
    }

    res.json({
      success: true,
      message: 'Logout berhasil',
    });
  } catch (error: any) {
    console.error('Logout error:', error);
    res.status(400).json({
      success: false,
      message: 'Logout gagal',
    });
  }
});

// Get current user (protected route)
router.get('/me', authenticate, async (req: Request, res: Response): Promise<void> => {
  try {
    if (!req.user) {
      res.status(401).json({
        success: false,
        message: 'Unauthorized',
      });
      return;
    }

    const user = await authService.getUserById(req.user.userId);

    if (!user) {
      res.status(404).json({
        success: false,
        message: 'User tidak ditemukan',
      });
      return;
    }

    res.json({
      success: true,
      data: user,
    });
  } catch (error: any) {
    console.error('Get user error:', error);
    res.status(500).json({
      success: false,
      message: 'Gagal mengambil data user',
    });
  }
});

export default router;

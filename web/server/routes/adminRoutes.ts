import express, { Request, Response } from 'express';
import { adminService } from '../services/adminService.js';
import { analysisService } from '../services/analysisService.js';
import { authenticate, authorize } from '../middleware/authMiddleware.js';

const router = express.Router();

// All routes require authentication and Admin Meta role
router.use(authenticate);
router.use(authorize('Admin Meta'));

// Create Admin RS account
router.post('/admin-rs', async (req: Request, res: Response): Promise<void> => {
  try {
    const { email, password, full_name, active_until, daily_ai_limit } = req.body;

    // Validation
    if (!email || !password || !full_name) {
      res.status(400).json({
        success: false,
        message: 'Email, password, and full name are required',
      });
      return;
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      res.status(400).json({
        success: false,
        message: 'Invalid email format',
      });
      return;
    }

    // Password validation
    if (password.length < 6) {
      res.status(400).json({
        success: false,
        message: 'Password must be at least 6 characters',
      });
      return;
    }

    const created_by = req.user!.userId;
    const activeUntilDate = active_until ? new Date(active_until) : null;

    const adminRS = await adminService.createAdminRS({
      email,
      password,
      full_name,
      active_until: activeUntilDate,
      created_by,
      daily_ai_limit: daily_ai_limit || 100, // Default 100
    });

    res.status(201).json({
      success: true,
      message: 'Admin RS account created successfully',
      data: adminRS,
    });
  } catch (error: any) {
    console.error('Create Admin RS error:', error);
    res.status(400).json({
      success: false,
      message: error.message || 'Failed to create Admin RS account',
    });
  }
});

// Get all Admin RS accounts
router.get('/admin-rs', async (req: Request, res: Response): Promise<void> => {
  try {
    const adminRSUsers = await adminService.getAllAdminRS();

    res.status(200).json({
      success: true,
      data: adminRSUsers,
    });
  } catch (error: any) {
    console.error('Get Admin RS list error:', error);
    res.status(500).json({
      success: false,
      message: error.message || 'Failed to get Admin RS list',
    });
  }
});

// Update Admin RS account status
router.patch('/admin-rs/:id/status', async (req: Request, res: Response): Promise<void> => {
  try {
    const user_id = parseInt(req.params.id);
    const { is_active, active_until } = req.body;

    if (isNaN(user_id)) {
      res.status(400).json({
        success: false,
        message: 'Invalid user ID',
      });
      return;
    }

    const activeUntilDate = active_until !== undefined 
      ? (active_until ? new Date(active_until) : null)
      : undefined;

    const updatedUser = await adminService.updateAccountStatus({
      user_id,
      is_active,
      active_until: activeUntilDate,
    });

    res.status(200).json({
      success: true,
      message: 'Account status updated successfully',
      data: updatedUser,
    });
  } catch (error: any) {
    console.error('Update account status error:', error);
    res.status(400).json({
      success: false,
      message: error.message || 'Failed to update account status',
    });
  }
});

// Delete Admin RS account
router.delete('/admin-rs/:id', async (req: Request, res: Response): Promise<void> => {
  try {
    const user_id = parseInt(req.params.id);

    if (isNaN(user_id)) {
      res.status(400).json({
        success: false,
        message: 'Invalid user ID',
      });
      return;
    }

    await adminService.deleteAdminRS(user_id);

    res.status(200).json({
      success: true,
      message: 'Admin RS account deleted successfully',
    });
  } catch (error: any) {
    console.error('Delete Admin RS error:', error);
    res.status(400).json({
      success: false,
      message: error.message || 'Failed to delete Admin RS account',
    });
  }
});

// Check and deactivate expired accounts (can be called manually or via cron job)
router.post('/admin-rs/check-expiration', async (req: Request, res: Response): Promise<void> => {
  try {
    const deactivatedCount = await adminService.deactivateExpiredAccounts();

    res.status(200).json({
      success: true,
      message: `${deactivatedCount} expired accounts deactivated`,
      data: { deactivated_count: deactivatedCount },
    });
  } catch (error: any) {
    console.error('Check expiration error:', error);
    res.status(500).json({
      success: false,
      message: error.message || 'Failed to check expiration',
    });
  }
});

// Get analysis statistics per user
router.get('/statistics/users', async (req: Request, res: Response): Promise<void> => {
  try {
    const stats = await analysisService.getAnalysisStatsByUser();

    res.status(200).json({
      success: true,
      data: stats,
    });
  } catch (error: any) {
    console.error('Get statistics error:', error);
    res.status(500).json({
      success: false,
      message: error.message || 'Failed to get statistics',
    });
  }
});

// Get overall statistics
router.get('/statistics/overall', async (req: Request, res: Response): Promise<void> => {
  try {
    const stats = await analysisService.getOverallStats();

    res.status(200).json({
      success: true,
      data: stats,
    });
  } catch (error: any) {
    console.error('Get overall statistics error:', error);
    res.status(500).json({
      success: false,
      message: error.message || 'Failed to get overall statistics',
    });
  }
});

// Update user's daily AI limit
router.patch('/users/:id/ai-limit', async (req: Request, res: Response): Promise<void> => {
  try {
    const user_id = parseInt(req.params.id);
    const { daily_ai_limit } = req.body;

    if (isNaN(user_id)) {
      res.status(400).json({
        success: false,
        message: 'Invalid user ID',
      });
      return;
    }

    if (daily_ai_limit === undefined || daily_ai_limit < 0) {
      res.status(400).json({
        success: false,
        message: 'Daily AI limit must be a positive number',
      });
      return;
    }

    await adminService.updateDailyAILimit(user_id, daily_ai_limit);

    res.status(200).json({
      success: true,
      message: 'Daily AI limit updated successfully',
    });
  } catch (error: any) {
    console.error('Update AI limit error:', error);
    res.status(400).json({
      success: false,
      message: error.message || 'Failed to update AI limit',
    });
  }
});

// Get analysis history logs with search/filter
router.get('/analysis-logs', async (req: Request, res: Response): Promise<void> => {
  try {
    const { 
      user_id, 
      search, 
      start_date, 
      end_date, 
      limit = '50', 
      offset = '0' 
    } = req.query;

    const filters = {
      user_id: user_id ? parseInt(user_id as string) : undefined,
      search_text: search as string,
      start_date: start_date ? new Date(start_date as string) : undefined,
      end_date: end_date ? new Date(end_date as string) : undefined,
      limit: parseInt(limit as string),
      offset: parseInt(offset as string),
    };

    const logs = await analysisService.searchAnalysisLogs(filters);

    res.status(200).json({
      success: true,
      data: logs,
      pagination: {
        limit: filters.limit,
        offset: filters.offset,
        total: logs.length,
      },
    });
  } catch (error: any) {
    console.error('Get analysis logs error:', error);
    res.status(500).json({
      success: false,
      message: error.message || 'Failed to get analysis logs',
    });
  }
});

// Get analysis log detail by ID
router.get('/analysis-logs/:id', async (req: Request, res: Response): Promise<void> => {
  try {
    const id = parseInt(req.params.id);

    if (isNaN(id)) {
      res.status(400).json({
        success: false,
        message: 'Invalid analysis log ID',
      });
      return;
    }

    const log = await analysisService.getAnalysisById(id);

    if (!log) {
      res.status(404).json({
        success: false,
        message: 'Analysis log not found',
      });
      return;
    }

    res.status(200).json({
      success: true,
      data: log,
    });
  } catch (error: any) {
    console.error('Get analysis log detail error:', error);
    res.status(500).json({
      success: false,
      message: error.message || 'Failed to get analysis log detail',
    });
  }
});

// Get analysis logs for specific user (can be used by Admin RS to see their own history)
router.get('/users/:id/analysis-logs', async (req: Request, res: Response): Promise<void> => {
  try {
    const user_id = parseInt(req.params.id);
    const { limit } = req.query;

    if (isNaN(user_id)) {
      res.status(400).json({
        success: false,
        message: 'Invalid user ID',
      });
      return;
    }

    const logs = await analysisService.getUserAnalysisLogs(
      user_id, 
      limit ? parseInt(limit as string) : undefined
    );

    res.status(200).json({
      success: true,
      data: logs,
    });
  } catch (error: any) {
    console.error('Get user analysis logs error:', error);
    res.status(500).json({
      success: false,
      message: error.message || 'Failed to get user analysis logs',
    });
  }
});

export default router;

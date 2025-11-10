import express, { Request, Response } from 'express';
import { analysisService } from '../services/analysisService.js';
import { authenticate } from '../middleware/authMiddleware.js';

const router = express.Router();

// All routes require authentication
router.use(authenticate);

// Log an analysis (called when user generates AI analysis)
router.post('/log', async (req: Request, res: Response): Promise<void> => {
  try {
    const { diagnosis, procedure, medication } = req.body;
    const user_id = req.user!.userId;

    if (!diagnosis && !procedure && !medication) {
      res.status(400).json({
        success: false,
        message: 'At least one field (diagnosis, procedure, or medication) is required',
      });
      return;
    }

    const log = await analysisService.logAnalysis(
      user_id,
      diagnosis || '',
      procedure || '',
      medication || ''
    );

    res.status(201).json({
      success: true,
      message: 'Analysis logged successfully',
      data: log,
    });
  } catch (error: any) {
    console.error('Log analysis error:', error);
    res.status(500).json({
      success: false,
      message: error.message || 'Failed to log analysis',
    });
  }
});

// Get current user's analysis logs
router.get('/my-logs', async (req: Request, res: Response): Promise<void> => {
  try {
    const user_id = req.user!.userId;
    const limit = req.query.limit ? parseInt(req.query.limit as string) : undefined;

    const logs = await analysisService.getUserAnalysisLogs(user_id, limit);

    res.status(200).json({
      success: true,
      data: logs,
    });
  } catch (error: any) {
    console.error('Get logs error:', error);
    res.status(500).json({
      success: false,
      message: error.message || 'Failed to get analysis logs',
    });
  }
});

// Get current user's total analysis count
router.get('/my-count', async (req: Request, res: Response): Promise<void> => {
  try {
    const user_id = req.user!.userId;
    const count = await analysisService.getUserAnalysisCount(user_id);

    res.status(200).json({
      success: true,
      data: { count },
    });
  } catch (error: any) {
    console.error('Get count error:', error);
    res.status(500).json({
      success: false,
      message: error.message || 'Failed to get analysis count',
    });
  }
});

export default router;

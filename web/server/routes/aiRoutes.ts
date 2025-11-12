import express, { Request, Response } from 'express';
import { authenticate } from '../middleware/authMiddleware.js';
import { authService } from '../services/authService.js';
import axios from 'axios';

const router = express.Router();

// Core engine API base URL
const CORE_ENGINE_URL = process.env.CORE_ENGINE_URL || 'http://localhost:8000';

// All routes require authentication
router.use(authenticate);

// Analyze single claim with form or text input (endpoint 1A)
router.post('/analyze', async (req: Request, res: Response): Promise<void> => {
  try {
    const { mode, diagnosis, procedure, medication, input_text } = req.body;
    const userId = req.user?.userId;

    if (!userId) {
      res.status(401).json({
        success: false,
        message: 'User not authenticated',
      });
      return;
    }

    // Check AI usage limit (without incrementing yet)
    const limitCheck = await authService.checkAIUsageLimit(userId);
    
    if (!limitCheck.allowed) {
      res.status(429).json({
        success: false,
        message: 'Daily AI usage limit exceeded',
        data: {
          used: limitCheck.current,
          remaining: limitCheck.remaining,
          limit: limitCheck.limit,
        },
      });
      return;
    }

    // Validation based on mode
    if (mode === 'text') {
      if (!input_text || input_text.trim() === '') {
        res.status(400).json({
          success: false,
          message: 'Input text is required for text mode',
        });
        return;
      }
    } else {
      // Default to form mode
      if (!diagnosis || !procedure || !medication) {
        res.status(400).json({
          success: false,
          message: 'Diagnosis, procedure, and medication are required for form mode',
        });
        return;
      }
    }

    // Prepare payload for core_engine
    const payload = mode === 'text' 
      ? {
          mode: 'text',
          input_text: input_text,
          save_history: true,
          rs_id: userId,
        }
      : {
          mode: 'form',
          diagnosis: diagnosis,
          tindakan: procedure,
          obat: medication,
          save_history: true,
          rs_id: userId,
        };

    // Call core_engine endpoint 1A
    const response = await axios.post(`${CORE_ENGINE_URL}/api/lite/analyze/single`, payload);

    if (response.data.status === 'success') {
      // Increment usage count AFTER successful analysis
      const updatedUsage = await authService.incrementAIUsage(userId);
      
      console.log(`[AI Analyze] Analysis success, updated usage:`, updatedUsage);
      
      res.status(200).json({
        success: true,
        data: response.data.result,
        usage: updatedUsage,
      });
    } else {
      res.status(400).json({
        success: false,
        message: response.data.message || 'Analysis failed',
      });
    }
  } catch (error: any) {
    console.error('AI Analysis error:', error);
    res.status(500).json({
      success: false,
      message: error.response?.data?.message || 'Failed to analyze claim',
      detail: error.message,
    });
  }
});

// Validate form input (optional preview before analysis)
router.post('/validate', async (req: Request, res: Response): Promise<void> => {
  try {
    const { diagnosis, procedure, medication } = req.body;

    // Call core_engine validate endpoint
    const response = await axios.post(`${CORE_ENGINE_URL}/api/lite/validate/form`, {
      diagnosis: diagnosis || '',
      tindakan: procedure || '',
      obat: medication || '',
    });

    res.status(200).json({
      success: true,
      data: response.data,
    });
  } catch (error: any) {
    console.error('Validation error:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to validate input',
    });
  }
});

// Get current AI usage status
router.get('/usage', async (req: Request, res: Response): Promise<void> => {
  try {
    const userId = req.user?.userId;

    if (!userId) {
      res.status(401).json({
        success: false,
        message: 'User not authenticated',
      });
      return;
    }

    const usage = await authService.getAIUsageStatus(userId);

    res.status(200).json({
      success: true,
      data: usage,
    });
  } catch (error: any) {
    console.error('Get usage status error:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get usage status',
    });
  }
});

export default router;

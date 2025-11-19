import express, { Request, Response } from 'express';
import { authenticate } from '../middleware/authMiddleware.js';
import { authService } from '../services/authService.js';
import { analysisService } from '../services/analysisService.js';
import * as icd10Service from '../services/icd10Service.js';
import axios from 'axios';

const router = express.Router();

// Core engine API base URL
const CORE_ENGINE_URL = process.env.CORE_ENGINE_URL || 'http://localhost:8000';

// All routes require authentication
router.use(authenticate);

// Analyze single claim with form or text input (endpoint 1A)
router.post('/analyze', async (req: Request, res: Response): Promise<void> => {
  try {
    const { mode, diagnosis, procedure, medication, service_type, input_text } = req.body;
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
      if (!diagnosis || !procedure || !medication || !service_type) {
        res.status(400).json({
          success: false,
          message: 'Diagnosis, procedure, medication, and service type are required for form mode',
        });
        return;
      }
    }

    // Extract additional fields
    const { icd10_code, icd9_code } = req.body;

    // Prepare payload for core_engine
    const payload = mode === 'text' 
      ? {
          mode: 'text',
          input_text: input_text,
          icd10_code: icd10_code || null,
          icd9_code: icd9_code || null,
          save_history: true,
          rs_id: userId,
        }
      : {
          mode: 'form',
          diagnosis: diagnosis,
          tindakan: procedure,
          obat: medication,
          service_type: service_type,
          icd10_code: icd10_code || null,
          icd9_code: icd9_code || null,
          save_history: true,
          rs_id: userId,
        };

    console.log('[AI Analyze] Payload with codes:', {
      mode,
      icd10_code: icd10_code || 'auto',
      icd9_code: icd9_code || 'auto',
      timestamp: new Date().toISOString()
    });

    // Call core_engine endpoint 1A with 5 minute timeout (for heavy OpenAI processing)
    const startTime = Date.now();
    console.log(`[AI Analyze] Calling core_engine at ${CORE_ENGINE_URL}/api/lite/analyze/single`);
    
    const response = await axios.post(`${CORE_ENGINE_URL}/api/lite/analyze/single`, payload, {
      timeout: 300000, // 5 minutes (increased from 3)
      headers: {
        'Content-Type': 'application/json',
      },
    });
    const processingTime = Date.now() - startTime;
    console.log(`[AI Analyze] Response received in ${processingTime}ms`);

    console.log('[AI Analyze] Core engine response status:', response.data.status);
    console.log('[AI Analyze] Core engine response keys:', Object.keys(response.data));

    // Core engine returns {status: "success", result: {...}}
    // Extract the actual result from the wrapper (backward compatible)
    const coreResponse = response.data;
    if (coreResponse.status !== 'success') {
      throw new Error(coreResponse.message || 'Core engine returned non-success status');
    }
    const result = coreResponse.result || coreResponse;
    
    // Check if result has required analysis data
    if (!result) {
      throw new Error('Core engine did not return result data');
    }
    
    if (result.klasifikasi) {
      // Increment usage count AFTER successful analysis
      const updatedUsage = await authService.incrementAIUsage(userId);
      
      console.log(`[AI Analyze] Analysis success, updated usage:`, updatedUsage);
      
      // Save complete analysis to database for history
      try {
        await analysisService.logAnalysis(
          userId,
          mode === 'text' ? input_text : diagnosis,
          mode === 'text' ? (result.klasifikasi?.tindakan?.map((t: any) => t.nama).join(', ') || '') : procedure,
          mode === 'text' ? result.klasifikasi?.obat || '' : medication,
          {
            analysis_id: result.metadata?.claim_id || `CLAIM-${Date.now()}`,
            analysis_mode: mode || 'form',
            input_data: {
              mode: mode,
              ...(mode === 'text' ? { input_text } : { diagnosis, procedure, medication }),
            },
            analysis_result: result,
            icd10_code: result.metadata?.icd10_code || null,
            severity: result.metadata?.severity || null,
            total_cost: undefined,
            processing_time_ms: processingTime,
            ai_calls_count: result.metadata?.ai_calls || 4,
            status: 'completed',
          }
        );
        console.log(`[AI Analyze] Saved analysis log for analysis_id: ${result.metadata?.claim_id}`);
      } catch (logError) {
        console.error('[AI Analyze] Failed to save analysis log:', logError);
        // Don't fail the request if logging fails
      }
      
      res.status(200).json({
        success: true,
        data: result,
        usage: updatedUsage,
      });
    } else {
      // Log failed analysis
      try {
        await analysisService.logAnalysis(
          userId,
          mode === 'text' ? input_text : diagnosis,
          mode === 'text' ? '' : procedure,
          mode === 'text' ? '' : medication,
          {
            analysis_mode: mode || 'form',
            input_data: {
              mode: mode,
              ...(mode === 'text' ? { input_text } : { diagnosis, procedure, medication }),
            },
            status: 'failed',
            error_message: response.data.message || 'Analysis failed',
            processing_time_ms: processingTime,
          }
        );
      } catch (logError) {
        console.error('[AI Analyze] Failed to save error log:', logError);
      }
      
      res.status(400).json({
        success: false,
        message: response.data.message || 'Analysis failed',
      });
    }
  } catch (error: any) {
    // Improved error logging for easier debugging
    const processingTime = Date.now() - (error.config?.startTime || Date.now());
    
    console.error('=== AI Analysis Error ===');
    console.error('Time elapsed:', processingTime, 'ms');
    console.error('Error name:', error.name);
    console.error('Error message:', error.message);
    console.error('Error code:', error.code);
    
    if (error.code === 'ECONNABORTED') {
      console.error('⏱️  Request timeout after', processingTime, 'ms');
      console.error('This usually means OpenAI API is slow or core_engine is processing heavy workload');
    }
    
        if (error.code === 'ECONNREFUSED') {
          console.error('🔌 Connection refused - core_engine might not be running');
          console.error('Check if Python process is running on port 8000');
        }

        if (error.response) {
          console.error('Response status:', error.response.status);
          console.error('Response data:', JSON.stringify(error.response.data, null, 2));
        } else if (error.request) {
          console.error('No response received from core_engine');
          console.error('Request config:', {
            url: error.config?.url,
            method: error.config?.method,
            timeout: error.config?.timeout,
          });
        }
        console.error('========================');

        // User-friendly error messages
        let userMessage = 'Failed to analyze claim';
        let statusCode = 500;
        let errorType = 'internal_error';
    
        if (error.code === 'ECONNABORTED' || error.message?.includes('timeout') || error.code === 'ETIMEDOUT') {
          userMessage = 'Analisis memakan waktu terlalu lama (timeout). Ini biasanya terjadi karena:\n' +
                       '1. OpenAI API sedang lambat\n' +
                       '2. Core engine sedang memproses banyak request\n' +
                       '3. Data input terlalu kompleks\n\n' +
                       'Silakan coba lagi dalam beberapa saat.';
          statusCode = 504; // Gateway Timeout
          errorType = 'timeout';
        } else if (error.code === 'ECONNREFUSED') {
          userMessage = 'Tidak dapat terhubung ke Core Engine.\n' +
                       'Pastikan Core Engine berjalan di port 8000.';
          statusCode = 503; // Service Unavailable
          errorType = 'connection_refused';
        } else if (error.response?.status === 500) {
          userMessage = 'Core Engine mengalami error internal.\n' +
                       'Detail: ' + (error.response?.data?.message || 'Unknown error');
          statusCode = 500;
          errorType = 'core_engine_error';
        } else if (error.response?.data?.message) {
          userMessage = error.response.data.message;
          errorType = 'core_engine_error';
          statusCode = error.response.status || 500;
        }

        res.status(statusCode).json({
          success: false,
          message: userMessage,
          error_type: errorType,
          detail: error.message,
          error_code: error.code,
          processing_time_ms: processingTime,
          error_data: error.response?.data || null,
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

// Get my analysis history (for Admin RS to see their own history)
router.get('/my-history', async (req: Request, res: Response): Promise<void> => {
  try {
    const userId = req.user?.userId;

    if (!userId) {
      res.status(401).json({
        success: false,
        message: 'User not authenticated',
      });
      return;
    }

    const { 
      search, 
      start_date, 
      end_date, 
      limit = '50', 
      offset = '0' 
    } = req.query;

    const filters = {
      user_id: userId, // Always filter by current user
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
    console.error('Get my history error:', error);
    res.status(500).json({
      success: false,
      message: error.message || 'Failed to get analysis history',
    });
  }
});

// Get analysis detail by ID (only if it belongs to current user)
router.get('/my-history/:id', async (req: Request, res: Response): Promise<void> => {
  try {
    const userId = req.user?.userId;
    const id = parseInt(req.params.id);

    if (!userId) {
      res.status(401).json({
        success: false,
        message: 'User not authenticated',
      });
      return;
    }

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

    // Security: Only allow users to see their own history
    if (log.user_id !== userId) {
      res.status(403).json({
        success: false,
        message: 'Forbidden: You can only access your own analysis history',
      });
      return;
    }

    res.status(200).json({
      success: true,
      data: log,
    });
  } catch (error: any) {
    console.error('Get analysis detail error:', error);
    res.status(500).json({
      success: false,
      message: error.message || 'Failed to get analysis detail',
    });
  }
});

// Get ICD-10 hierarchy based on search term (for Smart Input Correction feature)
router.get('/icd10-hierarchy', async (req: Request, res: Response): Promise<void> => {
  try {
    const { search } = req.query;

    if (!search || typeof search !== 'string' || search.trim() === '') {
      res.status(400).json({
        success: false,
        message: 'Search term is required',
      });
      return;
    }

    // Call core_engine API for ICD-10 hierarchy
    console.log('[Express] Calling core_engine /api/lite/icd10-hierarchy with search:', search);
    const response = await axios.post(
      `${CORE_ENGINE_URL}/api/lite/icd10-hierarchy`,
      { search_term: search },
      { timeout: 30000 }
    );

    console.log('[Express] Core engine response:', response.data);

    // The core_engine returns { status: "success", data: { categories: [...] } }
    if (response.data.status === 'success' && response.data.data) {
      res.status(200).json({
        success: true,
        data: {
          search_term: search,
          categories: response.data.data.categories,
          total_categories: response.data.data.categories.length,
        },
      });
    } else {
      res.status(500).json({
        success: false,
        message: 'Failed to get ICD-10 hierarchy from core engine',
      });
    }
  } catch (error: any) {
    console.error('Get ICD-10 hierarchy error:', error);
    res.status(500).json({
      success: false,
      message: error.message || 'Failed to get ICD-10 hierarchy',
    });
  }
});

// Get ICD-10 details for specific head code
router.get('/icd10-details/:headCode', async (req: Request, res: Response): Promise<void> => {
  try {
    const { headCode } = req.params;

    if (!headCode || !/^[A-Z][0-9]{2}$/.test(headCode)) {
      res.status(400).json({
        success: false,
        message: 'Invalid head code format. Expected format: A00-Z99',
      });
      return;
    }

    const details = await icd10Service.getICD10Details(headCode);

    res.status(200).json({
      success: true,
      data: {
        head_code: headCode,
        details: details,
        total: details.length,
      },
    });
  } catch (error: any) {
    console.error('Get ICD-10 details error:', error);
    res.status(500).json({
      success: false,
      message: error.message || 'Failed to get ICD-10 details',
    });
  }
});

// Search ICD-10 codes
router.get('/icd10-search', async (req: Request, res: Response): Promise<void> => {
  try {
    const { q, limit = '50' } = req.query;

    if (!q || typeof q !== 'string' || q.trim() === '') {
      res.status(400).json({
        success: false,
        message: 'Search query (q) is required',
      });
      return;
    }

    const results = await icd10Service.searchICD10Codes(q, parseInt(limit as string));

    res.status(200).json({
      success: true,
      data: {
        query: q,
        results: results,
        total: results.length,
      },
    });
  } catch (error: any) {
    console.error('Search ICD-10 codes error:', error);
    res.status(500).json({
      success: false,
      message: error.message || 'Failed to search ICD-10 codes',
    });
  }
});

// Translate colloquial medical term to medical terminology using OpenAI
router.post('/translate-medical-term', async (req: Request, res: Response): Promise<void> => {
  try {
    const { term } = req.body;

    if (!term || typeof term !== 'string' || term.trim() === '') {
      res.status(400).json({
        success: false,
        message: 'Medical term is required',
      });
      return;
    }

    // Call core_engine API for AI translation
    const response = await axios.post(`${CORE_ENGINE_URL}/api/lite/translate-medical`, {
      term: term.trim(),
    }, {
      timeout: 30000, // 30 seconds
    });

    if (response.data.status === 'success') {
      res.status(200).json({
        success: true,
        data: {
          original: term,
          translated: response.data.result.medical_term,
          confidence: response.data.result.confidence || 'high',
        },
      });
    } else {
      res.status(500).json({
        success: false,
        message: response.data.message || 'Translation failed',
      });
    }
  } catch (error: any) {
    console.error('Medical term translation error:', error);
    res.status(500).json({
      success: false,
      message: error.message || 'Failed to translate medical term',
    });
  }
});

// Translate procedure term (e.g., "ultrason" → "ultrasonography")
router.post('/translate-procedure-term', async (req: Request, res: Response): Promise<void> => {
  try {
    const { term } = req.body;

    if (!term || typeof term !== 'string' || term.trim() === '') {
      res.status(400).json({
        success: false,
        message: 'Procedure term is required',
      });
      return;
    }

    // Call core_engine API for AI translation
    const response = await axios.post(`${CORE_ENGINE_URL}/api/lite/translate-procedure`, {
      term: term.trim(),
    }, {
      timeout: 30000, // 30 seconds
    });

    if (response.data.status === 'success') {
      res.status(200).json({
        success: true,
        data: {
          original: term,
          translated: response.data.result.medical_term,
          synonyms: response.data.result.synonyms || [response.data.result.medical_term],
          confidence: response.data.result.confidence || 'high',
        },
      });
    } else {
      res.status(500).json({
        success: false,
        message: response.data.message || 'Translation failed',
      });
    }
  } catch (error: any) {
    console.error('Procedure term translation error:', error);
    res.status(500).json({
      success: false,
      message: error.message || 'Failed to translate procedure term',
    });
  }
});

// Get ICD-9 hierarchy for procedures (Tindakan)
router.post('/icd9-hierarchy', async (req: Request, res: Response): Promise<void> => {
  try {
    const { search_term, synonyms } = req.body;

    if (!search_term || typeof search_term !== 'string' || search_term.trim() === '') {
      res.status(400).json({
        success: false,
        message: 'Search term is required',
      });
      return;
    }

    // Call core_engine API for ICD-9 hierarchy with synonyms
    const response = await axios.post(`${CORE_ENGINE_URL}/api/lite/icd9-hierarchy`, {
      search_term: search_term.trim(),
      synonyms: synonyms || []
    }, {
      timeout: 30000, // 30 seconds
    });

    if (response.data.status === 'success') {
      res.status(200).json({
        success: true,
        data: response.data.data,
      });
    } else {
      res.status(500).json({
        success: false,
        message: response.data.message || 'Failed to get ICD-9 hierarchy',
      });
    }
  } catch (error: any) {
    console.error('ICD-9 hierarchy error:', error);
    res.status(500).json({
      success: false,
      message: error.message || 'Failed to get ICD-9 hierarchy',
    });
  }
});

export default router;

# main.py - Entry point untuk AI-CLAIM Lite Application

"""
AI-CLAIM Lite - Quick Analyzer & Batch Analyzer
FastAPI Application Entry Point
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
import asyncpg

# Load environment variables
load_dotenv()

# Setup logging
os.makedirs("logs", exist_ok=True)  # Create logs dir first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Reduce verbosity from watchfiles / uvicorn internal loggers which spam "1 change detected"
# These are INFO-level by default; raise to WARNING so they don't clutter the console during normal runs.
logging.getLogger('watchfiles').setLevel(logging.WARNING)
logging.getLogger('watchfiles.main').setLevel(logging.WARNING)
logging.getLogger('uvicorn.error').setLevel(logging.WARNING)
logging.getLogger('uvicorn.access').setLevel(logging.WARNING)

# Create FastAPI app
app = FastAPI(
    title="AI-CLAIM Lite",
    description="Quick Analyzer & Batch Analyzer untuk Verifikasi Klaim BPJS",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global database pool for async operations
db_pool = None

# CORS Configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# ✅ FIXED IMPORT - Tanpa 'core_engine.' prefix
# ============================================================
from lite_endpoints import (
    endpoint_validate_form,
    endpoint_analyze_single,
    endpoint_analyze_batch,
    endpoint_parse_text,
    endpoint_get_history,
    endpoint_load_history_detail
)

# ============================================================
# 🏥 HEALTH CHECK ENDPOINT
# ============================================================
@app.get("/health")
async def health_check():
    """Health check endpoint untuk monitoring"""
    return {
        "status": "healthy",
        "service": "AI-CLAIM Lite",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("APP_ENV", "development")
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to AI-CLAIM Lite API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# ============================================================
# 📋 VALIDATION & PARSING ENDPOINTS
# ============================================================
@app.post("/api/lite/validate/form")
async def validate_form(request: Request):
    """
    Validasi input form 3 field sebelum analisis
    """
    try:
        data = await request.json()
        result = endpoint_validate_form(data)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error in validate_form: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/api/lite/parse")
async def parse_text_short(request: Request):
    """
    Parse free text menjadi struktur terpisah (short URL)
    """
    try:
        data = await request.json()
        result = endpoint_parse_text(data)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error in parse_text: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

# ============================================================
# 📋 ANALYZE ENDPOINTS
# ============================================================
@app.post("/api/lite/analyze/single")
async def analyze_single(request: Request):
    """
    Analisis klaim tunggal dengan 3 mode input:
    - text: Free text parsing
    - form: 3 field terpisah (Diagnosis, Tindakan, Obat)
    - excel: Legacy mode
    """
    try:
        data = await request.json()
        result = endpoint_analyze_single(data, db_pool=db_pool)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error in analyze_single: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/api/lite/analyze/batch")
async def analyze_batch(request: Request):
    """
    Analisis batch dari Excel import
    """
    try:
        data = await request.json()
        result = endpoint_analyze_batch(data)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error in analyze_batch: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/api/lite/parse-text")
async def parse_text(request: Request):
    """
    Parse free text menjadi struktur terpisah
    """
    try:
        data = await request.json()
        result = endpoint_parse_text(data)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error in parse_text: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

# ============================================================
# 📚 HISTORY ENDPOINTS
# ============================================================
@app.get("/api/lite/history")
async def get_history(limit: int = 10):
    """
    Get history list
    """
    try:
        result = endpoint_get_history({"limit": limit})
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error in get_history: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/api/lite/history/{history_id}")
async def get_history_detail(history_id: str):
    """
    Get history detail by ID
    """
    try:
        result = endpoint_load_history_detail({"history_id": history_id})
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error in get_history_detail: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

# ============================================================
# 🔧 CONFIGURATION ENDPOINTS
# ============================================================
@app.get("/api/lite/config")
async def get_config():
    """
    Get application configuration (non-sensitive)
    """
    try:
        from config import get_config_summary
        config = get_config_summary()
        return JSONResponse(content={
            "status": "success",
            "config": config
        })
    except Exception as e:
        logger.error(f"Error in get_config: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

# ============================================================
# � PNPK SUMMARY ENDPOINTS
# ============================================================
@app.get("/api/pnpk/diagnoses")
async def list_pnpk_diagnoses():
    """
    Get list of all available diagnoses in PNPK database
    
    Response:
    {
        "status": "success",
        "count": 25,
        "diagnoses": [
            {
                "diagnosis_name": "Pneumonia",
                "stage_count": 5
            },
            ...
        ]
    }
    """
    try:
        if not db_pool:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "message": "Database connection not available"
                }
            )
        
        from services.pnpk_summary_service import PNPKSummaryService
        service = PNPKSummaryService(db_pool)
        
        diagnoses = await service.get_all_diagnoses()
        
        return JSONResponse(content={
            "status": "success",
            "count": len(diagnoses),
            "diagnoses": diagnoses
        })
    except Exception as e:
        logger.error(f"Error in list_pnpk_diagnoses: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/api/pnpk/search")
async def search_pnpk_diagnoses(q: str, limit: int = 10):
    """
    Search diagnoses with intelligent matching
    
    Query params:
    - q: Search keyword (diagnosis name or abbreviation)
    - limit: Maximum number of results (default: 10)
    
    Response:
    {
        "status": "success",
        "query": "pneumonia",
        "count": 3,
        "results": [
            {
                "diagnosis_name": "Pneumonia",
                "stage_count": 5,
                "match_score": 1.0,
                "matched_by": "exact"
            },
            {
                "diagnosis_name": "Hospital-Acquired Pneumonia (HAP)",
                "stage_count": 4,
                "match_score": 0.85,
                "matched_by": "partial"
            },
            ...
        ]
    }
    """
    try:
        if not db_pool:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "message": "Database connection not available"
                }
            )
        
        if not q or len(q.strip()) < 2:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "Query parameter 'q' must be at least 2 characters"
                }
            )
        
        from services.pnpk_summary_service import PNPKSummaryService
        service = PNPKSummaryService(db_pool)
        
        results = await service.search_diagnoses(q, limit)
        
        return JSONResponse(content={
            "status": "success",
            "query": q,
            "count": len(results),
            "results": results
        })
    except Exception as e:
        logger.error(f"Error in search_pnpk_diagnoses: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/api/pnpk/summary")
async def get_pnpk_summary(request: Request):
    """
    Get PNPK clinical pathway summary for a diagnosis
    
    Request body:
    {
        "diagnosis": "Pneumonia",  // Can be partial name or with variations
        "auto_match": true         // Enable intelligent matching (default: true)
    }
    
    Response:
    {
        "status": "success",
        "diagnosis": "Pneumonia",
        "total_stages": 5,
        "match_info": {
            "original_input": "pneumonia berat",
            "matched_name": "Pneumonia",
            "confidence": 0.95,
            "matched_by": "partial"
        },
        "stages": [
            {
                "id": 1,
                "order": 1,
                "stage_name": "Tahap Awal (Diagnosis & Stratifikasi)",
                "description": "Diagnosis (Radiologi + klinis)..."
            },
            ...
        ]
    }
    """
    try:
        if not db_pool:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "message": "Database connection not available"
                }
            )
        
        data = await request.json()
        diagnosis = data.get("diagnosis", "").strip()
        auto_match = data.get("auto_match", True)
        
        if not diagnosis:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "Field 'diagnosis' is required"
                }
            )
        
        from services.pnpk_summary_service import PNPKSummaryService
        service = PNPKSummaryService(db_pool)
        
        summary = await service.get_pnpk_summary(diagnosis, auto_match)
        
        if not summary:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"No PNPK summary found for diagnosis: {diagnosis}",
                    "suggestion": "Try using the search endpoint to find available diagnoses"
                }
            )
        
        return JSONResponse(content={
            "status": "success",
            **summary
        })
    except Exception as e:
        logger.error(f"Error in get_pnpk_summary: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/api/pnpk/summary/{diagnosis_name}")
async def get_pnpk_summary_get(diagnosis_name: str):
    """
    Get PNPK summary via GET request (alternative to POST)
    
    Path parameter:
    - diagnosis_name: Diagnosis name (URL encoded)
    """
    try:
        if not db_pool:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "message": "Database connection not available"
                }
            )
        
        from services.pnpk_summary_service import PNPKSummaryService
        service = PNPKSummaryService(db_pool)
        
        summary = await service.get_pnpk_summary(diagnosis_name, auto_match=True)
        
        if not summary:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"No PNPK summary found for diagnosis: {diagnosis_name}"
                }
            )
        
        return JSONResponse(content={
            "status": "success",
            **summary
        })
    except Exception as e:
        logger.error(f"Error in get_pnpk_summary_get: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/api/pnpk/validate")
async def validate_diagnosis(diagnosis: str):
    """
    Validate if a diagnosis exists in PNPK database
    
    Query params:
    - diagnosis: Diagnosis name to validate
    
    Response:
    {
        "status": "success",
        "diagnosis": "pneumonia",
        "exists": true,
        "match": {
            "diagnosis_name": "Pneumonia",
            "confidence": 0.95
        }
    }
    """
    try:
        if not db_pool:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "message": "Database connection not available"
                }
            )
        
        if not diagnosis or len(diagnosis.strip()) < 2:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "Query parameter 'diagnosis' must be at least 2 characters"
                }
            )
        
        from services.pnpk_summary_service import PNPKSummaryService
        service = PNPKSummaryService(db_pool)
        
        exists = await service.validate_diagnosis_exists(diagnosis)
        match_info = await service.find_best_match(diagnosis) if exists else None
        
        return JSONResponse(content={
            "status": "success",
            "diagnosis": diagnosis,
            "exists": exists,
            "match": match_info
        })
    except Exception as e:
        logger.error(f"Error in validate_diagnosis: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/api/pnpk/cache/clear")
async def clear_pnpk_cache():
    """
    Clear PNPK cache
    
    Response:
    {
        "status": "success",
        "message": "Cache cleared successfully",
        "entries_cleared": 15
    }
    """
    try:
        if not db_pool:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "message": "Database connection not available"
                }
            )
        
        from services.pnpk_summary_service import PNPKSummaryService
        service = PNPKSummaryService(db_pool)
        
        entries_cleared = service.clear_cache()
        
        return JSONResponse(content={
            "status": "success",
            "message": "Cache cleared successfully",
            "entries_cleared": entries_cleared
        })
    except Exception as e:
        logger.error(f"Error clearing PNPK cache: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/api/pnpk/cache/stats")
async def get_pnpk_cache_stats():
    """
    Get PNPK cache statistics
    
    Response:
    {
        "status": "success",
        "cache_stats": {
            "total_entries": 20,
            "active_entries": 15,
            "expired_entries": 5,
            "cache_ttl": 3600
        }
    }
    """
    try:
        if not db_pool:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "message": "Database connection not available"
                }
            )
        
        from services.pnpk_summary_service import PNPKSummaryService
        service = PNPKSummaryService(db_pool)
        
        cache_stats = service.get_cache_stats()
        
        return JSONResponse(content={
            "status": "success",
            "cache_stats": cache_stats
        })
    except Exception as e:
        logger.error(f"Error getting PNPK cache stats: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

# ============================================================
# � ERROR HANDLERS
# ============================================================
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "status": "error",
            "message": "Endpoint not found",
            "path": str(request.url)
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": str(exc) if os.getenv("DEBUG") == "true" else "Contact administrator"
        }
    )

# ============================================================
# 🚀 STARTUP & SHUTDOWN EVENTS
# ============================================================
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    global db_pool
    
    logger.info("🚀 AI-CLAIM Lite starting up...")
    logger.info(f"Environment: {os.getenv('APP_ENV', 'development')}")
    logger.info(f"Debug mode: {os.getenv('DEBUG', 'false')}")
    
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("temp", exist_ok=True)
    
    # Test database connection (SQLAlchemy)
    try:
        from database_connection import engine
        with engine.connect() as conn:
            logger.info("✅ Database connection successful (SQLAlchemy)")
    except Exception as e:
        logger.warning(f"⚠️ Database connection failed: {e}")
        logger.warning("App will continue without database features")
    
    # Initialize asyncpg pool for PNPK service
    try:
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            # Convert SQLAlchemy URL to asyncpg format
            # postgresql://user:pass@host:port/db -> postgresql://user:pass@host:port/db
            asyncpg_url = database_url.replace("postgresql://", "postgresql://")
            
            db_pool = await asyncpg.create_pool(
                asyncpg_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info("✅ AsyncPG connection pool created for PNPK service")
    except Exception as e:
        logger.warning(f"⚠️ AsyncPG pool creation failed: {e}")
        logger.warning("PNPK features will be unavailable")
    
    logger.info("✅ AI-CLAIM Lite started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    global db_pool
    
    logger.info("🛑 AI-CLAIM Lite shutting down...")
    
    # Close asyncpg pool
    if db_pool:
        await db_pool.close()
        logger.info("✅ Database pool closed")
    
    logger.info("✅ Shutdown complete")

# ============================================================
# 🧪 DEVELOPMENT ONLY
# ============================================================
if __name__ == "__main__":
    import uvicorn
    
    # Run with uvicorn for development
    # Only watch Python files in main directory and services
    uvicorn.run(
        "main:app",
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", 8003)),
        reload=os.getenv("DEBUG", "false").lower() == "true",
        reload_dirs=[".", "services"] if os.getenv("DEBUG", "false").lower() == "true" else None,
        reload_excludes=[
            "logs",
            "temp", 
            "__pycache__",
            "venv",
            ".env",
            "*.log",
            "*.pyc",
            "*.pyo",
            "*.db",
            "*.sqlite*"
        ],
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
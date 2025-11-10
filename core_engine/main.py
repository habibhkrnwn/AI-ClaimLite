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

# Create FastAPI app
app = FastAPI(
    title="AI-CLAIM Lite",
    description="Quick Analyzer & Batch Analyzer untuk Verifikasi Klaim BPJS",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

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
        result = endpoint_analyze_single(data)
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
# 🚨 ERROR HANDLERS
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
    logger.info("🚀 AI-CLAIM Lite starting up...")
    logger.info(f"Environment: {os.getenv('APP_ENV', 'development')}")
    logger.info(f"Debug mode: {os.getenv('DEBUG', 'false')}")
    
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("temp", exist_ok=True)
    
    # Test database connection
    try:
        from database_connection import engine
        with engine.connect() as conn:
            logger.info("✅ Database connection successful")
    except Exception as e:
        logger.warning(f"⚠️ Database connection failed: {e}")
        logger.warning("App will continue without database features")
    
    logger.info("✅ AI-CLAIM Lite started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("🛑 AI-CLAIM Lite shutting down...")
    logger.info("✅ Shutdown complete")

# ============================================================
# 🧪 DEVELOPMENT ONLY
# ============================================================
if __name__ == "__main__":
    import uvicorn
    
    # Run with uvicorn for development
    uvicorn.run(
        "main:app",
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", 8003)),
        reload=os.getenv("DEBUG", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
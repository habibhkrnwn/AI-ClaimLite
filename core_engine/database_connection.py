"""
Module: database_connection

Database connection untuk core_engine agar bisa akses rules_master table.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

# Load .env for environment variables
load_dotenv()

# Read DB URL from environment (sama dengan web)
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

# Validate DATABASE_URL
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL not found in environment variables. "
        "Please check your .env file in core_engine directory."
    )

# Create engine and session factory with connection pool settings
# Fix for "SSL SYSCALL error: EOF detected"
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,          # Test connection before using
    pool_recycle=3600,            # Recycle connections after 1 hour
    pool_size=5,                  # Connection pool size
    max_overflow=10,              # Max overflow connections
    connect_args={
        "connect_timeout": 10,    # Connection timeout
        "keepalives": 1,          # Enable TCP keepalive
        "keepalives_idle": 30,    # Idle time before sending keepalive
        "keepalives_interval": 10, # Interval between keepalives
        "keepalives_count": 5,    # Max keepalive probes
    }
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# ---------------------------
# DB dependency untuk FastAPI
# ---------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------
# Get direct session (untuk rules_loader.py dan services)
# ---------------------------
@contextmanager
def get_db_session():
    """Get database session dengan context manager untuk auto-close"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

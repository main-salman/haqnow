"""Database configuration and session management."""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import structlog

logger = structlog.get_logger()

def get_database_url():
    """Get database URL with explicit dotenv loading"""
    from dotenv import load_dotenv
    load_dotenv()  # Ensure environment variables are loaded
    
    # Database URL from environment
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if not DATABASE_URL:
        # Fallback to individual components
        mysql_host = os.getenv("MYSQL_HOST", "localhost")
        mysql_port = os.getenv("MYSQL_PORT", "3306")
        mysql_user = os.getenv("MYSQL_USER", "foi_user")
        mysql_password = os.getenv("MYSQL_PASSWORD", "password")
        mysql_database = os.getenv("MYSQL_DATABASE", "foi_archive")
        
        DATABASE_URL = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"
    
    return DATABASE_URL

# Get database URL with explicit dotenv loading
DATABASE_URL = get_database_url()

# Create engine with SQLite-compatible settings
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific configuration
    engine = create_engine(
        DATABASE_URL,
        echo=os.getenv("DEBUG", "false").lower() == "true"
    )
else:
    # MySQL/PostgreSQL configuration with connection timeout
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={
            "connect_timeout": 10,  # 10 second connection timeout
            "read_timeout": 10,     # 10 second read timeout
            "write_timeout": 10     # 10 second write timeout
        },
        echo=os.getenv("DEBUG", "false").lower() == "true"
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()

def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error("Database session error", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """Initialize database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        raise 
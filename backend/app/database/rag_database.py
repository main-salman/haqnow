"""RAG-specific PostgreSQL database configuration and session management."""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import structlog

logger = structlog.get_logger()

def get_rag_database_url():
    """Get PostgreSQL RAG database URL from environment variables."""
    from dotenv import load_dotenv
    load_dotenv()  # Ensure environment variables are loaded
    
    # Try to get the full URI first
    postgres_rag_uri = os.getenv("POSTGRES_RAG_URI")
    
    if postgres_rag_uri:
        # Parse the URI to convert from postgres:// to postgresql://
        if postgres_rag_uri.startswith("postgres://"):
            postgres_rag_uri = postgres_rag_uri.replace("postgres://", "postgresql://", 1)
        return postgres_rag_uri
    
    # Fallback to individual components
    postgres_host = os.getenv("POSTGRES_RAG_HOST", "localhost")
    postgres_port = os.getenv("POSTGRES_RAG_PORT", "5432")
    postgres_user = os.getenv("POSTGRES_RAG_USER", "rag_user")
    postgres_password = os.getenv("POSTGRES_RAG_PASSWORD", "password")
    postgres_database = os.getenv("POSTGRES_RAG_DATABASE", "rag_vectors")
    
    return f"postgresql+psycopg2://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_database}"

# Get RAG database URL
RAG_DATABASE_URL = get_rag_database_url()

# Create RAG engine with PostgreSQL-specific configuration
rag_engine = create_engine(
    RAG_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={
        "connect_timeout": 10,
        "application_name": "haqnow_rag"
    },
    echo=os.getenv("DEBUG", "false").lower() == "true"
)

# Create RAG session factory
RagSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=rag_engine)

# Create RAG declarative base
RagBase = declarative_base()

def get_rag_db():
    """Dependency to get RAG database session."""
    db = RagSessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error("RAG database session error", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()

def init_rag_db():
    """Initialize RAG database tables and pgvector extension."""
    try:
        # Create pgvector extension if it doesn't exist
        with rag_engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            logger.info("pgvector extension ensured")
        
        # Create all RAG tables
        RagBase.metadata.create_all(bind=rag_engine)
        logger.info("RAG database tables created successfully")
        
    except Exception as e:
        logger.error("Failed to initialize RAG database", error=str(e))
        raise

def test_rag_db_connection():
    """Test RAG database connection."""
    try:
        with rag_engine.connect() as conn:
            result = conn.execute(text("SELECT 1;"))
            row = result.fetchone()
            if row and row[0] == 1:
                logger.info("RAG database connection test successful")
                return True
            else:
                logger.error("RAG database connection test failed")
                return False
    except Exception as e:
        logger.error("RAG database connection test failed", error=str(e))
        return False

def ensure_pgvector_extension():
    """Ensure pgvector extension is available."""
    try:
        with rag_engine.connect() as conn:
            # Check if pgvector extension exists
            result = conn.execute(text(
                "SELECT 1 FROM pg_extension WHERE extname = 'vector';"
            ))
            if result.fetchone():
                logger.info("pgvector extension is already installed")
                return True
            
            # Try to create the extension
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            logger.info("pgvector extension created successfully")
            return True
            
    except Exception as e:
        logger.error("Failed to ensure pgvector extension", error=str(e))
        return False
#!/usr/bin/env python3
"""
Migration Script: Add Semantic Search Embeddings
===============================================

This script adds semantic search capabilities by:
1. Adding an embedding column to the documents table
2. Generating embeddings for all existing approved documents
3. Enabling hybrid semantic + keyword search

Usage:
    python add_semantic_search.py
"""

import os
import sys
import json
from datetime import datetime
from sqlalchemy import create_engine, text, Column, JSON, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import structlog
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database.database import Base
from app.database.models import Document
from app.services.semantic_search_service import semantic_search_service

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

def add_embedding_column_if_not_exists(engine):
    """Add embedding column to documents table if it doesn't exist."""
    try:
        logger.info("Checking if embedding column exists...")
        
        # Check if column exists
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM information_schema.columns 
                WHERE table_name = 'documents' 
                AND column_name = 'embedding'
                AND table_schema = DATABASE()
            """))
            column_exists = result.fetchone().count > 0
            
            if column_exists:
                logger.info("Embedding column already exists")
                return True
            
            # Add the column
            logger.info("Adding embedding column to documents table...")
            conn.execute(text("""
                ALTER TABLE documents 
                ADD COLUMN embedding JSON NULL 
                COMMENT 'Semantic search embedding vector (384 dimensions)'
            """))
            conn.commit()
            
            logger.info("✅ Embedding column added successfully")
            return True
            
    except Exception as e:
        logger.error("Failed to add embedding column", error=str(e))
        return False

def get_documents_without_embeddings(session, batch_size=50):
    """Get documents that need embeddings generated."""
    try:
        # Get approved documents without embeddings
        documents = session.query(Document).filter(
            Document.status == "approved",
            Document.embedding.is_(None)
        ).limit(batch_size).all()
        
        return documents
        
    except Exception as e:
        logger.error("Failed to fetch documents", error=str(e))
        return []

def generate_embeddings_batch(session, documents):
    """Generate embeddings for a batch of documents."""
    success_count = 0
    error_count = 0
    
    for doc in documents:
        try:
            # Prepare document data
            document_dict = {
                'id': doc.id,
                'title': doc.title,
                'description': doc.description,
                'search_text': doc.search_text,
                'generated_tags': doc.generated_tags
            }
            
            # Generate embedding
            embedding = semantic_search_service.generate_document_embedding(document_dict)
            
            if embedding:
                # Update document with embedding
                doc.embedding = json.dumps(embedding)
                session.commit()
                
                success_count += 1
                logger.info("Generated embedding", 
                           doc_id=doc.id, 
                           title=doc.title[:50],
                           embedding_dimensions=len(embedding))
            else:
                error_count += 1
                logger.warning("Failed to generate embedding", 
                             doc_id=doc.id, 
                             title=doc.title[:50])
                
        except Exception as e:
            error_count += 1
            session.rollback()
            logger.error("Error generating embedding", 
                        doc_id=doc.id, 
                        error=str(e))
    
    return success_count, error_count

def main():
    """Main migration function."""
    print("🚀 Starting Semantic Search Migration...")
    print("=" * 50)
    
    try:
        # Get database URL from environment  
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            logger.error("DATABASE_URL not found in environment")
            return False
        logger.info("Connecting to database", url=database_url.split('@')[1] if '@' in database_url else "local")
        
        # Create engine and session
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Test database connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        
        logger.info("✅ Database connection successful")
        
        # Add embedding column if needed
        if not add_embedding_column_if_not_exists(engine):
            print("❌ Failed to add embedding column")
            return False
        
        # Check if semantic search service is available
        if not semantic_search_service.is_available():
            print("❌ Semantic search service not available")
            print("Make sure sentence-transformers is installed: pip install sentence-transformers")
            return False
        
        logger.info("✅ Semantic search service loaded")
        
        # Start migration
        session = SessionLocal()
        total_processed = 0
        total_success = 0
        total_errors = 0
        batch_size = 10  # Small batches to avoid memory issues
        
        print(f"\n📊 Starting embedding generation (batch size: {batch_size})...")
        
        while True:
            # Get next batch of documents
            documents = get_documents_without_embeddings(session, batch_size)
            
            if not documents:
                break
            
            print(f"\n🔄 Processing batch of {len(documents)} documents...")
            
            # Generate embeddings for this batch
            success_count, error_count = generate_embeddings_batch(session, documents)
            
            total_processed += len(documents)
            total_success += success_count
            total_errors += error_count
            
            print(f"   ✅ Success: {success_count}")
            print(f"   ❌ Errors: {error_count}")
            print(f"   📈 Total processed: {total_processed}")
        
        session.close()
        
        # Final summary
        print("\n" + "=" * 50)
        print("🎉 Semantic Search Migration Complete!")
        print("=" * 50)
        print(f"📊 Total documents processed: {total_processed}")
        print(f"✅ Successful embeddings: {total_success}")
        print(f"❌ Failed embeddings: {total_errors}")
        
        if total_success > 0:
            success_rate = (total_success / total_processed) * 100
            print(f"📈 Success rate: {success_rate:.1f}%")
        
        print(f"🕒 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if total_errors > 0:
            print(f"\n⚠️  {total_errors} documents failed to generate embeddings")
            print("   You can re-run this script to retry failed documents")
        
        return True
        
    except SQLAlchemyError as e:
        logger.error("Database error during migration", error=str(e))
        print(f"❌ Database error: {e}")
        return False
        
    except Exception as e:
        logger.error("Migration failed with unexpected error", error=str(e))
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1) 
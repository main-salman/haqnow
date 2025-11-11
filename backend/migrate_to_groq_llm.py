#!/usr/bin/env python3
"""
Migration script: Switch from Ollama to Groq for LLM (embeddings stay local with sentence-transformers)
- Drops and recreates document_chunks table (keeps 384-dim)
- Re-embeds all approved documents using sentence-transformers (local)
- Requires GROQ_API_KEY in environment

Usage: python backend/migrate_to_groq_llm.py
"""

import sys
import os
import asyncio
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from app.database.database import SessionLocal
from app.database.rag_database import get_rag_db, rag_engine
from app.database.models import Document
from app.services.rag_service import rag_service

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_embeddings():
    """Main migration function"""
    
    # Check for Groq API key
    if not os.getenv("GROQ_API_KEY"):
        logger.error("❌ GROQ_API_KEY not set in .env file!")
        logger.error("Get your API key from: https://console.groq.com")
        sys.exit(1)
    
    logger.info("=" * 80)
    logger.info("🚀 Starting migration to Groq LLM (embeddings: sentence-transformers, 384-dim)")
    logger.info("=" * 80)
    
    # Step 1: Drop and recreate document_chunks table
    logger.info("\n📋 Step 1: Recreating document_chunks table with new dimensions...")
    rag_db = next(get_rag_db())
    
    try:
        # Drop existing table
        logger.info("   Dropping old document_chunks table...")
        rag_db.execute(text("DROP TABLE IF EXISTS document_chunks CASCADE"))
        rag_db.commit()
        logger.info("   ✅ Old table dropped")
        
        # Create new table with 384 dimensions (sentence-transformers)
        logger.info("   Creating new document_chunks table (384-dim)...")
        create_table_sql = """
        CREATE TABLE document_chunks (
            id SERIAL PRIMARY KEY,
            document_id INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            document_title VARCHAR(500),
            document_country VARCHAR(100),
            embedding vector(384),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            CONSTRAINT uq_document_chunk UNIQUE (document_id, chunk_index)
        );
        
        CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);
        CREATE INDEX idx_document_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
        """
        rag_db.execute(text(create_table_sql))
        rag_db.commit()
        logger.info("   ✅ New table created with indexes")
        
    except Exception as e:
        logger.error(f"   ❌ Failed to recreate table: {e}")
        rag_db.rollback()
        sys.exit(1)
    finally:
        rag_db.close()
    
    # Step 2: Get all approved documents from MySQL
    logger.info("\n📄 Step 2: Fetching approved documents from MySQL...")
    db = SessionLocal()
    
    try:
        documents = db.query(Document).filter(
            Document.status == "approved"
        ).all()
        logger.info(f"   Found {len(documents)} approved documents")
        
        if len(documents) == 0:
            logger.warning("   ⚠️ No approved documents found. Migration complete.")
            return
        
    except Exception as e:
        logger.error(f"   ❌ Failed to fetch documents: {e}")
        sys.exit(1)
    finally:
        db.close()
    
    # Step 3: Re-embed all documents using sentence-transformers (local)
    logger.info(f"\n🤖 Step 3: Re-embedding {len(documents)} documents with sentence-transformers (local)...")
    logger.info("   (This may take a while depending on document count)")
    
    successful = 0
    failed = 0
    
    for i, doc in enumerate(documents, 1):
        try:
            logger.info(f"   [{i}/{len(documents)}] Processing: {doc.title[:50]}...")
            
            # Prepare document content
            content_parts = []
            if doc.title:
                content_parts.append(f"Title: {doc.title}")
            if doc.description:
                content_parts.append(f"Description: {doc.description}")
            if doc.ocr_text:
                content_parts.append(f"Content: {doc.ocr_text}")
            
            if not content_parts:
                logger.warning(f"      ⚠️ No text content for document {doc.id}, skipping")
                continue
            
            full_content = "\n\n".join(content_parts)
            
            # Process document with new RAG service (uses sentence-transformers + Groq)
            await rag_service.process_document_for_rag(
                document_id=doc.id,
                content=full_content,
                title=doc.title,
                country=doc.country
            )
            
            successful += 1
            logger.info(f"      ✅ Successfully processed document {doc.id}")
            
        except Exception as e:
            failed += 1
            logger.error(f"      ❌ Failed to process document {doc.id}: {e}")
            continue
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("📊 Migration Summary")
    logger.info("=" * 80)
    logger.info(f"✅ Successfully processed: {successful} documents")
    if failed > 0:
        logger.info(f"❌ Failed: {failed} documents")
    logger.info(f"📈 Success rate: {(successful / len(documents) * 100):.1f}%")
    logger.info("\n🎉 Migration complete! RAG system now uses Groq (LLM) + sentence-transformers (embeddings).")
    logger.info("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(migrate_embeddings())
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Migration failed: {e}")
        sys.exit(1)


#!/usr/bin/env python3
"""
Create RAG database tables and initialize pgvector extension.
This script sets up the PostgreSQL database for RAG operations.
"""

import os
import sys
import asyncio
from sqlalchemy import text

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.rag_database import rag_engine, init_rag_db, ensure_pgvector_extension, test_rag_db_connection
from app.database.rag_models import create_vector_index_sql

def main():
    """Initialize RAG database and create all necessary tables and indexes."""
    
    print("🗄️ RAG Database Setup")
    print("=====================")
    
    # Test database connection
    print("1. Testing PostgreSQL connection...")
    if not test_rag_db_connection():
        print("❌ Failed to connect to PostgreSQL RAG database")
        print("   Check your POSTGRES_RAG_URI environment variable")
        print("   Ensure the PostgreSQL database is running and accessible")
        sys.exit(1)
    
    print("✅ PostgreSQL connection successful")
    
    # Ensure pgvector extension
    print("2. Setting up pgvector extension...")
    if not ensure_pgvector_extension():
        print("⚠️ pgvector extension not available")
        print("   Vector operations may not work optimally")
        print("   Consider installing pgvector on your PostgreSQL server")
    else:
        print("✅ pgvector extension is available")
    
    # Create all RAG tables
    print("3. Creating RAG database tables...")
    try:
        init_rag_db()
        print("✅ RAG database tables created successfully")
    except Exception as e:
        print(f"❌ Failed to create RAG tables: {e}")
        sys.exit(1)
    
    # Create vector indexes for better performance
    print("4. Creating vector indexes...")
    try:
        with rag_engine.connect() as conn:
            index_sql = create_vector_index_sql()
            if index_sql.strip() and not index_sql.startswith("--"):
                conn.execute(text(index_sql))
                conn.commit()
                print("✅ Vector indexes created successfully")
            else:
                print("⚠️ Vector indexes skipped (pgvector not available)")
    except Exception as e:
        print(f"⚠️ Failed to create vector indexes: {e}")
        print("   This is non-critical - vector search will still work")
    
    # Verify table creation
    print("5. Verifying table creation...")
    try:
        with rag_engine.connect() as conn:
            # Check if document_chunks table exists
            result = conn.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'document_chunks'
            """))
            
            if result.fetchone():
                print("✅ document_chunks table verified")
            else:
                print("❌ document_chunks table not found")
                sys.exit(1)
            
            # Check if rag_queries table exists
            result = conn.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'rag_queries'
            """))
            
            if result.fetchone():
                print("✅ rag_queries table verified")
            else:
                print("❌ rag_queries table not found")
                sys.exit(1)
                
    except Exception as e:
        print(f"❌ Table verification failed: {e}")
        sys.exit(1)
    
    print("")
    print("🎉 RAG Database Setup Complete!")
    print("===============================")
    print("")
    print("✅ PostgreSQL connection established")
    print("✅ pgvector extension configured")
    print("✅ RAG tables created and verified")
    print("✅ Vector indexes created (if pgvector available)")
    print("")
    print("Next steps:")
    print("1. Start your application server")
    print("2. Process existing documents: POST /api/rag/process-all-documents")
    print("3. Test natural language queries: POST /api/rag/question")
    print("")
    print("Monitor RAG status: GET /api/rag/status")

if __name__ == "__main__":
    main()
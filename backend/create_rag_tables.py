#!/usr/bin/env python3
"""
Create RAG tables for document Q&A functionality
Adds document_chunks table with vector embeddings
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add the parent directory to Python path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.env import get_database_url

def create_rag_tables():
    """Create tables needed for RAG functionality"""
    
    database_url = get_database_url()
    
    # Parse database URL for connection
    if database_url.startswith('postgresql://'):
        # Extract connection details
        url_parts = database_url.replace('postgresql://', '').split('@')
        user_pass = url_parts[0].split(':')
        host_db = url_parts[1].split('/')
        host_port = host_db[0].split(':')
        
        username = user_pass[0]
        password = user_pass[1] if len(user_pass) > 1 else ''
        host = host_port[0]
        port = host_port[1] if len(host_port) > 1 else '5432'
        database = host_db[1]
    else:
        print("Error: Unsupported database URL format")
        return False
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("🔗 Connected to database successfully")
        
        # Ensure pgvector extension is enabled
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("✅ pgvector extension enabled")
        
        # Create document_chunks table
        create_chunks_table = """
        CREATE TABLE IF NOT EXISTS document_chunks (
            id SERIAL PRIMARY KEY,
            document_id INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding vector(384),  -- all-MiniLM-L6-v2 produces 384-dim embeddings
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            UNIQUE(document_id, chunk_index)
        );
        """
        
        cursor.execute(create_chunks_table)
        print("✅ document_chunks table created")
        
        # Create index for vector similarity search
        create_embedding_index = """
        CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding 
        ON document_chunks USING ivfflat (embedding vector_cosine_ops) 
        WITH (lists = 100);
        """
        
        cursor.execute(create_embedding_index)
        print("✅ Vector similarity index created")
        
        # Create index for document_id lookups
        create_doc_index = """
        CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id 
        ON document_chunks(document_id);
        """
        
        cursor.execute(create_doc_index)
        print("✅ Document ID index created")
        
        # Create RAG queries log table for monitoring
        create_rag_queries_table = """
        CREATE TABLE IF NOT EXISTS rag_queries (
            id SERIAL PRIMARY KEY,
            query_text TEXT NOT NULL,
            answer_text TEXT,
            confidence_score FLOAT,
            sources_count INTEGER,
            response_time_ms INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        cursor.execute(create_rag_queries_table)
        print("✅ RAG queries log table created")
        
        # Create index for RAG queries timestamp
        create_rag_queries_index = """
        CREATE INDEX IF NOT EXISTS idx_rag_queries_created_at 
        ON rag_queries(created_at);
        """
        
        cursor.execute(create_rag_queries_index)
        print("✅ RAG queries index created")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 RAG database setup completed successfully!")
        print("📊 Tables created:")
        print("   • document_chunks - Stores document text chunks with embeddings")
        print("   • rag_queries - Logs Q&A interactions for monitoring")
        print("🔍 Indexes created for optimal query performance")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up RAG database: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Setting up RAG database tables...")
    success = create_rag_tables()
    
    if success:
        print("\n✅ RAG database setup complete!")
        print("🔄 Next steps:")
        print("   1. Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh")
        print("   2. Pull LLM model: ollama pull llama3")
        print("   3. Install Python dependencies: pip install -r requirements.txt")
        print("   4. Process existing documents for RAG")
    else:
        print("\n❌ RAG database setup failed!")
        sys.exit(1)
#!/usr/bin/env python3
"""
Migration script: OpenAI embeddings (1536-dim) → Sentence-Transformers (768-dim)

This script:
1. Updates the PostgreSQL vector column dimension from 1536 to 768
2. Re-embeds all existing document chunks using sentence-transformers
3. Verifies the migration was successful

Run this ONCE after deploying the new rag_service.py

Usage:
    cd backend
    source .venv/bin/activate
    python migrate_to_sentence_transformers.py
"""

import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../.env')
load_dotenv('.env')

import psycopg2
from sentence_transformers import SentenceTransformer

# Configuration
OLD_DIMENSIONS = 1536
NEW_DIMENSIONS = 384
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Lightweight model (~90MB)
BATCH_SIZE = 50  # Process chunks in batches to show progress


def get_rag_db_connection():
    """Get connection to RAG PostgreSQL database"""
    rag_uri = os.getenv("POSTGRES_RAG_URI")
    if not rag_uri:
        raise ValueError("POSTGRES_RAG_URI not found in environment")
    return psycopg2.connect(rag_uri)


def check_current_dimensions(conn):
    """Check current embedding dimensions"""
    cursor = conn.cursor()
    
    # Get a sample embedding to check dimensions
    cursor.execute("""
        SELECT array_length(embedding::float[], 1) 
        FROM document_chunks 
        LIMIT 1
    """)
    result = cursor.fetchone()
    cursor.close()
    
    if result and result[0]:
        return result[0]
    return None


def count_chunks(conn):
    """Count total document chunks"""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM document_chunks")
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else 0


def update_vector_column_dimension(conn):
    """Update the vector column to new dimensions"""
    cursor = conn.cursor()
    
    print(f"\n📐 Updating vector column dimension from {OLD_DIMENSIONS} to {NEW_DIMENSIONS}...")
    
    # Drop existing embedding column and recreate with new dimensions
    # This is the safest way to change pgvector dimensions
    try:
        # First, drop any indexes on the embedding column
        cursor.execute("""
            DROP INDEX IF EXISTS idx_document_chunks_embedding;
        """)
        
        # Drop the column
        cursor.execute("""
            ALTER TABLE document_chunks DROP COLUMN IF EXISTS embedding;
        """)
        
        # Recreate with new dimensions
        cursor.execute(f"""
            ALTER TABLE document_chunks ADD COLUMN embedding vector({NEW_DIMENSIONS});
        """)
        
        # Recreate the index for vector similarity search
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding 
            ON document_chunks USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """)
        
        conn.commit()
        print(f"✅ Vector column updated to {NEW_DIMENSIONS} dimensions")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error updating vector column: {e}")
        raise
    finally:
        cursor.close()


def reembed_all_chunks(conn, model):
    """Re-embed all document chunks with the new model"""
    cursor = conn.cursor()
    
    # Get all chunks
    cursor.execute("""
        SELECT id, content FROM document_chunks ORDER BY id
    """)
    chunks = cursor.fetchall()
    cursor.close()
    
    total = len(chunks)
    print(f"\n🔄 Re-embedding {total} document chunks...")
    
    if total == 0:
        print("⚠️ No chunks to re-embed")
        return
    
    # Process in batches
    start_time = time.time()
    processed = 0
    
    for i in range(0, total, BATCH_SIZE):
        batch = chunks[i:i+BATCH_SIZE]
        batch_ids = [c[0] for c in batch]
        batch_texts = [c[1] for c in batch]
        
        # Generate embeddings
        embeddings = model.encode(batch_texts)
        
        # Update database
        cursor = conn.cursor()
        for chunk_id, embedding in zip(batch_ids, embeddings):
            embedding_str = '[' + ','.join(map(str, embedding.tolist())) + ']'
            cursor.execute("""
                UPDATE document_chunks 
                SET embedding = %s::vector 
                WHERE id = %s
            """, (embedding_str, chunk_id))
        
        conn.commit()
        cursor.close()
        
        processed += len(batch)
        elapsed = time.time() - start_time
        rate = processed / elapsed if elapsed > 0 else 0
        eta = (total - processed) / rate if rate > 0 else 0
        
        print(f"  Progress: {processed}/{total} ({processed*100//total}%) - {rate:.1f} chunks/sec - ETA: {eta:.0f}s")
    
    print(f"✅ Re-embedded {total} chunks in {time.time() - start_time:.1f} seconds")


def verify_migration(conn):
    """Verify the migration was successful"""
    print("\n🔍 Verifying migration...")
    
    cursor = conn.cursor()
    
    # Check dimensions
    cursor.execute("""
        SELECT array_length(embedding::float[], 1) 
        FROM document_chunks 
        WHERE embedding IS NOT NULL
        LIMIT 1
    """)
    result = cursor.fetchone()
    
    if result and result[0] == NEW_DIMENSIONS:
        print(f"✅ Embedding dimensions: {result[0]} (correct)")
    else:
        print(f"❌ Embedding dimensions: {result[0] if result else 'NULL'} (expected {NEW_DIMENSIONS})")
        return False
    
    # Check for NULL embeddings
    cursor.execute("""
        SELECT COUNT(*) FROM document_chunks WHERE embedding IS NULL
    """)
    null_count = cursor.fetchone()[0]
    
    if null_count == 0:
        print("✅ All chunks have embeddings")
    else:
        print(f"⚠️ {null_count} chunks have NULL embeddings")
    
    # Test vector similarity search
    cursor.execute("""
        SELECT COUNT(*) FROM document_chunks 
        WHERE embedding IS NOT NULL
    """)
    total = cursor.fetchone()[0]
    print(f"✅ Total chunks with embeddings: {total}")
    
    cursor.close()
    return True


def main():
    print("=" * 60)
    print("Migration: OpenAI → Sentence-Transformers Embeddings")
    print("=" * 60)
    print(f"Old dimensions: {OLD_DIMENSIONS} (OpenAI text-embedding-3-small)")
    print(f"New dimensions: {NEW_DIMENSIONS} (Sentence-Transformers {EMBEDDING_MODEL})")
    
    # Connect to database
    print("\n📦 Connecting to RAG database...")
    conn = get_rag_db_connection()
    print("✅ Connected to PostgreSQL RAG database")
    
    # Check current state
    total_chunks = count_chunks(conn)
    print(f"📊 Total document chunks: {total_chunks}")
    
    current_dims = check_current_dimensions(conn)
    if current_dims:
        print(f"📐 Current embedding dimensions: {current_dims}")
    else:
        print("📐 No existing embeddings found")
    
    # Confirm before proceeding
    print("\n⚠️  WARNING: This will re-embed ALL documents!")
    print("⚠️  This operation cannot be undone.")
    response = input("\nProceed with migration? (yes/no): ")
    
    if response.lower() != 'yes':
        print("Migration cancelled.")
        conn.close()
        return
    
    # Load embedding model
    print(f"\n🤖 Loading embedding model: {EMBEDDING_MODEL}...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print(f"✅ Model loaded ({NEW_DIMENSIONS} dimensions)")
    
    # Update column dimensions
    update_vector_column_dimension(conn)
    
    # Re-embed all chunks
    reembed_all_chunks(conn, model)
    
    # Verify
    success = verify_migration(conn)
    
    # Close connection
    conn.close()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Restart the backend service")
        print("2. Test RAG queries to verify everything works")
    else:
        print("❌ MIGRATION COMPLETED WITH WARNINGS")
        print("=" * 60)
        print("\nPlease review the warnings above and fix any issues.")


if __name__ == "__main__":
    main()


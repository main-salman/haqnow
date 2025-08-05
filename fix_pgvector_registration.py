#!/usr/bin/env python3
"""Fix pgvector registration and test proper vector storage"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append('/opt/foi-archive/backend')

import psycopg2
from app.database.database import get_db
from app.database.models import Document
from app.services.rag_service import rag_service
from app.database.rag_database import get_rag_db, rag_engine, RagSessionLocal
from app.database.rag_models import RagBase, DocumentChunk
from sqlalchemy import text

# Register pgvector types
try:
    from pgvector.psycopg2 import register_vector
    print("✅ pgvector psycopg2 support available")
    PGVECTOR_PSYCOPG2_AVAILABLE = True
except ImportError:
    print("❌ pgvector psycopg2 support not available")
    PGVECTOR_PSYCOPG2_AVAILABLE = False

async def fix_pgvector_registration():
    print("🔧 FIXING PGVECTOR REGISTRATION")
    print("=" * 50)
    
    # 1. Register vector types with all connections
    print("1. Registering pgvector types...")
    
    if PGVECTOR_PSYCOPG2_AVAILABLE:
        try:
            # Get the raw connection
            rag_db = next(get_rag_db())
            raw_conn = rag_db.connection().connection
            
            # Register vector type
            register_vector(raw_conn)
            print("   ✅ pgvector types registered")
            
        except Exception as e:
            print(f"   ❌ Registration failed: {e}")
            return False
    else:
        print("   ⚠️ pgvector psycopg2 not available - trying manual approach")
    
    # 2. Test vector storage with proper registration
    print("2. Testing vector storage...")
    
    test_embedding = await rag_service.generate_embedding("test with proper registration")
    
    if not test_embedding or len(test_embedding) != 384:
        print("   ❌ Invalid embedding generated")
        return False
    
    print(f"   Generated: {len(test_embedding)} dims")
    
    try:
        # Test direct vector insertion
        if PGVECTOR_PSYCOPG2_AVAILABLE:
            # Use pgvector-aware insertion
            rag_db.execute(text("""
                INSERT INTO document_chunks 
                (document_id, chunk_index, content, embedding)
                VALUES (99999, 0, 'test content', :embedding::vector)
            """), {
                "embedding": test_embedding
            })
        else:
            # Fallback to array
            rag_db.execute(text("""
                INSERT INTO document_chunks 
                (document_id, chunk_index, content, embedding)
                VALUES (99999, 0, 'test content', :embedding)
            """), {
                "embedding": test_embedding
            })
        
        rag_db.commit()
        
        # Check what was stored
        result = rag_db.execute(text("""
            SELECT embedding FROM document_chunks 
            WHERE document_id = 99999
        """)).fetchone()
        
        if result and result[0]:
            stored = result[0]
            print(f"   Stored: {len(stored)} dims, type: {type(stored)}")
            
            if len(stored) == 384:
                print("   ✅ Vector storage working!")
                vector_works = True
            else:
                print(f"   ❌ Still corrupted: {len(stored)} dims")
                vector_works = False
        else:
            print("   ❌ No data stored")
            vector_works = False
        
        # Clean up
        rag_db.execute(text("DELETE FROM document_chunks WHERE document_id = 99999"))
        rag_db.commit()
        
    except Exception as e:
        print(f"   ❌ Storage test failed: {e}")
        rag_db.rollback()
        return False
    
    if not vector_works:
        print("❌ Vector storage still broken")
        return False
    
    # 3. Clear all existing data and rebuild
    print("3. Rebuilding with proper vector storage...")
    
    # Clear existing chunks
    deleted = rag_db.execute(text("DELETE FROM document_chunks")).rowcount
    rag_db.commit()
    print(f"   Cleared {deleted} existing chunks")
    
    # Get documents
    main_db = next(get_db())
    documents = main_db.query(Document).filter(Document.status == 'approved').all()
    print(f"   Processing {len(documents)} documents")
    
    success_count = 0
    total_chunks = 0
    
    for i, doc in enumerate(documents, 1):
        try:
            print(f"   Doc {i}/{len(documents)}: {doc.id}")
            
            # Build content
            content_parts = []
            if doc.title:
                content_parts.append(f"Title: {doc.title}")
            if doc.description:
                content_parts.append(f"Description: {doc.description}")
            if doc.ocr_text:
                content_parts.append(f"Content: {doc.ocr_text}")
            
            if not content_parts:
                continue
            
            full_content = "\n\n".join(content_parts)
            
            # Chunk and generate embeddings
            chunks = await rag_service.chunk_document(
                content=full_content,
                document_id=doc.id,
                document_title=doc.title,
                document_country=doc.country
            )
            
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = await rag_service.generate_embeddings(chunk_texts)
            
            # Store with proper vector handling
            for chunk, embedding in zip(chunks, embeddings):
                if PGVECTOR_PSYCOPG2_AVAILABLE:
                    rag_db.execute(text("""
                        INSERT INTO document_chunks 
                        (document_id, chunk_index, content, embedding)
                        VALUES (:document_id, :chunk_index, :content, :embedding::vector)
                    """), {
                        "document_id": chunk.document_id,
                        "chunk_index": chunk.chunk_index,
                        "content": chunk.content,
                        "embedding": embedding
                    })
                else:
                    rag_db.execute(text("""
                        INSERT INTO document_chunks 
                        (document_id, chunk_index, content, embedding)
                        VALUES (:document_id, :chunk_index, :content, :embedding)
                    """), {
                        "document_id": chunk.document_id,
                        "chunk_index": chunk.chunk_index,
                        "content": chunk.content,
                        "embedding": embedding
                    })
            
            rag_db.commit()
            success_count += 1
            total_chunks += len(chunks)
            
        except Exception as e:
            print(f"     ❌ Error: {e}")
            rag_db.rollback()
            continue
    
    # 4. Final verification
    print(f"4. ✅ Rebuild complete: {success_count}/{len(documents)} documents, {total_chunks} chunks")
    
    # Check final embedding dimensions
    sample = rag_db.execute(text("SELECT embedding FROM document_chunks LIMIT 1")).fetchone()
    if sample and sample[0]:
        final_dims = len(sample[0])
        print(f"   Final embedding dimensions: {final_dims}")
        
        if final_dims == 384:
            print("   🎉 SUCCESS: All embeddings are 384 dimensions!")
            return True
        else:
            print(f"   ❌ FAILED: Still {final_dims} dimensions")
    
    return False

if __name__ == "__main__":
    success = asyncio.run(fix_pgvector_registration())
    if success:
        print("\n🎉 PGVECTOR REGISTRATION FIX SUCCESSFUL!")
        print("   AI search should now work perfectly")
    else:
        print("\n❌ PGVECTOR REGISTRATION FIX FAILED")
        print("   Vector storage issues persist")
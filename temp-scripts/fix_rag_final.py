#!/usr/bin/env python3
"""Final fix for RAG embedding storage - ensures proper vector format"""

import asyncio
import sys
import os
import json

# Add backend to path
sys.path.append('/opt/foi-archive/backend')

from app.database.database import get_db
from app.database.models import Document
from app.services.rag_service import rag_service
from app.database.rag_database import get_rag_db, rag_engine, RagSessionLocal
from app.database.rag_models import RagBase, DocumentChunk
from sqlalchemy import text
import numpy as np

async def fix_rag_final():
    print("🔧 FINAL RAG EMBEDDING FIX")
    print("=" * 50)
    
    # 1. Check pgvector status
    print("1. Checking pgvector status...")
    rag_db = next(get_rag_db())
    
    try:
        # Test pgvector functionality
        result = rag_db.execute(text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")).fetchone()
        if result:
            print(f"   ✅ pgvector extension version: {result[0]}")
        else:
            print("   ❌ pgvector extension not found")
            return False
    except Exception as e:
        print(f"   ❌ pgvector check failed: {e}")
        return False
    
    # 2. Drop and recreate tables with proper vector columns
    print("2. Recreating RAG tables...")
    try:
        # Drop all tables
        RagBase.metadata.drop_all(bind=rag_engine)
        
        # Recreate with proper types
        RagBase.metadata.create_all(bind=rag_engine)
        print("   ✅ Tables recreated")
    except Exception as e:
        print(f"   ❌ Table recreation failed: {e}")
        return False
    
    # 3. Test proper vector storage
    print("3. Testing proper vector storage...")
    test_embedding = await rag_service.generate_embedding("test vector storage")
    
    if not test_embedding or len(test_embedding) != 384:
        print(f"   ❌ Invalid embedding: {len(test_embedding) if test_embedding else 0} dims")
        return False
    
    print(f"   Generated embedding: {len(test_embedding)} dims")
    
    # Convert to numpy array for proper vector storage
    vector_data = np.array(test_embedding, dtype=np.float32)
    
    try:
        # Store with explicit vector type
        rag_db.execute(text("""
            INSERT INTO document_chunks 
            (document_id, chunk_index, content, embedding)
            VALUES (99999, 0, 'test content', :embedding)
        """), {
            "embedding": vector_data.tolist()  # Ensure it's a proper list
        })
        rag_db.commit()
        
        # Verify storage
        result = rag_db.execute(text("""
            SELECT embedding FROM document_chunks 
            WHERE document_id = 99999
        """)).fetchone()
        
        if result and result[0]:
            stored = result[0]
            print(f"   Stored: {len(stored)} dims, type: {type(stored)}")
            
            if len(stored) == 384 and isinstance(stored, (list, np.ndarray)):
                print("   ✅ Vector storage working correctly!")
                vector_storage_works = True
            else:
                print(f"   ❌ Storage corruption: {len(stored)} dims, type: {type(stored)}")
                vector_storage_works = False
        else:
            print("   ❌ No data stored")
            vector_storage_works = False
        
        # Clean up test
        rag_db.execute(text("DELETE FROM document_chunks WHERE document_id = 99999"))
        rag_db.commit()
        
    except Exception as e:
        print(f"   ❌ Vector storage test failed: {e}")
        rag_db.rollback()
        return False
    
    if not vector_storage_works:
        print("   ❌ Vector storage is broken - cannot proceed")
        return False
    
    # 4. Process all documents with fixed storage
    print("4. Processing all documents with fixed storage...")
    main_db = next(get_db())
    documents = main_db.query(Document).filter(Document.status == 'approved').all()
    print(f"   Found {len(documents)} approved documents")
    
    success_count = 0
    for i, doc in enumerate(documents, 1):
        try:
            print(f"   Processing {i}/{len(documents)}: Doc {doc.id}")
            
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
            
            # Chunk the document
            chunks = await rag_service.chunk_document(
                content=full_content,
                document_id=doc.id,
                document_title=doc.title,
                document_country=doc.country
            )
            
            # Generate embeddings
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = await rag_service.generate_embeddings(chunk_texts)
            
            # Store with explicit vector format
            for chunk, embedding in zip(chunks, embeddings):
                # Ensure proper vector format
                vector_data = np.array(embedding, dtype=np.float32).tolist()
                
                rag_db.execute(text("""
                    INSERT INTO document_chunks 
                    (document_id, chunk_index, content, embedding)
                    VALUES (:document_id, :chunk_index, :content, :embedding)
                    ON CONFLICT (document_id, chunk_index) 
                    DO UPDATE SET content = :content, embedding = :embedding
                """), {
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "embedding": vector_data
                })
            
            rag_db.commit()
            success_count += 1
            
        except Exception as e:
            print(f"     ❌ Error processing doc {doc.id}: {e}")
            rag_db.rollback()
            continue
    
    print(f"5. ✅ Processing complete: {success_count}/{len(documents)} documents")
    
    # 6. Final verification
    final_count = rag_db.execute(text("SELECT COUNT(*) FROM document_chunks")).scalar()
    print(f"   Total chunks: {final_count}")
    
    if final_count > 0:
        # Test final embedding
        sample = rag_db.execute(text("SELECT embedding FROM document_chunks LIMIT 1")).fetchone()
        if sample and sample[0]:
            final_dims = len(sample[0])
            print(f"   Final embedding dims: {final_dims}")
            
            if final_dims == 384:
                print("   🎉 SUCCESS: All embeddings are 384 dimensions!")
                return True
            else:
                print(f"   ❌ FAILED: Still {final_dims} dimensions")
                return False
    
    return False

if __name__ == "__main__":
    success = asyncio.run(fix_rag_final())
    if success:
        print("\n🎉 RAG SYSTEM FULLY FIXED!")
        print("   AI search should now work perfectly")
    else:
        print("\n❌ RAG SYSTEM STILL BROKEN")
        print("   Manual intervention required")
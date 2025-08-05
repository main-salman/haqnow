#!/usr/bin/env python3
"""Debug the embedding storage corruption issue"""

import asyncio
import sys
import os
import json

# Add backend to path
sys.path.append('/opt/foi-archive/backend')

from app.services.rag_service import rag_service
from app.database.rag_database import get_rag_db
from sqlalchemy import text

async def debug_storage_corruption():
    print("🔍 Debugging Embedding Storage Corruption")
    print("=" * 50)
    
    # 1. Generate test embedding
    print("1. Generating test embedding...")
    test_text = "Egypt whistleblower document test"
    embedding = await rag_service.generate_embedding(test_text)
    
    if embedding:
        print(f"   Generated: {len(embedding)} dimensions")
        print(f"   Type: {type(embedding)}")
        print(f"   First 5: {embedding[:5]}")
    else:
        print("   ❌ Failed to generate embedding")
        return
    
    # 2. Test direct storage
    print("\n2. Testing direct database storage...")
    rag_db = next(get_rag_db())
    
    # Insert directly to see what happens
    try:
        rag_db.execute(text("""
            INSERT INTO document_chunks 
            (document_id, chunk_index, content, embedding)
            VALUES (99999, 0, :content, :embedding)
        """), {
            "content": test_text,
            "embedding": embedding
        })
        rag_db.commit()
        print("   ✅ Direct storage successful")
        
        # Check what was actually stored
        result = rag_db.execute(text("""
            SELECT embedding FROM document_chunks 
            WHERE document_id = 99999 AND chunk_index = 0
        """)).fetchone()
        
        if result and result[0]:
            stored_embedding = result[0]
            print(f"   Stored: {len(stored_embedding)} dimensions")
            print(f"   Type: {type(stored_embedding)}")
            print(f"   First 5: {stored_embedding[:5]}")
            
            # Compare
            if len(stored_embedding) == len(embedding):
                print("   ✅ Dimensions match!")
            else:
                print(f"   ❌ CORRUPTION: {len(embedding)} → {len(stored_embedding)}")
                
                # Analyze the corruption
                print(f"   Original type: {type(embedding[0]) if embedding else None}")
                print(f"   Stored type: {type(stored_embedding[0]) if stored_embedding else None}")
        
        # Clean up
        rag_db.execute(text("DELETE FROM document_chunks WHERE document_id = 99999"))
        rag_db.commit()
        
    except Exception as e:
        print(f"   ❌ Storage error: {e}")
        rag_db.rollback()
    
    # 3. Test the RAG service storage method
    print("\n3. Testing RAG service storage method...")
    try:
        # Create a dummy chunk
        from app.services.rag_service import DocumentChunk
        
        chunks = [DocumentChunk(
            content=test_text,
            document_id=99998,
            document_title="Test",
            document_country="Test",
            chunk_index=0
        )]
        
        # Use RAG service to store
        await rag_service.store_document_chunks(chunks)
        
        # Check what was stored
        result = rag_db.execute(text("""
            SELECT embedding FROM document_chunks 
            WHERE document_id = 99998 AND chunk_index = 0
        """)).fetchone()
        
        if result and result[0]:
            stored_embedding = result[0]
            print(f"   RAG service stored: {len(stored_embedding)} dimensions")
            
            if len(stored_embedding) != 384:
                print("   ❌ RAG service is corrupting embeddings!")
            else:
                print("   ✅ RAG service storage works correctly")
        
        # Clean up
        rag_db.execute(text("DELETE FROM document_chunks WHERE document_id = 99998"))
        rag_db.commit()
        
    except Exception as e:
        print(f"   ❌ RAG service error: {e}")
        rag_db.rollback()

if __name__ == "__main__":
    asyncio.run(debug_storage_corruption())
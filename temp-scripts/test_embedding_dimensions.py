#!/usr/bin/env python3
"""Test embedding dimensions to understand the mismatch"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append('/opt/foi-archive/backend')

from app.services.rag_service import rag_service
from sqlalchemy import text
from app.database.rag_database import get_rag_db

async def test_embedding_dimensions():
    print("🔍 Testing Embedding Dimensions")
    print("=" * 40)
    
    # 1. Test direct embedding generation
    print("1. Testing direct embedding generation...")
    test_embedding = await rag_service.generate_embedding("test query")
    if test_embedding:
        print(f"   Direct generation: {len(test_embedding)} dimensions")
        print(f"   First 5 values: {test_embedding[:5]}")
    else:
        print("   ❌ Direct generation failed")
        return
    
    # 2. Test embedding model details
    print("\n2. Checking embedding model...")
    print(f"   Model type: {type(rag_service.embedding_model)}")
    if hasattr(rag_service.embedding_model, 'get_sentence_embedding_dimension'):
        print(f"   Model dimension: {rag_service.embedding_model.get_sentence_embedding_dimension()}")
    
    # 3. Test batch generation
    print("\n3. Testing batch generation...")
    batch_embeddings = await rag_service.generate_embeddings(["test 1", "test 2"])
    if batch_embeddings:
        print(f"   Batch count: {len(batch_embeddings)}")
        print(f"   First embedding dims: {len(batch_embeddings[0])}")
        print(f"   Second embedding dims: {len(batch_embeddings[1])}")
    else:
        print("   ❌ Batch generation failed")
    
    # 4. Check what's actually stored in database
    print("\n4. Checking stored embeddings...")
    rag_db = next(get_rag_db())
    result = rag_db.execute(text("SELECT document_id, chunk_index, array_length(embedding, 1) as dims FROM document_chunks LIMIT 3")).fetchall()
    
    if result:
        for row in result:
            print(f"   Doc {row[0]}, Chunk {row[1]}: {row[2]} dimensions")
    else:
        print("   No stored embeddings found")
    
    # 5. Test actual embedding content
    sample = rag_db.execute(text("SELECT embedding FROM document_chunks LIMIT 1")).fetchone()
    if sample and sample[0]:
        embedding = sample[0]
        print(f"\n5. Sample stored embedding analysis:")
        print(f"   Type: {type(embedding)}")
        print(f"   Length: {len(embedding)}")
        print(f"   First 5 values: {embedding[:5]}")
    else:
        print("\n5. No sample embedding found")

if __name__ == "__main__":
    asyncio.run(test_embedding_dimensions())
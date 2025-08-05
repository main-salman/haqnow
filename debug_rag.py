#!/usr/bin/env python3
"""Debug script for RAG system"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append('/opt/foi-archive/backend')

from app.services.rag_service import rag_service

async def debug_rag():
    print("🔍 Debugging RAG Service Components")
    print("=" * 50)
    
    # Check embedding model
    print(f"1. Embedding model loaded: {rag_service.embedding_model is not None}")
    if rag_service.embedding_model:
        print(f"   Model type: {type(rag_service.embedding_model)}")
    
    # Check Ollama
    try:
        models = rag_service.ollama_client.list()
        print(f"2. Ollama available: ✅ True")
        print(f"   Models: {len(models.get('models', []))}")
    except Exception as e:
        print(f"2. Ollama available: ❌ False - {e}")
    
    # Test embedding generation
    try:
        embedding = await rag_service.generate_embedding("test iran documents")
        if embedding:
            print(f"3. Embedding generation: ✅ Success (length: {len(embedding)})")
        else:
            print("3. Embedding generation: ❌ Failed (returned None)")
    except Exception as e:
        print(f"3. Embedding generation: ❌ Error: {e}")
    
    # Test vector search
    try:
        if embedding:
            chunks = await rag_service.retrieve_relevant_chunks(embedding, limit=3)
            print(f"4. Vector search: ✅ Success (found {len(chunks)} chunks)")
            for i, chunk in enumerate(chunks):
                print(f"   Chunk {i+1}: {len(chunk.content)} chars")
        else:
            print("4. Vector search: ⏭️ Skipped (no embedding)")
    except Exception as e:
        print(f"4. Vector search: ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_rag())
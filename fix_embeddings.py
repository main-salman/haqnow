#!/usr/bin/env python3
"""Fix embedding dimensions by re-processing all documents"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append('/opt/foi-archive/backend')

from app.database.database import get_db
from app.database.models import Document
from app.services.rag_service import rag_service
from app.database.rag_database import get_rag_db
from app.database.rag_models import DocumentChunk
from sqlalchemy import text

async def fix_all_embeddings():
    print("🔧 Fixing Embedding Dimensions")
    print("=" * 50)
    
    # Get database sessions
    main_db = next(get_db())
    rag_db = next(get_rag_db())
    
    # Clear existing chunks with wrong dimensions
    print("1. Clearing existing chunks with wrong dimensions...")
    deleted = rag_db.execute(text("DELETE FROM document_chunks")).rowcount
    rag_db.commit()
    print(f"   Deleted {deleted} old chunks")
    
    # Get all approved documents
    documents = main_db.query(Document).filter(Document.status == 'approved').all()
    print(f"2. Found {len(documents)} approved documents to process")
    
    # Process each document
    success_count = 0
    for i, doc in enumerate(documents, 1):
        try:
            print(f"   Processing doc {i}/{len(documents)}: {doc.id} - {doc.title[:50]}...")
            
            # Process document through RAG pipeline
            await rag_service.process_new_document(doc.id, main_db)
            success_count += 1
            
            # Check progress every 10 documents
            if i % 10 == 0:
                chunk_count = rag_db.execute(text("SELECT COUNT(*) FROM document_chunks")).scalar()
                print(f"   Progress: {i}/{len(documents)} docs, {chunk_count} chunks created")
                
        except Exception as e:
            print(f"   ❌ Error processing doc {doc.id}: {e}")
    
    # Final check
    final_count = rag_db.execute(text("SELECT COUNT(*) FROM document_chunks")).scalar()
    print(f"\n🎉 Processing Complete!")
    print(f"   Documents processed: {success_count}/{len(documents)}")
    print(f"   Total chunks created: {final_count}")
    
    # Test embeddings
    if final_count > 0:
        print("\n3. Testing new embeddings...")
        test_embedding = await rag_service.generate_embedding("test iran documents")
        if test_embedding:
            chunks = await rag_service.retrieve_relevant_chunks(test_embedding, limit=3)
            print(f"   ✅ Vector search works! Found {len(chunks)} relevant chunks")
            if chunks:
                for i, chunk in enumerate(chunks):
                    print(f"      Chunk {i+1}: Doc {chunk.document_id}, {len(chunk.content)} chars")
        else:
            print("   ❌ Embedding generation failed")
    
    main_db.close()
    rag_db.close()

if __name__ == "__main__":
    asyncio.run(fix_all_embeddings())
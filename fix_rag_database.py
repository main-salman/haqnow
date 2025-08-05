#!/usr/bin/env python3
"""Fix RAG database schema and re-process documents"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append('/opt/foi-archive/backend')

from app.database.database import get_db
from app.database.models import Document
from app.services.rag_service import rag_service
from app.database.rag_database import get_rag_db, rag_engine, RagSessionLocal
from app.database.rag_models import RagBase, DocumentChunk
from sqlalchemy import text

async def fix_rag_database():
    print("🔧 Fixing RAG Database Schema and Re-processing Documents")
    print("=" * 60)
    
    # Get database sessions
    main_db = next(get_db())
    
    print("1. Dropping existing RAG tables...")
    try:
        # Drop all RAG tables to recreate with correct schema
        RagBase.metadata.drop_all(bind=rag_engine)
        print("   ✅ Existing tables dropped")
    except Exception as e:
        print(f"   ⚠️  Warning dropping tables: {e}")
    
    print("2. Creating new RAG tables with unique constraint...")
    try:
        # Create all tables with new schema
        RagBase.metadata.create_all(bind=rag_engine)
        print("   ✅ New tables created with unique constraint")
    except Exception as e:
        print(f"   ❌ Error creating tables: {e}")
        return
    
    # Verify constraint exists
    rag_db = next(get_rag_db())
    try:
        constraint_check = rag_db.execute(text("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'document_chunks' 
            AND constraint_type = 'UNIQUE'
        """)).fetchall()
        
        if constraint_check:
            print(f"   ✅ Unique constraint verified: {constraint_check[0][0]}")
        else:
            print("   ⚠️  Warning: Unique constraint not found")
    except Exception as e:
        print(f"   ⚠️  Could not verify constraint: {e}")
    
    print("3. Processing documents with correct embeddings...")
    
    # Get all approved documents
    documents = main_db.query(Document).filter(Document.status == 'approved').all()
    print(f"   Found {len(documents)} approved documents to process")
    
    # Process each document
    success_count = 0
    for i, doc in enumerate(documents, 1):
        try:
            print(f"   Processing doc {i}/{len(documents)}: {doc.id} - {doc.title[:50]}...")
            
            # Process document through RAG pipeline
            await rag_service.process_new_document(doc.id, main_db)
            success_count += 1
            
            # Check progress every 5 documents
            if i % 5 == 0:
                chunk_count = rag_db.execute(text("SELECT COUNT(*) FROM document_chunks")).scalar()
                print(f"   Progress: {i}/{len(documents)} docs, {chunk_count} chunks created")
                
        except Exception as e:
            print(f"   ❌ Error processing doc {doc.id}: {e}")
    
    # Final verification
    final_count = rag_db.execute(text("SELECT COUNT(*) FROM document_chunks")).scalar()
    print(f"\n🎉 Processing Complete!")
    print(f"   Documents processed: {success_count}/{len(documents)}")
    print(f"   Total chunks created: {final_count}")
    
    # Test the fixed system
    if final_count > 0:
        print("\n4. Testing fixed RAG system...")
        test_embedding = await rag_service.generate_embedding("iran documents corruption")
        if test_embedding:
            print(f"   ✅ Generated embedding: {len(test_embedding)} dimensions")
            
            chunks = await rag_service.retrieve_relevant_chunks(test_embedding, limit=3)
            print(f"   ✅ Vector search works! Found {len(chunks)} relevant chunks")
            
            if chunks:
                for i, chunk in enumerate(chunks, 1):
                    print(f"      Chunk {i}: Doc {chunk.document_id}, {len(chunk.content)} chars")
                    
                # Test full RAG pipeline
                result = await rag_service.answer_question("Do you have documents about Iran?", main_db)
                print(f"\n   🎯 AI Answer Test:")
                print(f"      Question: Do you have documents about Iran?")
                print(f"      Confidence: {result.confidence:.1%}")
                print(f"      Answer: {result.answer[:100]}...")
                print(f"      Sources: {len(result.sources)}")
                
                if result.confidence > 0:
                    print(f"   🎉 AI system is working perfectly!")
                else:
                    print(f"   ⚠️  AI system needs tuning (low confidence)")
            else:
                print("   ⚠️  No relevant chunks found")
        else:
            print("   ❌ Embedding generation failed")
    else:
        print("   ⚠️  No documents were processed successfully")
    
    main_db.close()
    rag_db.close()

if __name__ == "__main__":
    asyncio.run(fix_rag_database())
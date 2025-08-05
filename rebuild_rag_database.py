#!/usr/bin/env python3
"""Completely rebuild RAG database with correct embeddings"""

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

async def rebuild_rag_database():
    print("🔧 COMPLETELY REBUILDING RAG DATABASE")
    print("=" * 60)
    
    print("1. Dropping all RAG tables...")
    try:
        # Drop all RAG tables to start fresh
        RagBase.metadata.drop_all(bind=rag_engine)
        print("   ✅ All RAG tables dropped")
    except Exception as e:
        print(f"   ⚠️ Error dropping tables: {e}")
    
    print("2. Creating new RAG tables...")
    try:
        # Create fresh RAG tables
        RagBase.metadata.create_all(bind=rag_engine)
        print("   ✅ New RAG tables created")
    except Exception as e:
        print(f"   ❌ Error creating tables: {e}")
        return False
    
    # Get database sessions
    main_db = next(get_db())
    rag_db = next(get_rag_db())
    
    print("3. Verifying embedding model...")
    test_embedding = await rag_service.generate_embedding("test")
    if test_embedding:
        model_dims = len(test_embedding)
        print(f"   ✅ Model produces {model_dims} dimensions")
    else:
        print("   ❌ Embedding generation failed!")
        return False
    
    print("4. Getting approved documents...")
    documents = main_db.query(Document).filter(Document.status == 'approved').all()
    print(f"   Found {len(documents)} approved documents")
    
    if not documents:
        print("   ⚠️ No approved documents found")
        return True
    
    print("5. Processing documents one by one...")
    success_count = 0
    
    for i, doc in enumerate(documents, 1):
        try:
            print(f"   Processing {i}/{len(documents)}: Doc {doc.id} ({doc.title[:50] if doc.title else 'No title'})")
            
            # Build content from document
            content_parts = []
            if doc.title:
                content_parts.append(f"Title: {doc.title}")
            if doc.description:
                content_parts.append(f"Description: {doc.description}")
            if doc.ocr_text:
                content_parts.append(f"Content: {doc.ocr_text}")
            
            if not content_parts:
                print(f"     ⚠️ No content for doc {doc.id}")
                continue
            
            full_content = "\n\n".join(content_parts)
            
            # Manually chunk and store using correct methods
            chunks = await rag_service.chunk_document(
                content=full_content,
                document_id=doc.id,
                document_title=doc.title,
                document_country=doc.country
            )
            
            if chunks:
                # Generate embeddings for chunks
                chunk_texts = [chunk.content for chunk in chunks]
                embeddings = await rag_service.generate_embeddings(chunk_texts)
                
                # Manually insert into database to ensure correct format
                for chunk, embedding in zip(chunks, embeddings):
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
                print(f"     ✅ Stored {len(chunks)} chunks")
                success_count += 1
            else:
                print(f"     ⚠️ No chunks generated for doc {doc.id}")
                
        except Exception as e:
            print(f"     ❌ Error processing doc {doc.id}: {e}")
            rag_db.rollback()
            continue
    
    print(f"6. ✅ Processing complete!")
    print(f"   Successfully processed: {success_count}/{len(documents)} documents")
    
    # Final verification
    final_count = rag_db.execute(text("SELECT COUNT(*) FROM document_chunks")).scalar()
    print(f"   Total chunks stored: {final_count}")
    
    if final_count > 0:
        # Test one embedding
        sample = rag_db.execute(text("SELECT embedding FROM document_chunks LIMIT 1")).fetchone()
        if sample and sample[0]:
            final_dims = len(sample[0])
            print(f"   Final embedding dimensions: {final_dims}")
            
            if final_dims == model_dims:
                print("   🎉 SUCCESS: Embedding dimensions are correct!")
                return True
            else:
                print(f"   ❌ STILL WRONG: {final_dims} vs {model_dims}")
                return False
        else:
            print("   ⚠️ No sample embedding found")
            return False
    else:
        print("   ⚠️ No chunks were stored")
        return False

if __name__ == "__main__":
    success = asyncio.run(rebuild_rag_database())
    if success:
        print("\n🎉 RAG DATABASE REBUILD SUCCESSFUL!")
        print("   AI search should now work properly")
    else:
        print("\n❌ RAG DATABASE REBUILD FAILED")
        print("   AI search will not work")
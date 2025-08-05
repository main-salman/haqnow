#!/usr/bin/env python3
"""Manual vector fix using direct SQL with explicit casting"""

import asyncio
import sys
import os
import json

# Add backend to path
sys.path.append('/opt/foi-archive/backend')

from app.database.database import get_db
from app.database.models import Document
from app.services.rag_service import rag_service
from app.database.rag_database import get_rag_db
from sqlalchemy import text

async def manual_vector_fix():
    print("🔧 MANUAL VECTOR FIX")
    print("=" * 40)
    
    rag_db = next(get_rag_db())
    
    # 1. Clear existing chunks
    print("1. Clearing existing chunks...")
    deleted = rag_db.execute(text("DELETE FROM document_chunks")).rowcount
    rag_db.commit()
    print(f"   ✅ Cleared {deleted} chunks")
    
    # 2. Test simple vector storage
    print("2. Testing simple vector storage...")
    
    test_embedding = await rag_service.generate_embedding("Egypt test document")
    print(f"   Generated: {len(test_embedding)} dims")
    
    # Convert to JSON string for PostgreSQL
    embedding_json = json.dumps(test_embedding)
    
    try:
        # Insert with manual vector conversion
        rag_db.execute(text("""
            INSERT INTO document_chunks 
            (document_id, chunk_index, content, embedding)
            VALUES (99999, 0, 'test content', CAST(:embedding_json AS vector))
        """), {"embedding_json": embedding_json})
        
        rag_db.commit()
        print("   ✅ Manual vector storage successful")
        
        # Verify
        result = rag_db.execute(text("SELECT embedding FROM document_chunks WHERE document_id = 99999")).fetchone()
        if result and result[0]:
            stored = result[0]
            print(f"   Stored: {len(stored)} dims, type: {type(stored)}")
            
            # Clean up
            rag_db.execute(text("DELETE FROM document_chunks WHERE document_id = 99999"))
            rag_db.commit()
            
            if len(stored) == 384:
                print("   ✅ Vector format is correct!")
                use_manual_method = True
            else:
                print(f"   ❌ Still wrong: {len(stored)} dims")
                use_manual_method = False
        else:
            use_manual_method = False
            
    except Exception as e:
        print(f"   ❌ Manual storage failed: {e}")
        rag_db.rollback()
        use_manual_method = False
    
    if not use_manual_method:
        print("❌ Manual vector storage failed")
        return False
    
    # 3. Process Egyptian documents specifically
    print("3. Processing Egyptian documents...")
    
    main_db = next(get_db())
    
    # Find Egyptian documents
    egyptian_docs = main_db.query(Document).filter(
        Document.status == 'approved',
        Document.title.ilike('%egypt%')
    ).all()
    
    print(f"   Found {len(egyptian_docs)} Egyptian documents")
    
    if egyptian_docs:
        for doc in egyptian_docs:
            try:
                print(f"   Processing: {doc.title}")
                
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
                
                # Chunk
                chunks = await rag_service.chunk_document(
                    content=full_content,
                    document_id=doc.id,
                    document_title=doc.title,
                    document_country=doc.country
                )
                
                # Generate embeddings
                chunk_texts = [chunk.content for chunk in chunks]
                embeddings = await rag_service.generate_embeddings(chunk_texts)
                
                # Store with manual vector casting
                for chunk, embedding in zip(chunks, embeddings):
                    embedding_json = json.dumps(embedding)
                    
                    rag_db.execute(text("""
                        INSERT INTO document_chunks 
                        (document_id, chunk_index, content, embedding)
                        VALUES (:document_id, :chunk_index, :content, CAST(:embedding_json AS vector))
                    """), {
                        "document_id": chunk.document_id,
                        "chunk_index": chunk.chunk_index,
                        "content": chunk.content,
                        "embedding_json": embedding_json
                    })
                
                rag_db.commit()
                print(f"     ✅ Stored {len(chunks)} chunks")
                
            except Exception as e:
                print(f"     ❌ Error: {e}")
                rag_db.rollback()
                continue
    
    # 4. Process a few more key documents
    print("4. Processing other key documents...")
    
    other_docs = main_db.query(Document).filter(
        Document.status == 'approved',
        ~Document.title.ilike('%egypt%')
    ).limit(5).all()
    
    for doc in other_docs:
        try:
            print(f"   Processing: {doc.title}")
            
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
            
            # Chunk and store
            chunks = await rag_service.chunk_document(
                content=full_content,
                document_id=doc.id,
                document_title=doc.title,
                document_country=doc.country
            )
            
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = await rag_service.generate_embeddings(chunk_texts)
            
            for chunk, embedding in zip(chunks, embeddings):
                embedding_json = json.dumps(embedding)
                
                rag_db.execute(text("""
                    INSERT INTO document_chunks 
                    (document_id, chunk_index, content, embedding)
                    VALUES (:document_id, :chunk_index, :content, CAST(:embedding_json AS vector))
                """), {
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "embedding_json": embedding_json
                })
            
            rag_db.commit()
            print(f"     ✅ Stored {len(chunks)} chunks")
            
        except Exception as e:
            print(f"     ❌ Error: {e}")
            rag_db.rollback()
            continue
    
    # 5. Final count
    final_count = rag_db.execute(text("SELECT COUNT(*) FROM document_chunks")).scalar()
    print(f"5. ✅ Processing complete: {final_count} total chunks")
    
    # Test final dimensions
    if final_count > 0:
        sample = rag_db.execute(text("SELECT embedding FROM document_chunks LIMIT 1")).fetchone()
        if sample and sample[0]:
            final_dims = len(sample[0])
            print(f"   Final embedding dimensions: {final_dims}")
            
            if final_dims == 384:
                print("   🎉 SUCCESS: Embeddings are 384 dimensions!")
                return True
    
    return False

if __name__ == "__main__":
    success = asyncio.run(manual_vector_fix())
    if success:
        print("\n🎉 MANUAL VECTOR FIX SUCCESSFUL!")
        print("   Test AI search now!")
    else:
        print("\n❌ MANUAL VECTOR FIX FAILED")
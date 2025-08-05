#!/usr/bin/env python3
"""Fix embedding dimensions by clearing old embeddings and regenerating them"""

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

async def fix_embeddings():
    print("🔧 Fixing RAG Embedding Dimensions")
    print("=" * 50)
    
    # Get database sessions
    main_db = next(get_db())
    rag_db = next(get_rag_db())
    
    # 1. Check current embedding dimensions
    print("1. Checking current embedding dimensions...")
    sample = rag_db.execute(text("SELECT embedding FROM document_chunks LIMIT 1")).fetchone()
    if sample and sample[0]:
        current_dims = len(sample[0])
        print(f"   Current stored embeddings: {current_dims} dimensions")
    else:
        print("   No embeddings found")
        current_dims = 0
    
    # 2. Check what the current model produces
    print("2. Testing current embedding model...")
    test_embedding = await rag_service.generate_embedding("test")
    if test_embedding:
        model_dims = len(test_embedding)
        print(f"   Current model produces: {model_dims} dimensions")
    else:
        print("   ❌ Embedding generation failed!")
        return False
    
    # 3. If dimensions don't match, clear and regenerate
    if current_dims != model_dims:
        print(f"3. Dimension mismatch detected ({current_dims} vs {model_dims})")
        print("   Clearing all existing chunks...")
        
        deleted = rag_db.execute(text("DELETE FROM document_chunks")).rowcount
        rag_db.commit()
        print(f"   ✅ Deleted {deleted} old chunks")
        
        # 4. Get all documents from main database
        print("4. Getting documents to re-process...")
        documents = main_db.query(Document).filter(Document.status == 'approved').all()
        print(f"   Found {len(documents)} approved documents")
        
        # 5. Re-process each document
        print("5. Re-processing documents with correct embeddings...")
        for i, doc in enumerate(documents, 1):
            try:
                print(f"   Processing {i}/{len(documents)}: Doc {doc.id}")
                
                # Use the correct RAG service method
                await rag_service.process_new_document(doc.id, main_db)
                
                if i % 5 == 0:  # Progress update every 5 docs
                    print(f"   ✅ Processed {i}/{len(documents)} documents")
                    
            except Exception as e:
                print(f"   ⚠️ Error processing doc {doc.id}: {e}")
                continue
        
        print(f"6. ✅ Re-processing complete!")
        
        # 7. Verify the fix
        final_count = rag_db.execute(text("SELECT COUNT(*) FROM document_chunks")).scalar()
        print(f"   Final chunk count: {final_count}")
        
        # Test embedding dimensions
        final_sample = rag_db.execute(text("SELECT embedding FROM document_chunks LIMIT 1")).fetchone()
        if final_sample and final_sample[0]:
            final_dims = len(final_sample[0])
            print(f"   New embedding dimensions: {final_dims}")
            if final_dims == model_dims:
                print("   ✅ Embedding dimensions now match!")
                return True
            else:
                print(f"   ❌ Still mismatched: {final_dims} vs {model_dims}")
                return False
        else:
            print("   ⚠️ No embeddings found after processing")
            return False
        
    else:
        print("3. ✅ Embedding dimensions already match - no action needed")
        return True

if __name__ == "__main__":
    success = asyncio.run(fix_embeddings())
    if success:
        print("\n🎉 SUCCESS: Embedding dimensions fixed!")
        print("   AI search should now work properly")
    else:
        print("\n❌ FAILED: Could not fix embedding dimensions")
        print("   AI search may still have issues")
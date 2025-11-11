#!/usr/bin/env python3
"""
Test multilingual RAG processing with Arabic, French, and Russian documents
"""
import sys
import asyncio
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from app.database.database import SessionLocal
from app.database.models import Document
from app.apis.document_processing import process_document_internal
from app.services.rag_service import rag_service
from sqlalchemy import text

async def test_document(doc_id: int, expected_language: str):
    """Test OCR and RAG processing for a specific document"""
    db = SessionLocal()
    
    try:
        # Get document
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            print(f"❌ Document {doc_id} not found")
            return False
        
        print(f"\n{'='*80}")
        print(f"📄 Testing Document {doc_id}: {doc.title}")
        print(f"   Language: {doc.document_language}")
        print(f"   Country: {doc.country}")
        print(f"   Status: {doc.status}")
        print(f"{'='*80}")
        
        # Check if needs processing
        if not doc.ocr_text or len(doc.ocr_text) < 10:
            print("🔄 Running OCR processing...")
            result = await process_document_internal(doc_id, db)
            
            if result and result.get('ocr_text'):
                ocr_text = result['ocr_text']
                print(f"✅ OCR completed: {len(ocr_text)} chars extracted")
                
                # Refresh document
                db.refresh(doc)
            else:
                print("❌ OCR failed")
                return False
        else:
            print(f"✅ OCR already done: {len(doc.ocr_text)} chars")
        
        # Approve if not already
        if doc.status != 'approved':
            print("🔓 Approving document...")
            doc.status = 'approved'
            db.commit()
            print("✅ Document approved")
        
        # Check RAG chunks
        from app.database.rag_database import get_rag_db
        rag_db = next(get_rag_db())
        result = rag_db.execute(text(f'SELECT COUNT(*) FROM document_chunks WHERE document_id = {doc_id}'))
        chunk_count = result.scalar()
        rag_db.close()
        
        if chunk_count == 0:
            print("🤖 Processing for RAG...")
            success = await rag_service.process_document_for_rag(
                document_id=doc_id,
                content=doc.ocr_text,
                title=doc.title,
                country=doc.country
            )
            
            if success:
                print(f"✅ RAG processing complete")
                
                # Check chunks again
                rag_db = next(get_rag_db())
                result = rag_db.execute(text(f'SELECT COUNT(*) FROM document_chunks WHERE document_id = {doc_id}'))
                chunk_count = result.scalar()
                rag_db.close()
                print(f"📦 Created {chunk_count} chunks")
            else:
                print("❌ RAG processing failed")
                return False
        else:
            print(f"✅ RAG chunks exist: {chunk_count} chunks")
        
        # Test Q&A
        print("\n🧪 Testing Q&A...")
        test_question = "What is this document about?"
        result = await rag_service.answer_question_for_document(
            query=test_question,
            document_id=doc_id,
            db=db
        )
        
        if result.answer and len(result.answer) > 50:
            print(f"✅ Q&A working!")
            print(f"   Answer: {result.answer[:200]}...")
            print(f"   Sources: {len(result.sources)}")
            print(f"   Confidence: {result.confidence}")
            return True
        else:
            print(f"❌ Q&A failed or empty response")
            print(f"   Answer: '{result.answer}'")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

async def main():
    print("🚀 Testing Multilingual RAG System")
    print("="*80)
    
    # Test existing document 10 first
    print("\n1️⃣ Testing Document 10 (Resume - English)")
    success_10 = await test_document(10, "english")
    
    print("\n" + "="*80)
    print("📊 Test Summary")
    print("="*80)
    print(f"Document 10 (English): {'✅ PASS' if success_10 else '❌ FAIL'}")
    print("\n🎉 Testing complete!")

if __name__ == "__main__":
    asyncio.run(main())


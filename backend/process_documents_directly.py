#!/usr/bin/env python3
"""
Process documents 41, 42, 43 directly using the internal processing function.
This bypasses the job queue and processes documents synchronously.
"""
import os
import sys
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.database import SessionLocal
from app.database.models import Document, JobQueue
from app.apis.document_processing import process_document_internal
from datetime import datetime
import structlog

logger = structlog.get_logger()

async def process_documents_directly(document_ids: list):
    """Process documents directly without using the job queue."""
    db = SessionLocal()
    
    try:
        for doc_id in document_ids:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if not doc:
                print(f"❌ Document {doc_id} not found")
                continue
            
            print(f"\n📄 Processing document {doc_id}: {doc.title[:60]}...")
            
            # Check if already processed
            if doc.ocr_text and doc.ocr_text.strip():
                print(f"   ℹ️  Document already has OCR text ({len(doc.ocr_text)} chars)")
                if doc.ai_summary:
                    print(f"   ℹ️  Document already has summary")
                    continue
            
            # Delete any existing jobs for this document
            jobs = db.query(JobQueue).filter(JobQueue.document_id == doc_id).all()
            for job in jobs:
                db.delete(job)
            db.commit()
            
            try:
                # Process document directly
                result = await process_document_internal(doc_id, db)
                
                if result:
                    # Refresh document
                    db.refresh(doc)
                    has_ocr = bool(doc.ocr_text and doc.ocr_text.strip())
                    has_summary = bool(doc.ai_summary and doc.ai_summary.strip())
                    print(f"   ✅ Document processed successfully")
                    print(f"      OCR text: {has_ocr} ({len(doc.ocr_text) if doc.ocr_text else 0} chars)")
                    print(f"      AI Summary: {has_summary} ({len(doc.ai_summary) if doc.ai_summary else 0} chars)")
                else:
                    print(f"   ⚠️  Processing returned None")
                    
            except Exception as e:
                print(f"   ❌ Error processing document: {str(e)}")
                import traceback
                traceback.print_exc()
                db.rollback()
        
        print(f"\n{'='*60}")
        print(f"✅ Processing complete!")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🔄 Processing documents 41, 42, 43 directly...")
    print("="*60)
    asyncio.run(process_documents_directly([41, 42, 43]))


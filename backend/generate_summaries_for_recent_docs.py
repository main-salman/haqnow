#!/usr/bin/env python3
"""
Generate AI summaries for the three most recently uploaded documents.
This script finds documents without summaries and generates them using Thaura AI.
"""
import os
import sys
import asyncio
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.database import SessionLocal
from app.database.models import Document
from app.services.ai_summary_service import ai_summary_service

async def generate_summaries_for_recent_docs(limit: int = 3):
    """Generate AI summaries for the most recently uploaded documents."""
    db: Session = SessionLocal()
    
    try:
        # Find the most recent approved documents, prioritizing those without summaries
        # First try documents without summaries
        documents_no_summary = db.query(Document).filter(
            (Document.ai_summary.is_(None)) | (Document.ai_summary == ""),
            Document.status == "approved",
            Document.ocr_text.isnot(None),
            Document.ocr_text != ""
        ).order_by(Document.created_at.desc()).limit(limit).all()
        
        # If we need more, get the most recent documents regardless of summary status
        if len(documents_no_summary) < limit:
            remaining = limit - len(documents_no_summary)
            documents_with_summary = db.query(Document).filter(
                Document.status == "approved",
                Document.ocr_text.isnot(None),
                Document.ocr_text != "",
                Document.ai_summary.isnot(None),
                Document.ai_summary != ""
            ).order_by(Document.created_at.desc()).limit(remaining).all()
            documents = list(documents_no_summary) + list(documents_with_summary)
        else:
            documents = documents_no_summary
        
        if not documents:
            print("✅ No documents found that need summaries.")
            return
        
        print(f"📄 Found {len(documents)} document(s) without summaries. Generating summaries...")
        
        success_count = 0
        error_count = 0
        
        for doc in documents:
            try:
                print(f"\n📝 Processing document ID {doc.id}: {doc.title[:60]}...")
                
                # Get text for summary - prefer English translation, fallback to OCR text
                summary_text = None
                if hasattr(doc, 'ocr_text_english') and doc.ocr_text_english and doc.ocr_text_english.strip():
                    summary_text = doc.ocr_text_english
                    print("   Using English translation text")
                elif doc.ocr_text and doc.ocr_text.strip():
                    summary_text = doc.ocr_text
                    print("   Using OCR text")
                else:
                    print(f"   ⚠️  Skipping - no text available")
                    error_count += 1
                    continue
                
                # Truncate to first 5000 chars for summary
                summary_text = summary_text[:5000]
                
                # Generate summary
                ai_summary = await ai_summary_service.generate_summary(
                    text=summary_text,
                    title=doc.title,
                    max_length=200
                )
                
                if ai_summary:
                    # Update document with summary
                    doc.ai_summary = ai_summary
                    db.commit()
                    print(f"   ✅ Summary generated ({len(ai_summary)} chars)")
                    success_count += 1
                else:
                    print(f"   ⚠️  Failed to generate summary")
                    error_count += 1
                    
            except Exception as e:
                print(f"   ❌ Error processing document {doc.id}: {str(e)}")
                db.rollback()
                error_count += 1
        
        print(f"\n{'='*60}")
        print(f"✅ Summary generation complete!")
        print(f"   Success: {success_count}")
        print(f"   Errors: {error_count}")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🤖 Generating AI summaries for recent documents using Thaura AI...")
    print("="*60)
    
    # Check if Thaura AI is configured
    if not ai_summary_service.available:
        print("❌ ERROR: Thaura AI is not configured!")
        print("   Please set THAURA_API_KEY in your .env file")
        sys.exit(1)
    
    # Run async function
    asyncio.run(generate_summaries_for_recent_docs(limit=3))


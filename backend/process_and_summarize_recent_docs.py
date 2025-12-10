#!/usr/bin/env python3
"""
Process and generate AI summaries for the three most recently uploaded documents.
This script processes documents that haven't been processed yet, then generates summaries.
"""
import os
import sys
import asyncio
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.database import SessionLocal
from app.database.models import Document
from app.services.ai_summary_service import ai_summary_service
from app.apis.document_processing import process_document_internal

async def process_and_summarize_recent_docs(limit: int = 3):
    """Process and generate AI summaries for the most recently uploaded documents."""
    db: Session = SessionLocal()
    
    try:
        # Get the 3 most recent approved documents
        documents = db.query(Document).filter(
            Document.status == "approved"
        ).order_by(Document.created_at.desc()).limit(limit).all()
        
        if not documents:
            print("✅ No documents found.")
            return
        
        print(f"📄 Found {len(documents)} most recent document(s). Processing and generating summaries...")
        
        success_count = 0
        error_count = 0
        
        for doc in documents:
            try:
                print(f"\n📝 Processing document ID {doc.id}: {doc.title[:60]}...")
                
                # Check if document needs processing
                needs_processing = not doc.ocr_text or not doc.ocr_text.strip()
                
                if needs_processing:
                    print("   ⚙️  Document needs processing (no OCR text found)...")
                    try:
                        # Process the document
                        result = await process_document_internal(doc.id, db)
                        if result:
                            # Refresh document from DB
                            db.refresh(doc)
                            print("   ✅ Document processed successfully")
                        else:
                            print("   ⚠️  Processing returned None")
                    except Exception as e:
                        print(f"   ⚠️  Processing error: {str(e)}")
                        # Continue anyway - maybe OCR text exists but wasn't detected
                
                # Get text for summary - prefer English translation, fallback to OCR text
                summary_text = None
                if hasattr(doc, 'ocr_text_english') and doc.ocr_text_english and doc.ocr_text_english.strip():
                    summary_text = doc.ocr_text_english
                    print("   Using English translation text for summary")
                elif doc.ocr_text and doc.ocr_text.strip():
                    summary_text = doc.ocr_text
                    print("   Using OCR text for summary")
                else:
                    print(f"   ⚠️  Skipping summary - no text available (document may need manual processing)")
                    error_count += 1
                    continue
                
                # Check if summary already exists
                if doc.ai_summary and doc.ai_summary.strip():
                    print(f"   ℹ️  Summary already exists ({len(doc.ai_summary)} chars)")
                    success_count += 1
                    continue
                
                # Truncate to first 5000 chars for summary
                summary_text = summary_text[:5000]
                
                # Generate summary
                print("   🤖 Generating AI summary...")
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
                import traceback
                traceback.print_exc()
                db.rollback()
                error_count += 1
        
        print(f"\n{'='*60}")
        print(f"✅ Processing and summary generation complete!")
        print(f"   Success: {success_count}")
        print(f"   Errors: {error_count}")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🤖 Processing and generating AI summaries for recent documents...")
    print("="*60)
    
    # Check if Thaura AI is configured
    if not ai_summary_service.available:
        print("❌ ERROR: Thaura AI is not configured!")
        print("   Please set THAURA_API_KEY in your .env file")
        sys.exit(1)
    
    # Run async function
    asyncio.run(process_and_summarize_recent_docs(limit=3))


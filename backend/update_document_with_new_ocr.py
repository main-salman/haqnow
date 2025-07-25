#!/usr/bin/env python3
"""
Update document 30 with new Arabic OCR results
"""
import sys
import os
import asyncio

# Set environment variables
os.environ['DATABASE_URL'] = 'mysql+pymysql://foi_user:***REMOVED***@localhost:3306/foi_archive'
os.environ['EXOSCALE_S3_ACCESS_KEY'] = '***REMOVED***'
os.environ['EXOSCALE_S3_SECRET_KEY'] = '***REMOVED***'
os.environ['EXOSCALE_S3_ENDPOINT'] = 'sos-ch-dk-2.exo.io'
os.environ['EXOSCALE_S3_REGION'] = 'ch-dk-2'
os.environ['EXOSCALE_BUCKET'] = 'foi-archive-terraform'
os.environ['EXOSCALE_S3_PUBLIC_URL'] = 'https://sos-ch-dk-2.exo.io/foi-archive-terraform'

# Add the app directory to Python path
sys.path.append('/opt/foi-archive/backend')

from app.database.database import SessionLocal
from app.database.models import Document
from app.services.arabic_ocr_service import arabic_ocr_service
from app.services.s3_service import s3_service
import requests

async def update_document_30():
    """Update document 30 with new Arabic OCR results"""
    
    print("Updating document 30 with new Arabic OCR results...")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Get document 30
        document = db.query(Document).filter(Document.id == 30).first()
        if not document:
            print("❌ Document 30 not found")
            return
        
        print(f"✅ Found document: {document.title}")
        
        # Download the PDF file
        file_path = document.file_path
        file_url = s3_service.get_file_url(file_path)
        print(f"📥 Downloading file from: {file_url}")
        
        response = requests.get(file_url, timeout=30)
        response.raise_for_status()
        pdf_content = response.content
        print(f"✅ Downloaded PDF file: {len(pdf_content)} bytes")
        
        # Process with new Arabic OCR
        print("🔄 Processing with new Arabic OCR...")
        arabic_text, english_translation = await arabic_ocr_service.process_arabic_document(pdf_content)
        
        if arabic_text:
            # Update document with new OCR results
            document.ocr_text_original = arabic_text
            document.ocr_text_english = english_translation or ""
            
            # Use English translation for search if available, otherwise Arabic
            search_text = english_translation if english_translation else arabic_text
            document.ocr_text = search_text[:5000]  # Limit for search performance
            
            # Update combined search_text for full-text search optimization
            search_text_parts = []
            if document.title:
                search_text_parts.append(document.title)
            if document.description:
                search_text_parts.append(document.description)
            if search_text:
                search_text_parts.append(search_text)
            if document.country:
                search_text_parts.append(document.country)
            if document.state:
                search_text_parts.append(document.state)
            if document.generated_tags:
                search_text_parts.extend(document.generated_tags)
            
            # Include both original Arabic and English translation in search
            if document.ocr_text_original:
                search_text_parts.append(document.ocr_text_original)
            if document.ocr_text_english:
                search_text_parts.append(document.ocr_text_english)
            
            document.search_text = ' '.join(search_text_parts)
            
            # Commit changes
            db.commit()
            
            print("✅ Document updated successfully!")
            print(f"📄 Arabic text: {len(arabic_text)} characters")
            print(f"📄 English translation: {len(english_translation) if english_translation else 0} characters")
            print(f"📄 Search text: {len(document.search_text)} characters")
            
        else:
            print("❌ No Arabic text extracted")
            
    except Exception as e:
        print(f"❌ Error during update: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(update_document_30()) 
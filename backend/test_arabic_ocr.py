#!/usr/bin/env python3
"""
Test script for Arabic OCR service
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

from app.services.arabic_ocr_service import arabic_ocr_service
from app.services.s3_service import s3_service
import requests

async def test_arabic_ocr():
    """Test the Arabic OCR service with document ID 30"""
    
    print("Testing Arabic OCR Service...")
    
    # Check if service is available
    if not arabic_ocr_service.is_available():
        print("❌ Arabic OCR service is not available")
        return
    
    print("✅ Arabic OCR service is available")
    
    try:
        # Download the test PDF file
        file_path = "documents/1871e79e-bf31-4eeb-95ec-534621e571aa.pdf"
        file_url = s3_service.get_file_url(file_path)
        print(f"📥 Downloading file from: {file_url}")
        
        response = requests.get(file_url, timeout=30)
        response.raise_for_status()
        pdf_content = response.content
        print(f"✅ Downloaded PDF file: {len(pdf_content)} bytes")
        
        # Process with Arabic OCR
        print("🔄 Processing with Arabic OCR...")
        arabic_text, english_translation = await arabic_ocr_service.process_arabic_document(pdf_content)
        
        print("\n" + "="*50)
        print("RESULTS:")
        print("="*50)
        
        if arabic_text:
            print(f"✅ Arabic text extracted ({len(arabic_text)} characters)")
            print("📄 Arabic text preview:")
            print(arabic_text[:200] + "..." if len(arabic_text) > 200 else arabic_text)
        else:
            print("❌ No Arabic text extracted")
        
        if english_translation:
            print(f"\n✅ English translation generated ({len(english_translation)} characters)")
            print("📄 English translation preview:")
            print(english_translation[:200] + "..." if len(english_translation) > 200 else english_translation)
        else:
            print("\n❌ No English translation generated")
        
        return arabic_text, english_translation
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    asyncio.run(test_arabic_ocr()) 
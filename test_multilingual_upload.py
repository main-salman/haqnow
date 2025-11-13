#!/usr/bin/env python3
"""
Test script to upload, approve, and verify multilingual documents.
"""
import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "https://www.haqnow.com"
# BASE_URL = "http://localhost:8000"  # For local testing

def get_admin_token():
    """Get admin JWT token."""
    admin_email = os.getenv("admin_email")
    admin_password = os.getenv("admin_password")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": admin_email, "password": admin_password}
    )
    
    if response.status_code != 200:
        print(f"❌ Admin login failed: {response.status_code} - {response.text}")
        sys.exit(1)
    
    data = response.json()
    return data.get("access_token")

def upload_file(file_path, title, country, language):
    """Upload a file."""
    print(f"\n📤 Uploading {file_path}...")
    print(f"   Title: {title}")
    print(f"   Language: {language}")
    
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f, 'image/png')}
        data = {
            'title': title,
            'country': country,
            'state': country,
            'document_language': language,
            'description': f'Test upload for {language} language document'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/file-uploader/upload",
            files=files,
            data=data
        )
    
    if response.status_code != 200:
        print(f"❌ Upload failed: {response.status_code} - {response.text}")
        return None
    
    result = response.json()
    document_id = result.get('document_id')
    print(f"✅ Upload successful! Document ID: {document_id}")
    return document_id

def approve_document(document_id, token):
    """Approve a document."""
    print(f"\n✅ Approving document {document_id}...")
    
    response = requests.post(
        f"{BASE_URL}/api/document-processing/approve-document/{document_id}",
        headers={'Authorization': f'Bearer {token}'}
    )
    
    if response.status_code != 200:
        print(f"❌ Approval failed: {response.status_code} - {response.text}")
        return None
    
    result = response.json()
    print(f"✅ Document approved!")
    print(f"   OCR text length: {result.get('ocr_text_length', 0)} chars")
    print(f"   Tags generated: {result.get('tags_generated', 0)}")
    return result

def get_document_details(document_id, token):
    """Get full document details."""
    print(f"\n🔍 Fetching document {document_id} details...")
    
    response = requests.get(
        f"{BASE_URL}/api/document-processing/document/{document_id}",
        headers={'Authorization': f'Bearer {token}'}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch document: {response.status_code} - {response.text}")
        return None
    
    return response.json()

def verify_results(doc, language):
    """Verify OCR, tags, and AI summary."""
    print(f"\n📊 Verification Results for {language} document:")
    print("=" * 60)
    
    # Check OCR text
    ocr_text = doc.get('ocr_text', '')
    if ocr_text:
        preview = ocr_text[:200].replace('\n', ' ')
        print(f"✅ OCR Text: {len(ocr_text)} characters")
        print(f"   Preview: {preview}...")
    else:
        print("❌ OCR Text: MISSING")
    
    # Check tags
    tags = doc.get('generated_tags', [])
    if tags:
        print(f"✅ Tags: {len(tags)} tags generated")
        print(f"   Tags: {', '.join(tags[:10])}")
        if len(tags) > 10:
            print(f"   ... and {len(tags) - 10} more")
    else:
        print("❌ Tags: MISSING")
    
    # Check AI summary
    ai_summary = doc.get('ai_summary', '')
    if ai_summary:
        print(f"✅ AI Summary: {len(ai_summary)} characters")
        print(f"   Summary: {ai_summary[:300]}...")
    else:
        print("❌ AI Summary: MISSING")
    
    # Check status
    status = doc.get('status', 'unknown')
    print(f"📋 Status: {status}")
    
    print("=" * 60)

def main():
    print("🧪 Testing Multilingual Document Upload & Processing")
    print("=" * 60)
    
    # Get admin token
    print("\n🔐 Logging in as admin...")
    token = get_admin_token()
    if not token:
        print("❌ Failed to get admin token")
        sys.exit(1)
    print("✅ Admin authenticated")
    
    # Upload French document
    french_id = upload_file(
        "/Users/salman/Documents/fadih/french-test.png",
        "French Health Information Document",
        "Canada",
        "french"
    )
    
    if not french_id:
        print("❌ French upload failed, aborting")
        sys.exit(1)
    
    # Wait for rate limit (2 minutes between uploads)
    print("\n⏳ Waiting 2 minutes for rate limit...")
    import time
    time.sleep(120)
    
    # Upload Russian document
    russian_id = upload_file(
        "/Users/salman/Documents/fadih/russian-test.png",
        "Russian Ministry of Health Statement",
        "Russia",
        "russian"
    )
    
    if not russian_id:
        print("❌ Russian upload failed, aborting")
        sys.exit(1)
    
    # Wait a moment for processing
    print("\n⏳ Waiting 3 seconds for upload processing...")
    import time
    time.sleep(3)
    
    # Approve French document
    approve_document(french_id, token)
    
    # Wait for processing
    print("\n⏳ Waiting 10 seconds for OCR/tagging/AI processing...")
    time.sleep(10)
    
    # Approve Russian document
    approve_document(russian_id, token)
    
    # Wait for processing
    print("\n⏳ Waiting 10 seconds for OCR/tagging/AI processing...")
    time.sleep(10)
    
    # Verify French document
    french_doc = get_document_details(french_id, token)
    if french_doc:
        verify_results(french_doc, "French")
    
    # Verify Russian document
    russian_doc = get_document_details(russian_id, token)
    if russian_doc:
        verify_results(russian_doc, "Russian")
    
    print("\n🎉 Testing Complete!")
    print(f"\n📄 View documents:")
    print(f"   French: https://www.haqnow.com/document/{french_id}")
    print(f"   Russian: https://www.haqnow.com/document/{russian_id}")

if __name__ == "__main__":
    main()


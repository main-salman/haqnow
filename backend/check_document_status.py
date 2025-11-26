#!/usr/bin/env python3
"""
Check status of a specific document in the database.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("Error: DATABASE_URL not found in environment")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def check_document(document_id: int):
    db = SessionLocal()
    try:
        # Check document
        result = db.execute(text("""
            SELECT id, title, status, approved_at, approved_by, created_at, updated_at, processed_at
            FROM documents
            WHERE id = :doc_id
        """), {"doc_id": document_id})
        
        doc = result.fetchone()
        if not doc:
            print(f"Document {document_id} not found")
            return
        
        print(f"\n=== Document {document_id} ===")
        print(f"Title: {doc[1]}")
        print(f"Status: {doc[2]}")
        print(f"Approved At: {doc[3]}")
        print(f"Approved By: {doc[4]}")
        print(f"Created At: {doc[5]}")
        print(f"Updated At: {doc[6]}")
        print(f"Processed At: {doc[7]}")
        
        # Check job queue
        job_result = db.execute(text("""
            SELECT id, job_type, status, current_step, progress, error_message, 
                   created_at, started_at, completed_at, failed_at
            FROM job_queue
            WHERE document_id = :doc_id
            ORDER BY created_at DESC
        """), {"doc_id": document_id})
        
        jobs = job_result.fetchall()
        if jobs:
            print(f"\n=== Job Queue Entries ({len(jobs)}) ===")
            for job in jobs:
                print(f"\nJob ID: {job[0]}")
                print(f"  Type: {job[1]}")
                print(f"  Status: {job[2]}")
                print(f"  Step: {job[3]}")
                print(f"  Progress: {job[4]}%")
                print(f"  Error: {job[5]}")
                print(f"  Created: {job[6]}")
                print(f"  Started: {job[7]}")
                print(f"  Completed: {job[8]}")
                print(f"  Failed: {job[9]}")
        else:
            print("\n=== No Job Queue Entries ===")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_document_status.py <document_id>")
        sys.exit(1)
    
    doc_id = int(sys.argv[1])
    check_document(doc_id)


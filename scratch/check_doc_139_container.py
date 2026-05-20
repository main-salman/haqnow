import sys
import os
import asyncio
from sqlalchemy import text

from app.database.database import get_db
from app.database.rag_database import get_rag_db
from app.database.models import Document

async def check_doc():
    print("Checking Document 139 in MySQL...")
    db = next(get_db())
    try:
        doc = db.query(Document).filter(Document.id == 139).first()
        if doc:
            print(f"Document found in MySQL!")
            print(f"  ID: {doc.id}")
            print(f"  Title: {doc.title}")
            print(f"  Status: {doc.status}")
            print(f"  Country: {doc.country}")
            print(f"  OCR length: {len(doc.ocr_text) if doc.ocr_text else 0}")
            print(f"  OCR preview: {doc.ocr_text[:200] if doc.ocr_text else 'None'}")
        else:
            print("Document 139 NOT found in MySQL.")
    except Exception as e:
        print(f"MySQL query failed: {e}")
    finally:
        db.close()

    print("\nChecking Document 139 in RAG PostgreSQL database...")
    try:
        rag_db = next(get_rag_db())
        # Let's count chunks for document 139
        result = rag_db.execute(text("SELECT COUNT(*) FROM document_chunks WHERE document_id = :doc_id"), {"doc_id": 139}).scalar()
        print(f"Number of chunks in RAG database for document 139: {result}")
        
        # Let's list a few if any
        if result and result > 0:
            rows = rag_db.execute(text("SELECT chunk_index, content FROM document_chunks WHERE document_id = :doc_id LIMIT 3"), {"doc_id": 139}).fetchall()
            for r in rows:
                print(f"  Chunk {r[0]}: {r[1][:100]}...")
    except Exception as e:
        print(f"PostgreSQL RAG query failed: {e}")
    finally:
        if 'rag_db' in locals():
            rag_db.close()

if __name__ == "__main__":
    asyncio.run(check_doc())

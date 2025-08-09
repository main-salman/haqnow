#!/usr/bin/env python3
"""
One-time script: re-embed all approved documents using the new 1024-dim English model

Usage:
  python3 scripts/reembed_all.py

Notes:
- Reads DB credentials from .env via backend env loader
- Recreates embeddings in RAG PostgreSQL for every approved document
"""

import os
import sys
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database.database import get_db
from app.database.models import Document
from app.services.rag_service import rag_service


async def reembed_all() -> None:
    db = next(get_db())
    try:
        docs = db.query(Document).filter(Document.status == 'approved').all()
        print(f"Found {len(docs)} approved documents to re-embed")
        for d in docs:
            text_parts = []
            if d.title:
                text_parts.append(f"Title: {d.title}")
            if d.description:
                text_parts.append(f"Description: {d.description}")
            # Always prefer English text first
            if d.ocr_text_english:
                text_parts.append(d.ocr_text_english)
            elif d.ocr_text:
                text_parts.append(d.ocr_text)
            elif d.ocr_text_original:
                text_parts.append(d.ocr_text_original)

            content = "\n\n".join([p for p in text_parts if p and p.strip()])
            if not content:
                print(f"Skipping {d.id}: no content")
                continue

            print(f"Re-embedding document {d.id} ...")
            await rag_service.process_document_for_rag(d.id, content, d.title or "Untitled", d.country or "Unknown")
        # After re-embedding, remove any RAG chunks for documents that are no longer approved/exist
        try:
            from app.database.rag_database import rag_engine
            from sqlalchemy import text
            with rag_engine.begin() as conn:
                conn.execute(text("""
                    DELETE FROM document_chunks dc
                    WHERE NOT EXISTS (
                        SELECT 1 FROM documents d WHERE d.id = dc.document_id AND d.status = 'approved'
                    )
                """))
            print("Pruned RAG chunks for non-approved/deleted documents")
        except Exception as cleanup_err:
            print("Warning: failed to prune obsolete RAG chunks:", cleanup_err)
        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(reembed_all())



import sys
import os
import asyncio

from app.database.database import get_db
from app.services.rag_service import rag_service

async def test_qa():
    db = next(get_db())
    try:
        doc_id = 139
        question = "What is this document about?"
        print(f"Asking question: '{question}' for document_id={doc_id}...")
        
        result = await rag_service.answer_question_for_document(question, doc_id, db)
        
        print("\n=== QA Result ===")
        print(f"Query: {result.query}")
        print(f"Answer: {result.answer}")
        print(f"Confidence: {result.confidence}%")
        print(f"Sources count: {len(result.sources) if result.sources else 0}")
        if result.sources:
            for i, src in enumerate(result.sources):
                print(f"  Source {i}: doc_id={src.get('document_id')}, score={src.get('score')}")
                print(f"  Text: {src.get('text')[:200]}...")
                
    except Exception as e:
        print(f"QA Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_qa())

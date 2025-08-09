"""
RAG (Retrieval-Augmented Generation) API endpoints for document Q&A
"""

import time
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, model_validator, ConfigDict

from ...database.database import get_db
from ...database.models import RAGQuery
from ...services.rag_service import rag_service, RAGResult

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response

class QuestionRequest(BaseModel):
    """Request model for asking questions"""
    # Allow extra field "query" and map it to "question" for backward compatibility
    model_config = ConfigDict(extra='allow')

    question: str = Field(..., min_length=5, max_length=1000, description="Question about the documents")
    language: Optional[str] = Field("en", description="Response language preference")

    @model_validator(mode="before")
    @classmethod
    def _normalize_payload(cls, data):
        # Accept payloads that provide "query" instead of "question"
        if isinstance(data, dict) and not data.get("question"):
            if data.get("query"):
                data["question"] = data["query"]
        return data

class QuestionResponse(BaseModel):
    """Response model for Q&A"""
    question: str
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]
    response_time_ms: int
    query_id: int

class DocQuestionRequest(BaseModel):
     """Request model for asking questions about a specific document"""
     model_config = ConfigDict(extra='allow')
     question: str = Field(..., min_length=3, max_length=1000)
     document_id: int = Field(..., description="Target document ID")
     language: Optional[str] = Field("en")

class ProcessDocumentRequest(BaseModel):
    """Request model for processing documents"""
    document_id: int = Field(..., description="ID of document to process for RAG")

class FeedbackRequest(BaseModel):
    """Request model for user feedback"""
    query_id: int = Field(..., description="ID of the RAG query")
    feedback: str = Field(..., description="User feedback: helpful, not_helpful, incorrect")

class RAGStatusResponse(BaseModel):
    """Response model for RAG system status"""
    status: str
    ollama_available: bool
    embedding_model_loaded: bool
    total_chunks: int
    latest_query_time: Optional[str]

# Debug models
class RAGDocChunkCount(BaseModel):
    document_id: int
    chunks: int

class RAGDebugResponse(BaseModel):
    total_chunks: int
    by_document: List[RAGDocChunkCount]

class RAGDocChunkCount(BaseModel):
    document_id: int
    chunks: int

class RAGDebugResponse(BaseModel):
    total_chunks: int
    by_document: List[RAGDocChunkCount]

@router.post("/question", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db)
):
    """
    Ask a question about the documents using RAG
    """
    try:
        start_time = time.time()
        
        logger.info(f"RAG question received: {request.question}")
        
        # Process question through RAG pipeline
        result: RAGResult = await rag_service.answer_question(request.question, db)
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Log the query for monitoring
        rag_query = RAGQuery(
            query_text=request.question,
            answer_text=result.answer,
            confidence_score=result.confidence,
            sources_count=len(result.sources),
            response_time_ms=response_time_ms
        )
        db.add(rag_query)
        db.commit()
        db.refresh(rag_query)
        
        logger.info(f"RAG question answered successfully in {response_time_ms}ms")
        
        # Filter out sources that no longer exist (approved-only)
        filtered_sources = []
        try:
            from ...database.models import Document
            for s in result.sources:
                doc = db.query(Document).filter(Document.id == s.get('document_id')).first()
                if doc and doc.status == 'approved':
                    filtered_sources.append(s)
        except Exception:
            filtered_sources = result.sources

        return QuestionResponse(
            question=result.query,
            answer=result.answer,
            confidence=result.confidence,
            sources=filtered_sources,
            response_time_ms=response_time_ms,
            query_id=rag_query.id
        )
        
    except Exception as e:
        logger.error(f"Error processing RAG question: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your question. Please try again."
        )

@router.post("/document-question", response_model=QuestionResponse)
async def ask_document_question(
    request: DocQuestionRequest,
    db: Session = Depends(get_db)
):
    """
    Ask a question strictly about a specific document using RAG.
    """
    try:
        start_time = time.time()

        logger.info(
            f"RAG document question received: doc_id={request.document_id} q={request.question}"
        )

        # Validate document exists and is approved
        from ...database.models import Document
        doc = db.query(Document).filter(Document.id == request.document_id).first()
        if not doc or doc.status != 'approved':
            raise HTTPException(status_code=404, detail="Document not found or not accessible")

        # Process question through doc-scoped RAG pipeline
        result: RAGResult = await rag_service.answer_question_for_document(
            request.question, request.document_id, db
        )

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # Log the query for monitoring
        rag_query = RAGQuery(
            query_text=f"[doc:{request.document_id}] {request.question}",
            answer_text=result.answer,
            confidence_score=result.confidence,
            sources_count=len(result.sources),
            response_time_ms=response_time_ms
        )
        db.add(rag_query)
        db.commit()
        db.refresh(rag_query)

        # Filter sources to only this document (safety)
        filtered_sources = [
            s for s in result.sources if s.get('document_id') == request.document_id
        ]

        return QuestionResponse(
            question=result.query,
            answer=result.answer,
            confidence=result.confidence,
            sources=filtered_sources,
            response_time_ms=response_time_ms,
            query_id=rag_query.id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document-scoped question: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your question for this document."
        )

@router.post("/process-document")
async def process_document_for_rag(
    request: ProcessDocumentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Process a specific document for RAG (admin function)
    """
    try:
        logger.info(f"Processing document {request.document_id} for RAG")
        
        # Add background task to process document
        background_tasks.add_task(
            rag_service.process_new_document,
            request.document_id,
            db
        )
        
        return {
            "status": "success",
            "message": f"Document {request.document_id} queued for RAG processing",
            "document_id": request.document_id
        }
        
    except Exception as e:
        logger.error(f"Error queuing document {request.document_id} for RAG processing: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing the document."
        )

@router.post("/process-all-documents")
async def process_all_documents_for_rag(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Process all approved documents for RAG (admin function)
    """
    try:
        from ...database.models import Document
        
        # Get all approved documents
        approved_docs = db.query(Document).filter(Document.status == 'approved').all()
        
        logger.info(f"Processing {len(approved_docs)} documents for RAG")
        
        # Add background tasks for each document
        for doc in approved_docs:
            background_tasks.add_task(
                rag_service.process_new_document,
                doc.id,
                db
            )
        
        return {
            "status": "success",
            "message": f"Queued {len(approved_docs)} documents for RAG processing",
            "document_count": len(approved_docs)
        }
        
    except Exception as e:
        logger.error(f"Error queuing all documents for RAG processing: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing documents."
        )

@router.post("/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """
    Submit user feedback on RAG answers
    """
    try:
        # Find the query
        rag_query = db.query(RAGQuery).filter(RAGQuery.id == request.query_id).first()
        if not rag_query:
            raise HTTPException(status_code=404, detail="Query not found")
        
        # Update with feedback
        rag_query.user_feedback = request.feedback
        db.commit()
        
        logger.info(f"Feedback received for query {request.query_id}: {request.feedback}")
        
        return {
            "status": "success",
            "message": "Thank you for your feedback!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving feedback: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while saving feedback."
        )

@router.get("/status", response_model=RAGStatusResponse)
async def get_rag_status(db: Session = Depends(get_db)):
    """
    Get RAG system status and health
    """
    try:
        # Check Ollama availability
        ollama_available = False
        try:
            models = rag_service.ollama_client.list()
            ollama_available = True
        except:
            pass
        
        # Check embedding model
        embedding_model_loaded = rag_service.embedding_model is not None
        
        # Get chunk statistics from the RAG PostgreSQL database
        try:
            from sqlalchemy import text
            from ...database.rag_database import rag_engine
            with rag_engine.connect() as rag_conn:
                chunk_count_result = rag_conn.execute(text("SELECT COUNT(*) FROM document_chunks")).scalar()
                total_chunks = int(chunk_count_result or 0)
        except Exception:
            total_chunks = 0
        
        # Get latest query time
        latest_query = db.query(RAGQuery).order_by(RAGQuery.created_at.desc()).first()
        latest_query_time = latest_query.created_at.isoformat() if latest_query else None
        
        # Determine overall status
        if ollama_available and embedding_model_loaded:
            status = "operational"
        elif embedding_model_loaded:
            status = "degraded"  # Can do retrieval but not generation
        else:
            status = "unavailable"
        
        return RAGStatusResponse(
            status=status,
            ollama_available=ollama_available,
            embedding_model_loaded=embedding_model_loaded,
            total_chunks=total_chunks,
            latest_query_time=latest_query_time
        )
        
    except Exception as e:
        logger.error(f"Error getting RAG status: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while checking system status."
        )

@router.get("/analytics")
async def get_rag_analytics(db: Session = Depends(get_db)):
    """
    Get RAG usage analytics (admin function)
    """
    try:
        from sqlalchemy import text, func
        
        # Query statistics
        total_queries = db.query(func.count(RAGQuery.id)).scalar()
        
        # Average confidence score
        avg_confidence = db.query(func.avg(RAGQuery.confidence_score)).scalar()
        
        # Response time statistics
        avg_response_time = db.query(func.avg(RAGQuery.response_time_ms)).scalar()
        
        # Feedback statistics
        feedback_stats = db.query(
            RAGQuery.user_feedback,
            func.count(RAGQuery.id)
        ).filter(
            RAGQuery.user_feedback.isnot(None)
        ).group_by(RAGQuery.user_feedback).all()
        
        feedback_summary = {feedback: count for feedback, count in feedback_stats}
        
        # Recent queries
        recent_queries = db.query(RAGQuery).order_by(
            RAGQuery.created_at.desc()
        ).limit(10).all()
        
        return {
            "total_queries": total_queries,
            "average_confidence": float(avg_confidence) if avg_confidence else 0.0,
            "average_response_time_ms": int(avg_response_time) if avg_response_time else 0,
            "feedback_summary": feedback_summary,
            "recent_queries": [
                {
                    "id": q.id,
                    "query": q.query_text[:100] + "..." if len(q.query_text) > 100 else q.query_text,
                    "confidence": q.confidence_score,
                    "response_time_ms": q.response_time_ms,
                    "feedback": q.user_feedback,
                    "created_at": q.created_at.isoformat()
                }
                for q in recent_queries
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting RAG analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving analytics."
        )

@router.get("/debug-doc-chunks/{document_id}")
async def debug_doc_chunks(document_id: int):
    """Debug helper: count chunks by document in RAG DB."""
    try:
        from sqlalchemy import text
        from ...database.rag_database import rag_engine
        with rag_engine.connect() as conn:
            total = conn.execute(text("SELECT COUNT(*) FROM document_chunks")).scalar() or 0
            doc_count = conn.execute(
                text("SELECT COUNT(*) FROM document_chunks WHERE document_id = :id"),
                {"id": document_id}
            ).scalar() or 0
        return {
            "total_chunks": int(total),
            "by_document": [{"document_id": document_id, "chunks": int(doc_count)}],
        }
    except Exception as e:
        logger.error(f"Error in debug_doc_chunks: {e}")
        raise HTTPException(status_code=500, detail="Debug query failed")
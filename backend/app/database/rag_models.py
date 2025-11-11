"""RAG-specific database models for PostgreSQL with pgvector support."""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, UniqueConstraint
from sqlalchemy.sql import func

try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    # Fallback to ARRAY for environments without pgvector
    from sqlalchemy.dialects.postgresql import ARRAY
    Vector = None

from .rag_database import RagBase

class DocumentChunk(RagBase):
    """Document chunk model for RAG operations"""
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    document_title = Column(String(500))
    document_country = Column(String(100))
    
    # Vector embedding - use pgvector if available, otherwise ARRAY
    if PGVECTOR_AVAILABLE and Vector:
        # Use 1536 dimensions to match OpenAI text-embedding-3-small
        embedding = Column(Vector(1536))
    else:
        embedding = Column(ARRAY(Float))  # Fallback to array
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Unique constraint to enable ON CONFLICT upserts
    __table_args__ = (UniqueConstraint('document_id', 'chunk_index', name='uq_document_chunk'),)
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"

class RAGQuery(RagBase):
    """RAG query log model for analytics"""
    __tablename__ = "rag_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(Text, nullable=False)
    answer_text = Column(Text)
    confidence_score = Column(Float)
    sources_count = Column(Integer, default=0)
    response_time_ms = Column(Integer)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<RAGQuery(id={self.id}, query='{self.query_text[:50]}...', confidence={self.confidence_score})>"

# Additional utility functions for vector operations
def create_vector_index_sql():
    """SQL to create vector index for better performance"""
    if PGVECTOR_AVAILABLE:
        return """
        CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding 
        ON document_chunks USING ivfflat (embedding vector_cosine_ops) 
        WITH (lists = 100);
        """
    else:
        return "-- pgvector not available, skipping vector index creation"

def get_vector_similarity_query():
    """Get appropriate similarity query based on pgvector availability"""
    if PGVECTOR_AVAILABLE:
        return """
        SELECT 
            dc.document_id,
            dc.chunk_index,
            dc.content,
            dc.document_title,
            dc.document_country,
            (dc.embedding <=> %s::vector) as similarity
        FROM document_chunks dc
        ORDER BY dc.embedding <=> %s::vector
        LIMIT %s
        """
    else:
        return """
        SELECT 
            dc.document_id,
            dc.chunk_index,
            dc.content,
            dc.document_title,
            dc.document_country,
            -- Fallback cosine similarity calculation
            (1 - (
                (dc.embedding::float[] <.> %s::float[]) / 
                (sqrt(array_sum(array_square(dc.embedding::float[]))) * sqrt(array_sum(array_square(%s::float[]))))
            )) as similarity
        FROM document_chunks dc
        ORDER BY similarity ASC
        LIMIT %s
        """
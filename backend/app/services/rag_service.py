"""
RAG (Retrieval-Augmented Generation) Service for Document Q&A
Uses Groq (fast LLM inference) + sentence-transformers (local embeddings) + PostgreSQL
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
import os
from dataclasses import dataclass
import json

# LLM API client (Groq)
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    Groq = None

# Local embeddings (sentence-transformers)
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database.database import get_db
from ..database.rag_database import get_rag_db, init_rag_db, ensure_pgvector_extension
from ..database.models import Document
from .cache_service import cache_service

logger = logging.getLogger(__name__)

@dataclass
class RAGResult:
    """Result from RAG query"""
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    query: str
    context_used: str

@dataclass
class DocumentChunk:
    """Document chunk with metadata"""
    content: str
    document_id: int
    document_title: str
    document_country: str
    chunk_index: int
    embedding: Optional[List[float]] = None

class RAGService:
    """
    Hybrid RAG service using Groq (cloud LLM) + sentence-transformers (local embeddings)
    """
    
    def __init__(self):
        self.groq_client = None
        self.embedding_model = None
        self.llm_model = "mixtral-8x7b-32768"  # Groq model for LLM
        self.embedding_model_name = "paraphrase-multilingual-MiniLM-L12-v2"  # sentence-transformers
        self.embedding_dimensions = 384  # sentence-transformers dimensions
        self._initialize_clients()
        self._initialize_rag_database()
    
    def _initialize_clients(self):
        """Initialize Groq API (LLM) and sentence-transformers (embeddings)"""
        try:
            # Initialize Groq for LLM inference (cloud)
            groq_api_key = os.getenv("GROQ_API_KEY")
            if not groq_api_key:
                logger.error("GROQ_API_KEY not found in environment variables")
                raise ValueError("GROQ_API_KEY is required for RAG functionality")
            
            if not GROQ_AVAILABLE:
                logger.error("groq package not installed - run: pip install groq")
                raise ImportError("groq package required")
            
            self.groq_client = Groq(api_key=groq_api_key)
            logger.info(f"✅ Groq client initialized (LLM: {self.llm_model})")
            
            # Delay loading sentence-transformers model until first use (saves ~900MB RAM at startup)
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                logger.warning("sentence-transformers not installed - RAG embeddings will not work")
                self.embedding_model = None
            else:
                logger.info(f"✅ sentence-transformers available - model will be lazy-loaded on first RAG query")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG clients: {e}")
            raise
    
    def _initialize_rag_database(self):
        """Initialize RAG database and ensure pgvector extension"""
        try:
            logger.info("Initializing RAG database...")
            
            # Ensure pgvector extension is available
            if ensure_pgvector_extension():
                logger.info("✅ pgvector extension is available")
            else:
                logger.warning("⚠️ pgvector extension not available - vector operations may fail")
            
            # Initialize RAG database tables
            init_rag_db()
            logger.info("✅ RAG database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG database: {e}")
            # Don't raise exception as this shouldn't prevent the main app from starting
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text string using sentence-transformers (local)"""
        # Lazy load the model on first use to save memory at startup
        if self.embedding_model is None and SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.info(f"🔄 Lazy-loading sentence-transformers model ({self.embedding_model_name})...")
            try:
                self.embedding_model = SentenceTransformer(self.embedding_model_name)
                logger.info(f"✅ Embedding model loaded ({self.embedding_dimensions}-dim)")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                return None
        
        if not self.embedding_model:
            logger.error("Embedding model not available")
            return None
        
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, 
                self.embedding_model.encode, 
                text
            )
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using sentence-transformers (local)"""
        # Lazy load the model on first use to save memory at startup
        if self.embedding_model is None and SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.info(f"🔄 Lazy-loading sentence-transformers model ({self.embedding_model_name})...")
            try:
                self.embedding_model = SentenceTransformer(self.embedding_model_name)
                logger.info(f"✅ Embedding model loaded ({self.embedding_dimensions}-dim)")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise RuntimeError(f"Embedding model loading failed: {e}")
        
        if not self.embedding_model:
            raise RuntimeError("Embedding model not available")
        
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, 
                self.embedding_model.encode, 
                texts
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    async def chunk_document(self, content: str, document_id: int, 
                           document_title: str, document_country: str) -> List[DocumentChunk]:
        """
        Chunk document content for optimal RAG performance
        """
        try:
            # Simple but effective chunking strategy
            # Split on paragraphs, then combine to target size
            paragraphs = content.split('\n\n')
            chunks = []
            current_chunk = ""
            chunk_index = 0
            target_size = 500  # Target chunk size in characters
            overlap = 50     # Overlap between chunks
            
            for paragraph in paragraphs:
                # If adding this paragraph exceeds target size, create chunk
                if len(current_chunk) + len(paragraph) > target_size and current_chunk:
                    chunks.append(DocumentChunk(
                        content=current_chunk.strip(),
                        document_id=document_id,
                        document_title=document_title,
                        document_country=document_country,
                        chunk_index=chunk_index
                    ))
                    
                    # Start new chunk with overlap
                    overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                    current_chunk = overlap_text + " " + paragraph
                    chunk_index += 1
                else:
                    current_chunk += "\n\n" + paragraph if current_chunk else paragraph
            
            # Add final chunk
            if current_chunk.strip():
                chunks.append(DocumentChunk(
                    content=current_chunk.strip(),
                    document_id=document_id,
                    document_title=document_title,
                    document_country=document_country,
                    chunk_index=chunk_index
                ))
            
            logger.info(f"Document {document_id} chunked into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to chunk document {document_id}: {e}")
            raise
    
    async def store_document_chunks(self, chunks: List[DocumentChunk], db: Session = None):
        """Store document chunks with embeddings in RAG database"""
        try:
            # Always use the dedicated RAG database; ignore any external session to avoid MySQL misuse
            rag_db = next(get_rag_db())
            should_close = True
            logger.info(f"Using RAG database connection: {rag_db.bind.url}")
                
            # Generate embeddings for all chunks
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = await self.generate_embeddings(chunk_texts)
            
            # Store chunks in RAG database (PostgreSQL with pgvector) using upsert via raw cursor
            raw_connection = rag_db.connection().connection
            cursor = raw_connection.cursor()
            upsert_sql = """
                INSERT INTO document_chunks 
                    (document_id, chunk_index, content, embedding, document_title, document_country)
                VALUES 
                    (%s, %s, %s, %s::vector, %s, %s)
                ON CONFLICT (document_id, chunk_index) DO UPDATE SET
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    document_title = EXCLUDED.document_title,
                    document_country = EXCLUDED.document_country
            """
            for chunk, embedding in zip(chunks, embeddings):
                embedding_literal = '[' + ','.join(map(str, embedding)) + ']'
                cursor.execute(
                    upsert_sql,
                    (
                        chunk.document_id,
                        chunk.chunk_index,
                        chunk.content,
                        embedding_literal,
                        chunk.document_title,
                        chunk.document_country,
                    ),
                )
            raw_connection.commit()
            cursor.close()
            logger.info(f"Stored {len(chunks)} chunks for document {chunks[0].document_id} in RAG database")
            
            if should_close:
                rag_db.close()
            
        except Exception as e:
            logger.error(f"Failed to store document chunks: {e}")
            if 'rag_db' in locals():
                rag_db.rollback()
                if should_close:
                    rag_db.close()
            raise
    
    async def retrieve_relevant_chunks(self, query_embedding: List[float], 
                                     limit: int = 5, db: Session = None) -> List[DocumentChunk]:
        """Retrieve most relevant document chunks for query"""
        try:
            # Always use the dedicated RAG database to ensure pgvector operations
            rag_db = next(get_rag_db())
            should_close = True
            
            # Search for similar chunks using vector similarity in RAG database
            # Convert embedding to PostgreSQL vector literal
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

            # Use direct SQL execution without text() wrapper to avoid parameter escaping
            sql_query = """
                SELECT 
                    document_id,
                    chunk_index,
                    content,
                    document_title,
                    document_country,
                    (embedding <=> %s::vector) as similarity
                FROM document_chunks 
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """

            # Execute using raw psycopg2 connection to avoid SQLAlchemy parameter issues
            raw_connection = rag_db.connection().connection
            cursor = raw_connection.cursor()
            cursor.execute(sql_query, (embedding_str, embedding_str, limit))
            results = cursor.fetchall()
            cursor.close()
            
            chunks = []
            for row in results:
                chunks.append(DocumentChunk(
                    content=row[2],  # content
                    document_id=row[0],  # document_id
                    document_title=row[3],  # document_title
                    document_country=row[4],  # document_country
                    chunk_index=row[1]  # chunk_index
                ))
            
            if should_close:
                rag_db.close()
                
            logger.info(f"Retrieved {len(chunks)} relevant chunks for query from RAG database")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to retrieve relevant chunks: {e}")
            if 'rag_db' in locals() and should_close:
                rag_db.close()
            raise

    async def retrieve_relevant_chunks_for_document(
        self,
        query_embedding: List[float],
        document_id: int,
        limit: int = 8,
    ) -> List[DocumentChunk]:
        """Retrieve most relevant chunks but limited to a single document_id."""
        try:
            rag_db = next(get_rag_db())
            should_close = True

            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            sql_query = """
                SELECT 
                    document_id,
                    chunk_index,
                    content,
                    document_title,
                    document_country,
                    (embedding <=> %s::vector) as similarity
                FROM document_chunks 
                WHERE document_id = %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """

            raw_connection = rag_db.connection().connection
            cursor = raw_connection.cursor()
            cursor.execute(sql_query, (embedding_str, document_id, embedding_str, limit))
            results = cursor.fetchall()
            cursor.close()

            chunks: List[DocumentChunk] = []
            for row in results:
                chunks.append(DocumentChunk(
                    content=row[2],
                    document_id=row[0],
                    document_title=row[3],
                    document_country=row[4],
                    chunk_index=row[1]
                ))

            if should_close:
                rag_db.close()

            logger.info(
                f"Retrieved {len(chunks)} relevant chunks for document {document_id} from RAG database"
            )
            return chunks
        except Exception as e:
            logger.error(f"Failed to retrieve relevant chunks for document {document_id}: {e}")
            try:
                if 'rag_db' in locals() and should_close:
                    rag_db.close()
            except Exception:
                pass
            raise

    async def retrieve_chunks_by_keywords(self, query_text: str, limit: int = 5) -> List[DocumentChunk]:
        """Fallback retrieval using simple keyword matching when semantic search yields nothing."""
        try:
            rag_db = next(get_rag_db())
            should_close = True
            # Extract simple keywords (length >= 4)
            tokens = [t.strip('.,!?"\'()').lower() for t in query_text.split()]
            keywords = [t for t in tokens if len(t) >= 4]
            if not keywords:
                return []
            # Build a dynamic ILIKE filter
            conditions = " OR ".join([f"content ILIKE %s OR document_title ILIKE %s" for _ in keywords])
            sql_query = f"""
                SELECT document_id, chunk_index, content, document_title, document_country
                FROM document_chunks
                WHERE {conditions}
                ORDER BY document_id DESC, chunk_index ASC
                LIMIT %s
            """
            params: List[str | int] = []
            for k in keywords:
                pattern = f"%{k}%"
                params.extend([pattern, pattern])
            params.append(limit)
            raw_connection = rag_db.connection().connection
            cursor = raw_connection.cursor()
            cursor.execute(sql_query, tuple(params))
            results = cursor.fetchall()
            cursor.close()
            chunks: List[DocumentChunk] = []
            for row in results:
                chunks.append(DocumentChunk(
                    content=row[2],
                    document_id=row[0],
                    document_title=row[3],
                    document_country=row[4],
                    chunk_index=row[1]
                ))
            if should_close:
                rag_db.close()
            return chunks
        except Exception as e:
            logger.error(f"Keyword fallback retrieval failed: {e}")
            try:
                if 'rag_db' in locals() and should_close:
                    rag_db.close()
            except Exception:
                pass
            return []
    
    async def generate_answer(self, query: str, context_chunks: List[DocumentChunk]) -> RAGResult:
        """Generate answer using Groq API (fast inference)"""
        
        try:
            # Prepare context from chunks
            context_text = "\n\n".join([
                f"Document: {chunk.document_title} (Country: {chunk.document_country})\n"
                f"Content: {chunk.content}"
                for chunk in context_chunks
            ])
            
            # Create prompt for LLM
            prompt = f"""Based on the following document excerpts, please answer the user's question. If the information is not available in the provided context, please say so clearly.

Context Documents:
{context_text}

User Question: {query}

Please provide a detailed and accurate answer based only on the information provided in the context documents. Include references to the specific documents when possible."""

            if not self.groq_client:
                return RAGResult(
                    answer="AI text generation is not available.",
                    sources=[],
                    confidence=0.0,
                    query=query,
                    context_used=context_text[:1000] + "..." if len(context_text) > 1000 else context_text
                )
            
            # Call Groq API for fast inference
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.groq_client.chat.completions.create(
                    model=self.llm_model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that answers questions based only on provided document context and cites sources."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    max_tokens=2048,
                )
            )
            answer = response.choices[0].message.content
            
            # Prepare sources information (deduplicate by document_id)
            sources_by_doc: Dict[int, Dict[str, Any]] = {}
            for chunk in context_chunks:
                if chunk.document_id not in sources_by_doc:
                    sources_by_doc[chunk.document_id] = {
                        'document_id': chunk.document_id,
                        'document_title': chunk.document_title,
                        'country': chunk.document_country,
                        'chunk_preview': chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content
                    }
            sources = list(sources_by_doc.values())
            
            # Calculate confidence (simple heuristic)
            confidence = min(0.9, 0.3 + 0.1 * len(context_chunks))
            
            return RAGResult(
                answer=answer,
                sources=sources,
                confidence=confidence,
                query=query,
                context_used=context_text[:1000] + "..." if len(context_text) > 1000 else context_text
            )
            
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            # Return fallback response
            return RAGResult(
                answer="I apologize, but I encountered an error while processing your question. Please try again or rephrase your question.",
                sources=[],
                confidence=0.0,
                query=query,
                context_used=""
            )
    
    async def answer_question(self, query: str, db: Session) -> RAGResult:
        """
        Main RAG pipeline: retrieve relevant context and generate answer
        """
        try:
            logger.info(f"Processing RAG query: {query}")
            
            # Step 1: Generate embedding for the query
            query_embedding = await self.generate_embedding(query)
            if not query_embedding:
                logger.error("Failed to generate embedding for query")
                return RAGResult(
                    answer="I'm unable to process your question right now. Please try again later.",
                    sources=[],
                    confidence=0.0,
                    query=query,
                    context_used=""
                )
            
            # Step 2: Retrieve relevant document chunks (semantic)
            relevant_chunks = await self.retrieve_relevant_chunks(query_embedding, limit=20, db=None)
            
            # Heuristic: if question references a specific document id (e.g., "id 73"), load that document's chunks directly
            if not relevant_chunks:
                import re
                id_match = re.search(r"id\s*(\d+)", query, re.IGNORECASE)
                if id_match:
                    target_id = int(id_match.group(1))
                    direct_chunks = await self.retrieve_chunks_by_keywords(str(target_id), limit=10)
                    if direct_chunks:
                        relevant_chunks = direct_chunks
            # Fallback: keyword-based retrieval if semantic search finds nothing
            if not relevant_chunks:
                relevant_chunks = await self.retrieve_chunks_by_keywords(query, limit=10)
            
            if not relevant_chunks:
                return RAGResult(
                    answer="I couldn't find any relevant documents to answer your question. Please try rephrasing your question or check if there are documents available on this topic.",
                    sources=[],
                    confidence=0.0,
                    query=query,
                    context_used=""
                )
            
            # Step 2: Generate answer using LLM
            result = await self.generate_answer(query, relevant_chunks)
            
            logger.info(f"RAG query completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"RAG pipeline failed: {e}")
            return RAGResult(
                answer="I encountered an error while processing your question. Please try again later.",
                sources=[],
                confidence=0.0,
                query=query,
                context_used=""
            )

    async def answer_question_for_document(self, query: str, document_id: int, db: Session) -> RAGResult:
        """
        RAG pipeline scoped strictly to a single document.
        """
        try:
            logger.info(f"Processing RAG doc-scoped query: doc_id={document_id} query={query}")

            query_embedding = await self.generate_embedding(query)
            if not query_embedding:
                logger.error("Failed to generate embedding for query")
                return RAGResult(
                    answer="I'm unable to process your question right now. Please try again later.",
                    sources=[],
                    confidence=0.0,
                    query=query,
                    context_used=""
                )

            relevant_chunks = await self.retrieve_relevant_chunks_for_document(
                query_embedding=query_embedding,
                document_id=document_id,
                limit=10,
            )

            if not relevant_chunks:
                return RAGResult(
                    answer="I couldn't find relevant content in this document for your question.",
                    sources=[],
                    confidence=0.0,
                    query=query,
                    context_used=""
                )

            result = await self.generate_answer(query, relevant_chunks)
            logger.info("RAG doc-scoped query completed successfully")
            return result
        except Exception as e:
            logger.error(f"RAG doc-scoped pipeline failed: {e}")
            return RAGResult(
                answer="I encountered an error while processing your question for this document.",
                sources=[],
                confidence=0.0,
                query=query,
                context_used=""
            )
    
    async def process_new_document(self, document_id: int, db: Session):
        """
        Process newly uploaded document for RAG system
        """
        try:
            # Get document from database
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                logger.error(f"Document {document_id} not found")
                return
            
            # Combine all available text content
            content_parts = []
            if document.title:
                content_parts.append(f"Title: {document.title}")
            if document.description:
                content_parts.append(f"Description: {document.description}")
            if document.ocr_text:
                content_parts.append(f"Content: {document.ocr_text}")
            
            if not content_parts:
                logger.warning(f"No text content available for document {document_id}")
                return
            
            full_content = "\n\n".join(content_parts)
            
            # Chunk the document
            chunks = await self.chunk_document(
                content=full_content,
                document_id=document.id,
                document_title=document.title,
                document_country=document.country
            )
            
            # Store chunks with embeddings in RAG database
            await self.store_document_chunks(chunks)
            
            logger.info(f"Successfully processed document {document_id} for RAG")
            
        except Exception as e:
            logger.error(f"Failed to process document {document_id} for RAG: {e}")
            raise

    async def process_document_for_rag(self, document_id: int, content: str, title: str, country: str) -> bool:
        """
        Process a document for RAG by chunking content and generating embeddings
        """
        try:
            if not content or not content.strip():
                logger.warning(f"Document {document_id} has no content for RAG processing")
                return False
            
            # Create document chunks
            chunks = await self.chunk_document(content, document_id, title, country)
            
            if not chunks:
                logger.warning(f"No chunks created for document {document_id}")
                return False
                
            # Store chunks in database
            db = next(get_db())
            await self.store_document_chunks(chunks, db)
            
            logger.info(f"Successfully processed document {document_id} for RAG: {len(chunks)} chunks created")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process document {document_id} for RAG: {e}")
            return False

# Global RAG service instance
rag_service = RAGService()
"""
RAG (Retrieval-Augmented Generation) Service for Document Q&A
Uses open source components: Ollama + sentence-transformers + PostgreSQL
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json

# Optional imports for RAG functionality
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    ollama = None

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
    Open source RAG service for document question answering
    """
    
    def __init__(self):
        self.embedding_model = None
        self.ollama_client = None
        self.model_name = "llama3"  # Default Ollama model
        self._initialize_models()
        self._initialize_rag_database()
    
    def _initialize_models(self):
        """Initialize open source AI models"""
        try:
            # Check if dependencies are available
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                logger.warning("sentence-transformers not available - RAG embeddings disabled")
                self.embedding_model = None
            else:
                # Initialize sentence-transformers for embeddings
                logger.info("Loading sentence-transformers embedding model...")
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("✅ Embedding model loaded successfully")
            
            if not OLLAMA_AVAILABLE:
                logger.warning("ollama not available - RAG text generation disabled")
                self.ollama_client = None
            else:
                # Initialize Ollama client
                logger.info("Connecting to Ollama...")
                self.ollama_client = ollama.Client()
            
            # Check if model is available, pull if needed
            try:
                models = self.ollama_client.list()
                available_models = [m['name'] for m in models['models']]
                
                if self.model_name not in available_models:
                    logger.info(f"Pulling {self.model_name} model from Ollama...")
                    self.ollama_client.pull(self.model_name)
                    logger.info(f"✅ {self.model_name} model pulled successfully")
                else:
                    logger.info(f"✅ {self.model_name} model already available")
                    
            except Exception as e:
                logger.warning(f"Could not verify Ollama model: {e}")
                # Try with smaller model as fallback
                self.model_name = "llama3:8b"
                logger.info(f"Falling back to {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG models: {e}")
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
        """Generate embedding for a single text string"""
        if not self.embedding_model:
            logger.error("Embedding model not available - install sentence-transformers")
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
        """Generate embeddings for texts using sentence-transformers"""
        if not self.embedding_model:
            raise RuntimeError("Embedding model not available - install sentence-transformers")
        
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
            # Use RAG database if no db session provided
            if db is None:
                rag_db = next(get_rag_db())
                should_close = True
            else:
                rag_db = db
                should_close = False
                
            # Generate embeddings for all chunks
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = await self.generate_embeddings(chunk_texts)
            
            # Store chunks in RAG database
            for chunk, embedding in zip(chunks, embeddings):
                # Store in document_chunks table in RAG database
                query = text("""
                    INSERT INTO document_chunks 
                    (document_id, chunk_index, content, embedding)
                    VALUES (:document_id, :chunk_index, :content, :embedding)
                    ON CONFLICT (document_id, chunk_index) 
                    DO UPDATE SET content = :content, embedding = :embedding
                """)
                
                rag_db.execute(query, {
                    'document_id': chunk.document_id,
                    'chunk_index': chunk.chunk_index,
                    'content': chunk.content,
                    'embedding': embedding
                })
            
            rag_db.commit()
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
            # Use RAG database if no db session provided
            if db is None:
                rag_db = next(get_rag_db())
                should_close = True
            else:
                rag_db = db
                should_close = False
            
            # Search for similar chunks using vector similarity in RAG database
            # Convert embedding to PostgreSQL array format
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            
            # Use raw SQL that works with PostgreSQL and pgvector
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
            
            # Execute with proper parameter binding
            cursor = rag_db.execute(text(sql_query), (embedding_str, embedding_str, limit))
            results = cursor.fetchall()
            
            chunks = []
            for row in results:
                chunks.append(DocumentChunk(
                    content=row.content,
                    document_id=row.document_id,
                    document_title=row.document_title,
                    document_country=row.document_country,
                    chunk_index=row.chunk_index
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
    
    async def generate_answer(self, query: str, context_chunks: List[DocumentChunk]) -> RAGResult:
        """Generate answer using Ollama LLM with retrieved context"""
        if not self.ollama_client:
            return RAGResult(
                answer="AI text generation is not available. Please install Ollama and required dependencies.",
                sources=[],
                confidence=0.0,
                query=query,
                context_used=""
            )
        
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

            # Generate response using Ollama
            response = self.ollama_client.chat(
                model=self.model_name,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a helpful assistant that answers questions about documents related to corruption, transparency, and government accountability. Always base your answers on the provided context and cite sources when possible.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                stream=False
            )
            
            answer = response['message']['content']
            
            # Prepare sources information
            sources = []
            for chunk in context_chunks:
                sources.append({
                    'document_id': chunk.document_id,
                    'document_title': chunk.document_title,
                    'country': chunk.document_country,
                    'chunk_preview': chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content
                })
            
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
            
            # Step 2: Retrieve relevant document chunks
            relevant_chunks = await self.retrieve_relevant_chunks(query_embedding, limit=5, db=None)
            
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
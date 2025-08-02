"""
RAG (Retrieval-Augmented Generation) Service for Document Q&A
Uses open source components: Ollama + sentence-transformers + PostgreSQL
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json

import ollama
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database.database import get_db
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
    
    def _initialize_models(self):
        """Initialize open source AI models"""
        try:
            # Initialize sentence-transformers for embeddings
            logger.info("Loading sentence-transformers embedding model...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Embedding model loaded successfully")
            
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
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts using sentence-transformers"""
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
    
    async def store_document_chunks(self, chunks: List[DocumentChunk], db: Session):
        """Store document chunks with embeddings in database"""
        try:
            # Generate embeddings for all chunks
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = await self.generate_embeddings(chunk_texts)
            
            # Store chunks in database
            for chunk, embedding in zip(chunks, embeddings):
                # Store in document_chunks table
                query = text("""
                    INSERT INTO document_chunks 
                    (document_id, chunk_index, content, embedding)
                    VALUES (:document_id, :chunk_index, :content, :embedding)
                    ON CONFLICT (document_id, chunk_index) 
                    DO UPDATE SET content = :content, embedding = :embedding
                """)
                
                db.execute(query, {
                    'document_id': chunk.document_id,
                    'chunk_index': chunk.chunk_index,
                    'content': chunk.content,
                    'embedding': embedding
                })
            
            db.commit()
            logger.info(f"Stored {len(chunks)} chunks for document {chunks[0].document_id}")
            
        except Exception as e:
            logger.error(f"Failed to store document chunks: {e}")
            db.rollback()
            raise
    
    async def retrieve_relevant_chunks(self, query: str, db: Session, 
                                     limit: int = 5) -> List[DocumentChunk]:
        """Retrieve most relevant document chunks for query"""
        try:
            # Generate embedding for query
            query_embeddings = await self.generate_embeddings([query])
            query_embedding = query_embeddings[0]
            
            # Search for similar chunks
            search_query = text("""
                SELECT 
                    dc.document_id,
                    dc.chunk_index,
                    dc.content,
                    d.title,
                    d.country,
                    (dc.embedding <=> :query_embedding::vector) as similarity
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE d.status = 'approved'
                ORDER BY dc.embedding <=> :query_embedding::vector
                LIMIT :limit
            """)
            
            results = db.execute(search_query, {
                'query_embedding': query_embedding,
                'limit': limit
            })
            
            chunks = []
            for row in results:
                chunks.append(DocumentChunk(
                    content=row.content,
                    document_id=row.document_id,
                    document_title=row.title,
                    document_country=row.country,
                    chunk_index=row.chunk_index
                ))
            
            logger.info(f"Retrieved {len(chunks)} relevant chunks for query")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to retrieve relevant chunks: {e}")
            raise
    
    async def generate_answer(self, query: str, context_chunks: List[DocumentChunk]) -> RAGResult:
        """Generate answer using Ollama LLM with retrieved context"""
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
            
            # Step 1: Retrieve relevant document chunks
            relevant_chunks = await self.retrieve_relevant_chunks(query, db, limit=5)
            
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
            
            # Store chunks with embeddings
            await self.store_document_chunks(chunks, db)
            
            logger.info(f"Successfully processed document {document_id} for RAG")
            
        except Exception as e:
            logger.error(f"Failed to process document {document_id} for RAG: {e}")
            raise

# Global RAG service instance
rag_service = RAGService()
"""
Semantic Search Service using Multilingual BERT
===============================================

This service provides semantic search capabilities using sentence-transformers
with a multilingual BERT model for FOI Archive documents.

Features:
- Multilingual embedding generation (100+ languages)
- Cosine similarity search
- Hybrid search combining semantic and keyword results
- Efficient local processing (no API costs)
"""

import asyncio
import json
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from sentence_transformers import SentenceTransformer
import structlog
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = structlog.get_logger()

class SemanticSearchService:
    """Service for semantic search using multilingual BERT embeddings."""
    
    def __init__(self):
        """Initialize the semantic search service."""
        self.model = None
        # English-only, high-quality OSS model (top MTEB): 1024 dims
        # Source: BAAI/bge-large-en-v1.5
        self.model_name = "BAAI/bge-large-en-v1.5"
        self._model_loaded = False
        
    def _load_model(self):
        """Load the sentence transformer model (lazy loading)."""
        if not self._model_loaded:
            try:
                logger.info("Loading semantic search model", model=self.model_name)
                self.model = SentenceTransformer(self.model_name)
                self._model_loaded = True
                logger.info("Semantic search model loaded successfully", 
                           model=self.model_name, 
                           dimensions=self.model.get_sentence_embedding_dimension())
            except Exception as e:
                logger.error("Failed to load semantic search model", error=str(e))
                raise
    
    def is_available(self) -> bool:
        """Check if the semantic search service is available."""
        try:
            self._load_model()
            return self._model_loaded
        except:
            return False
    
    def generate_embedding(self, text: str, *, is_query: bool = False) -> Optional[List[float]]:
        """
        Generate embedding for a text string.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector, or None if failed
        """
        if not text or not text.strip():
            return None
            
        try:
            self._load_model()
            
            # Clean and prepare text
            clean_text = text.strip()
            if len(clean_text) > 5000:  # Truncate very long texts for efficiency
                clean_text = clean_text[:5000]
            
            # Best practice prefixes for BGE models
            if is_query:
                clean_text = f"query: {clean_text}"
            else:
                clean_text = f"passage: {clean_text}"

            # Generate embedding (L2 normalized)
            embedding = self.model.encode(clean_text, convert_to_tensor=False, normalize_embeddings=True)
            embedding_list = embedding.tolist()
            
            logger.debug("Generated embedding", 
                        text_length=len(clean_text),
                        embedding_dimensions=len(embedding_list))
            
            return embedding_list
            
        except Exception as e:
            logger.error("Failed to generate embedding", error=str(e), text_preview=text[:100])
            return None
    
    def cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1, higher = more similar)
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error("Failed to calculate cosine similarity", error=str(e))
            return 0.0
    
    def search_similar_documents(self, 
                                query_text: str, 
                                db: Session, 
                                limit: int = 20,
                                similarity_threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        Search for documents similar to the query text using semantic similarity.
        
        Args:
            query_text: Text to search for
            db: Database session
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of document dictionaries with similarity scores
        """
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query_text, is_query=True)
            if not query_embedding:
                logger.warning("Failed to generate query embedding", query=query_text)
                return []
            
            # Get all documents with embeddings
            query = text("""
                SELECT id, title, country, state, description, 
                       document_language, generated_tags, search_text,
                       created_at, embedding
                FROM documents 
                WHERE status = 'approved' AND embedding IS NOT NULL
                LIMIT 1000
            """)
            
            result = db.execute(query)
            documents = result.fetchall()
            
            if not documents:
                logger.info("No documents with embeddings found")
                return []
            
            # Calculate similarities
            scored_documents = []
            for doc in documents:
                try:
                    doc_embedding = json.loads(doc.embedding) if doc.embedding else None
                    if not doc_embedding:
                        continue
                    
                    similarity = self.cosine_similarity(query_embedding, doc_embedding)
                    
                    if similarity >= similarity_threshold:
                        scored_documents.append({
                            'id': doc.id,
                            'title': doc.title,
                            'country': doc.country,
                            'state': doc.state,
                            'description': doc.description,
                            'document_language': doc.document_language,
                            'generated_tags': json.loads(doc.generated_tags) if doc.generated_tags else [],
                            'search_text': doc.search_text,
                            'created_at': doc.created_at.isoformat() if doc.created_at else None,
                            'similarity_score': similarity,
                            'search_type': 'semantic'
                        })
                        
                except Exception as e:
                    logger.warning("Error processing document in semantic search", 
                                 doc_id=doc.id, error=str(e))
                    continue
            
            # Sort by similarity score (highest first)
            scored_documents.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # Limit results
            results = scored_documents[:limit]
            
            logger.info("Semantic search completed", 
                       query=query_text,
                       total_documents=len(documents),
                       results_found=len(results),
                       avg_similarity=np.mean([r['similarity_score'] for r in results]) if results else 0)
            
            return results
            
        except Exception as e:
            logger.error("Semantic search failed", query=query_text, error=str(e))
            return []
    
    def generate_document_embedding(self, document_dict: Dict[str, Any]) -> Optional[List[float]]:
        """
        Generate embedding for a document by combining its searchable fields.
        
        Args:
            document_dict: Document data dictionary
            
        Returns:
            Embedding vector or None if failed
        """
        try:
            # Combine searchable text fields
            text_parts = []
            
            if document_dict.get('title'):
                text_parts.append(document_dict['title'])
            
            if document_dict.get('description'):
                text_parts.append(document_dict['description'])
            
            if document_dict.get('search_text'):
                text_parts.append(document_dict['search_text'])
            
            # Use generated tags as additional context
            if document_dict.get('generated_tags'):
                tags = document_dict['generated_tags']
                if isinstance(tags, list):
                    text_parts.extend(tags)
            
            if not text_parts:
                logger.warning("No text content found for embedding generation", 
                             doc_id=document_dict.get('id'))
                return None
            
            # Combine all text
            combined_text = ' '.join(text_parts)
            
            # Generate embedding
            embedding = self.generate_embedding(combined_text, is_query=False)
            
            if embedding:
                logger.debug("Generated document embedding", 
                           doc_id=document_dict.get('id'),
                           text_length=len(combined_text),
                           embedding_dimensions=len(embedding))
            
            return embedding
            
        except Exception as e:
            logger.error("Failed to generate document embedding", 
                        doc_id=document_dict.get('id'), 
                        error=str(e))
            return None

# Global service instance
semantic_search_service = SemanticSearchService() 
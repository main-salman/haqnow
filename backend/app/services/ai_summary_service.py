"""
AI Summary Service using Groq API
Generates concise 1-paragraph summaries of documents for search and display
"""
import os
import structlog
from typing import Optional

logger = structlog.get_logger()

class AISummaryService:
    """Service for generating AI summaries using Groq API"""
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.available = bool(self.api_key)
        
        if not self.available:
            logger.warning("Groq API key not configured - AI summaries disabled")
        else:
            logger.info("AI Summary service initialized with Groq API")
    
    async def generate_summary(self, text: str, title: str = "", max_length: int = 200) -> Optional[str]:
        """
        Generate a concise 1-paragraph summary of document text using Groq API.
        
        Args:
            text: The document text to summarize
            title: Document title (optional, for context)
            max_length: Maximum length in words (default: 200)
        
        Returns:
            Summary text or None if generation failed
        """
        if not self.available:
            logger.warning("AI summary generation skipped - Groq API not configured")
            return None
        
        if not text or len(text.strip()) < 50:
            logger.warning("Text too short for summary generation", text_length=len(text))
            return None
        
        try:
            from groq import Groq
            
            client = Groq(api_key=self.api_key)
            
            # Truncate text if too long (Groq has token limits)
            max_input_chars = 15000  # ~3750 tokens
            if len(text) > max_input_chars:
                text = text[:max_input_chars] + "..."
                logger.debug("Truncated input text for summary", original_length=len(text))
            
            # Create prompt for summary generation
            prompt = f"""Summarize the following document in ONE concise paragraph (maximum {max_length} words). 
Focus on the key facts, main topic, and important details. Be objective and factual.

Document Title: {title}

Document Text:
{text}

Provide ONLY the summary paragraph, no additional commentary or formatting."""
            
            logger.info("Generating AI summary", text_length=len(text), title=title[:50])
            
            # Call Groq API
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Fast, high-quality model
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional document summarizer. Create concise, factual summaries."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more factual output
                max_tokens=300,  # Enough for ~200 word summary
                top_p=0.9,
                stream=False
            )
            
            summary = response.choices[0].message.content.strip()
            
            if not summary:
                logger.error("Empty summary received from Groq API")
                return None
            
            # Clean up the summary
            summary = summary.replace('\n\n', ' ').replace('\n', ' ')
            summary = ' '.join(summary.split())  # Normalize whitespace
            
            # Truncate to max_length words if needed
            words = summary.split()
            if len(words) > max_length:
                summary = ' '.join(words[:max_length]) + '...'
            
            logger.info(
                "AI summary generated successfully",
                summary_length=len(summary),
                word_count=len(summary.split())
            )
            
            return summary
            
        except ImportError:
            logger.error("Groq library not available")
            return None
        except Exception as e:
            logger.error(
                "Error generating AI summary",
                error=str(e),
                error_type=type(e).__name__
            )
            return None
    
    def get_status(self) -> dict:
        """Get current status of AI summary service"""
        return {
            "available": self.available,
            "model": "llama-3.3-70b-versatile" if self.available else None,
            "provider": "Groq API"
        }


# Singleton instance
ai_summary_service = AISummaryService()


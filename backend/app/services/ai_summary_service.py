"""
AI Summary Service using Thaura AI (Ethical LLM)
Generates concise 1-paragraph summaries of documents for search and display
"""
import os
import structlog
from typing import Optional

logger = structlog.get_logger()

class AISummaryService:
    """Service for generating AI summaries using Thaura AI (ethical, privacy-first)"""
    
    def __init__(self):
        self.api_key = os.getenv("THAURA_API_KEY")
        self.base_url = os.getenv("THAURA_BASE_URL", "https://backend.thaura.ai/v1")
        self.available = bool(self.api_key)
        
        if not self.available:
            logger.warning("Thaura API key not configured - AI summaries disabled")
        else:
            logger.info("AI Summary service initialized with Thaura AI (ethical LLM)")
    
    async def generate_summary(self, text: str, title: str = "", max_length: int = 200) -> Optional[str]:
        """
        Generate a concise 1-paragraph summary of document text using Thaura AI.
        
        Args:
            text: The document text to summarize
            title: Document title (optional, for context)
            max_length: Maximum length in words (default: 200)
        
        Returns:
            Summary text or None if generation failed
        """
        if not self.available:
            logger.warning("AI summary generation skipped - Thaura API not configured")
            return None
        
        if not text or len(text.strip()) < 50:
            logger.warning("Text too short for summary generation", text_length=len(text))
            return None
        
        try:
            from openai import OpenAI
            
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            # Truncate text if too long (LLM has token limits)
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
            
            logger.info("Generating AI summary with Thaura AI", text_length=len(text), title=title[:50])
            
            # Call Thaura AI with streaming (required for proper response handling)
            stream = client.chat.completions.create(
                model="thaura",  # Thaura's ethical AI model
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional document summarizer. Create concise, factual summaries. Do not include any thinking or reasoning in your response."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=800,  # Increased from 300 to avoid truncation (Thaura uses tokens internally)
                stream=True  # Thaura requires streaming
            )
            
            # Collect streamed response
            summary = ""
            for chunk in stream:
                if hasattr(chunk, 'choices') and chunk.choices:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        summary += delta.content
            
            summary = summary.strip()
            
            if not summary:
                logger.error("Empty summary received from Thaura AI")
                return None
            
            # Clean up any <think> tags if present
            import re
            summary = re.sub(r'<think>.*?</think>', '', summary, flags=re.DOTALL).strip()
            
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
            logger.error("OpenAI library not available (required for Thaura AI)")
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
            "model": "thaura" if self.available else None,
            "provider": "Thaura AI (Ethical LLM)"
        }


# Singleton instance
ai_summary_service = AISummaryService()

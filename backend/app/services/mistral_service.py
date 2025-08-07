"""
Mistral AI Service for Arabic Document Processing
================================================

This service provides:
1. Arabic OCR capabilities using Mistral's vision models
2. Arabic to English translation
3. Text processing for bilingual search

Environment Variables Required:
- MISTRAL_API_KEY: Mistral AI API key
"""

import os
import base64
import io
from typing import Optional, Tuple
import structlog
from mistralai import Mistral
import requests
from pdf2image import convert_from_bytes
from PIL import Image

logger = structlog.get_logger()

class MistralService:
    """Service for Arabic document processing using Mistral AI."""
    
    def __init__(self):
        """Initialize Mistral AI client."""
        self.api_key = os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            logger.warning("MISTRAL_API_KEY not found in environment variables")
            self.client = None
        else:
            try:
                self.client = Mistral(api_key=self.api_key)
                logger.info("Mistral AI client initialized successfully")
            except Exception as e:
                logger.error("Failed to initialize Mistral AI client", error=str(e))
                self.client = None
    
    def is_available(self) -> bool:
        """Check if Mistral AI service is available."""
        return self.client is not None
    
    def _convert_pdf_to_images(self, pdf_content: bytes) -> list[Image.Image]:
        """Convert PDF to images for OCR processing."""
        try:
            # Convert PDF to images (first 10 pages max for efficiency)
            images = convert_from_bytes(pdf_content, first_page=1, last_page=10, dpi=300)
            logger.info("PDF converted to images", page_count=len(images))
            return images
        except Exception as e:
            logger.error("Failed to convert PDF to images", error=str(e))
            return []
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string."""
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save to bytes
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=95)
            img_bytes = buffer.getvalue()
            
            # Encode to base64
            return base64.b64encode(img_bytes).decode('utf-8')
        except Exception as e:
            logger.error("Failed to convert image to base64", error=str(e))
            return ""
    
    async def extract_arabic_text_from_pdf(self, pdf_content: bytes) -> Optional[str]:
        """
        Extract Arabic text from PDF using Mistral AI vision model.
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            Extracted Arabic text or None if extraction failed
        """
        if not self.is_available():
            logger.error("Mistral AI service not available for Arabic OCR")
            return None
        
        try:
            # Convert PDF to images
            images = self._convert_pdf_to_images(pdf_content)
            if not images:
                logger.error("No images extracted from PDF for Arabic OCR")
                return None
            
            extracted_texts = []
            
            # Process each page (limit to first 5 pages for efficiency)
            for i, image in enumerate(images[:5]):
                try:
                    # Convert image to base64
                    image_base64 = self._image_to_base64(image)
                    if not image_base64:
                        continue
                    
                    # Prepare messages for Mistral AI
                    messages = [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Please extract all Arabic text from this image. Preserve the original Arabic script and formatting. If there's no Arabic text, respond with 'NO_ARABIC_TEXT'. Only return the extracted text, no explanations."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            ]
                        }
                    ]
                    
                    # Call Mistral AI vision model
                    response = self.client.chat.complete(
                        model="pixtral-12b-2409",  # Mistral's vision model
                        messages=messages,
                        max_tokens=2000,
                        temperature=0.1  # Low temperature for accurate OCR
                    )
                    
                    if response.choices and response.choices[0].message.content:
                        page_text = response.choices[0].message.content.strip()
                        
                        # Skip if no Arabic text found
                        if page_text != "NO_ARABIC_TEXT" and page_text:
                            extracted_texts.append(page_text)
                            logger.info("Arabic text extracted from page", page=i+1, text_length=len(page_text))
                    
                except Exception as page_error:
                    logger.warning("Failed to process page for Arabic OCR", page=i+1, error=str(page_error))
                    continue
            
            if extracted_texts:
                # Combine all extracted text
                combined_text = "\n\n".join(extracted_texts)
                logger.info("Arabic OCR completed successfully", 
                           pages_processed=len(extracted_texts),
                           total_text_length=len(combined_text))
                return combined_text
            else:
                logger.info("No Arabic text found in document")
                return None
                
        except Exception as e:
            logger.error("Arabic OCR processing failed", error=str(e))
            return None
    
    async def translate_arabic_to_english(self, arabic_text: str) -> Optional[str]:
        """
        Translate Arabic text to English using Mistral AI.
        
        Args:
            arabic_text: Arabic text to translate
            
        Returns:
            English translation or None if translation failed
        """
        if not self.is_available():
            logger.error("Mistral AI service not available for translation")
            return None
        
        if not arabic_text or not arabic_text.strip():
            return None
        
        try:
            # Split long text into chunks (Mistral AI has token limits)
            chunk_size = 3000  # Conservative chunk size
            chunks = [arabic_text[i:i+chunk_size] for i in range(0, len(arabic_text), chunk_size)]
            
            translated_chunks = []
            
            for i, chunk in enumerate(chunks):
                try:
                    messages = [
                        {
                            "role": "user",
                            "content": f"""Translate the following Arabic text to English. Preserve the meaning and context. Only return the English translation, no explanations or additional text.

Arabic text:
{chunk}"""
                        }
                    ]
                    
                    response = self.client.chat.complete(
                        model="mistral-large-latest",  # Use the best model for translation
                        messages=messages,
                        max_tokens=4000,
                        temperature=0.2  # Low temperature for consistent translation
                    )
                    
                    if response.choices and response.choices[0].message.content:
                        translated_chunk = response.choices[0].message.content.strip()
                        translated_chunks.append(translated_chunk)
                        logger.info("Arabic text chunk translated", chunk=i+1, length=len(translated_chunk))
                    
                except Exception as chunk_error:
                    logger.warning("Failed to translate text chunk", chunk=i+1, error=str(chunk_error))
                    continue
            
            if translated_chunks:
                # Combine all translated chunks
                combined_translation = "\n\n".join(translated_chunks)
                logger.info("Arabic to English translation completed successfully",
                           chunks_translated=len(translated_chunks),
                           total_length=len(combined_translation))
                return combined_translation
            else:
                logger.error("No chunks were successfully translated")
                return None
                
        except Exception as e:
            logger.error("Arabic to English translation failed", error=str(e))
            return None
    
    async def process_arabic_document(self, pdf_content: bytes) -> Tuple[Optional[str], Optional[str]]:
        """
        Complete Arabic document processing: OCR + Translation.
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            Tuple of (arabic_text, english_translation)
        """
        logger.info("Starting complete Arabic document processing")
        
        # Step 1: Extract Arabic text using OCR
        arabic_text = await self.extract_arabic_text_from_pdf(pdf_content)
        if not arabic_text:
            logger.warning("No Arabic text extracted from document")
            return None, None
        
        # Step 2: Translate to English
        english_translation = await self.translate_arabic_to_english(arabic_text)
        if not english_translation:
            logger.warning("Arabic text extracted but translation failed")
            # Return Arabic text even if translation fails
            return arabic_text, None
        
        logger.info("Arabic document processing completed successfully",
                   arabic_length=len(arabic_text),
                   english_length=len(english_translation))
        
        return arabic_text, english_translation

# Global service instance
mistral_service = MistralService() 
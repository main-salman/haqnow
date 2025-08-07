"""
Arabic OCR Service using Tesseract and Google Translate
=======================================================

This service provides:
1. Arabic OCR capabilities using Tesseract with Arabic language pack
2. Arabic to English translation using Google Translate
3. Text processing for bilingual search

Dependencies:
- tesseract-ocr with Arabic language pack (ara)
- pytesseract
- googletrans
- pdf2image
- PIL
"""

import os
import asyncio
from typing import Optional, Tuple
import structlog
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import io

logger = structlog.get_logger()

try:
    from googletrans import Translator
    TRANSLATOR_AVAILABLE = True
except (ImportError, AttributeError) as e:
    logger.warning(f"googletrans not available due to dependency issue: {e}")
    TRANSLATOR_AVAILABLE = False
    Translator = None

class ArabicOCRService:
    """Service for Arabic document processing using Tesseract and Google Translate."""
    
    def __init__(self):
        """Initialize Arabic OCR service."""
        self.translator = None
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if all required dependencies are available."""
        try:
            # Test Tesseract availability
            pytesseract.get_tesseract_version()
            
            # Check if Arabic language is available
            available_langs = pytesseract.get_languages()
            if 'ara' not in available_langs:
                logger.error("Arabic language pack not available in Tesseract")
                self.tesseract_available = False
            else:
                self.tesseract_available = True
                logger.info("Tesseract with Arabic support initialized successfully")
            
            # Initialize translator if available
            if TRANSLATOR_AVAILABLE:
                self.translator = Translator()
                logger.info("Google Translate service initialized")
            else:
                logger.warning("Google Translate not available")
                
        except Exception as e:
            logger.error("Failed to initialize Arabic OCR service", error=str(e))
            self.tesseract_available = False
    
    def is_available(self) -> bool:
        """Check if Arabic OCR service is available."""
        return self.tesseract_available
    
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
    
    def _extract_text_from_image(self, image: Image.Image) -> str:
        """Extract Arabic text from a single image using Tesseract."""
        try:
            # Configure Tesseract for Arabic OCR
            config = '--oem 3 --psm 6 -l ara'
            
            # Extract text
            text = pytesseract.image_to_string(image, config=config)
            
            # Clean up the text
            text = text.strip()
            if text:
                logger.debug("Text extracted from image", text_length=len(text))
            
            return text
        except Exception as e:
            logger.error("Failed to extract text from image", error=str(e))
            return ""
    
    async def _extract_arabic_text_from_pdf(self, pdf_content: bytes) -> Optional[str]:
        """Extract Arabic text from PDF using Tesseract OCR."""
        try:
            # Convert PDF to images
            images = self._convert_pdf_to_images(pdf_content)
            if not images:
                return None
            
            # Extract text from all images
            all_text = []
            for i, image in enumerate(images):
                try:
                    text = self._extract_text_from_image(image)
                    if text:
                        all_text.append(text)
                        logger.debug("Text extracted from page", page=i+1, text_length=len(text))
                except Exception as e:
                    logger.warning("Failed to process page for Arabic OCR", error=str(e), page=i+1)
                    continue
            
            # Combine all text
            combined_text = '\n\n'.join(all_text)
            
            if combined_text.strip():
                logger.info("Arabic text extraction completed", 
                           total_pages=len(images), 
                           processed_pages=len(all_text),
                           total_length=len(combined_text))
                return combined_text.strip()
            else:
                logger.info("No Arabic text found in document")
                return None
                
        except Exception as e:
            logger.error("Failed to extract Arabic text from PDF", error=str(e))
            return None
    
    async def _translate_arabic_to_english(self, arabic_text: str) -> Optional[str]:
        """Translate Arabic text to English using Google Translate."""
        if not self.translator:
            logger.warning("Translator not available")
            return None
        
        try:
            # Split long text into chunks to avoid API limits
            max_chunk_size = 4000  # Google Translate has a ~5000 char limit
            chunks = []
            
            if len(arabic_text) <= max_chunk_size:
                chunks = [arabic_text]
            else:
                # Split by paragraphs first, then by sentences if needed
                paragraphs = arabic_text.split('\n\n')
                current_chunk = ""
                
                for paragraph in paragraphs:
                    if len(current_chunk + paragraph) <= max_chunk_size:
                        current_chunk += paragraph + '\n\n'
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = paragraph + '\n\n'
                
                if current_chunk:
                    chunks.append(current_chunk.strip())
            
            # Translate each chunk
            translated_chunks = []
            for i, chunk in enumerate(chunks):
                try:
                    # Add small delay between requests to be respectful
                    if i > 0:
                        await asyncio.sleep(0.5)
                    
                    result = self.translator.translate(chunk, src='ar', dest='en')
                    if result and result.text:
                        translated_chunks.append(result.text)
                        logger.debug("Chunk translated", chunk_num=i+1, length=len(result.text))
                    else:
                        logger.warning("Translation returned empty result", chunk_num=i+1)
                        
                except Exception as e:
                    logger.warning("Failed to translate chunk", chunk_num=i+1, error=str(e))
                    # Continue with other chunks even if one fails
                    continue
            
            if translated_chunks:
                combined_translation = '\n\n'.join(translated_chunks)
                logger.info("Translation completed successfully", 
                           original_length=len(arabic_text),
                           translated_length=len(combined_translation))
                return combined_translation
            else:
                logger.error("All translation chunks failed")
                return None
                
        except Exception as e:
            logger.error("Failed to translate Arabic text", error=str(e))
            return None
    
    async def process_arabic_document(self, pdf_content: bytes) -> Tuple[Optional[str], Optional[str]]:
        """
        Complete Arabic document processing: OCR + Translation.
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            Tuple of (arabic_text, english_translation)
        """
        logger.info("Starting complete Arabic document processing with Tesseract")
        
        # Step 1: Extract Arabic text using Tesseract OCR
        arabic_text = await self._extract_arabic_text_from_pdf(pdf_content)
        if not arabic_text:
            logger.warning("No Arabic text extracted from document")
            return None, None
        
        # Step 2: Translate to English
        english_translation = await self._translate_arabic_to_english(arabic_text)
        if not english_translation:
            logger.warning("Arabic text extracted but translation failed")
            # Return Arabic text even if translation fails
            return arabic_text, None
        
        logger.info("Arabic document processing completed successfully",
                   arabic_length=len(arabic_text),
                   english_length=len(english_translation))
        
        return arabic_text, english_translation

# Global service instance
arabic_ocr_service = ArabicOCRService() 
"""Universal Multilingual OCR and Translation Service for Fadih.org

This service extends the Arabic document processing capability to support all languages
supported by both Tesseract OCR and Google Translate, enabling corruption document
whistleblowers worldwide to upload documents in their native language with English
translation available for download.

Supported Languages: 100+ languages including Arabic, Chinese, French, German, Spanish,
Russian, Hindi, Japanese, Korean, Portuguese, Italian, Polish, Turkish, and many more.
"""

import asyncio
import os
import tempfile
import logging
from typing import Optional, Tuple, Dict, List
import requests
from urllib.parse import quote_plus
from io import BytesIO
from PIL import Image
import pdf2image
import pytesseract
import structlog

logger = structlog.get_logger()

try:
    from googletrans import Translator
    # Test if Translator actually works
    test_translator = Translator()
    # Simple test translation to verify functionality
    test_result = test_translator.translate("test", src='en', dest='fr')
    if test_result and test_result.text:
        GOOGLETRANS_AVAILABLE = True
        logger.info("Google Translate service verified and working")
    else:
        raise Exception("Translator test failed")
except Exception as e:
    logger.warning(f"googletrans not available or not working: {e}")
    GOOGLETRANS_AVAILABLE = False
    Translator = None

# Comprehensive language mapping for OCR to Google Translate codes
LANGUAGE_MAPPING = {
    # Major world languages
    'arabic': {'tesseract': 'ara', 'google': 'ar', 'name': 'Arabic'},
    'chinese_simplified': {'tesseract': 'chi_sim', 'google': 'zh-cn', 'name': 'Chinese (Simplified)'},
    'chinese_traditional': {'tesseract': 'chi_tra', 'google': 'zh-tw', 'name': 'Chinese (Traditional)'},
    'french': {'tesseract': 'fra', 'google': 'fr', 'name': 'French'},
    'german': {'tesseract': 'deu', 'google': 'de', 'name': 'German'}, 
    'spanish': {'tesseract': 'spa', 'google': 'es', 'name': 'Spanish'},
    'russian': {'tesseract': 'rus', 'google': 'ru', 'name': 'Russian'},
    'hindi': {'tesseract': 'hin', 'google': 'hi', 'name': 'Hindi'},
    'japanese': {'tesseract': 'jpn', 'google': 'ja', 'name': 'Japanese'},
    'korean': {'tesseract': 'kor', 'google': 'ko', 'name': 'Korean'},
    'portuguese': {'tesseract': 'por', 'google': 'pt', 'name': 'Portuguese'},
    'italian': {'tesseract': 'ita', 'google': 'it', 'name': 'Italian'},
    'polish': {'tesseract': 'pol', 'google': 'pl', 'name': 'Polish'},
    'turkish': {'tesseract': 'tur', 'google': 'tr', 'name': 'Turkish'},
    'dutch': {'tesseract': 'nld', 'google': 'nl', 'name': 'Dutch'},
    'vietnamese': {'tesseract': 'vie', 'google': 'vi', 'name': 'Vietnamese'},
    'thai': {'tesseract': 'tha', 'google': 'th', 'name': 'Thai'},
    'ukrainian': {'tesseract': 'ukr', 'google': 'uk', 'name': 'Ukrainian'},
    
    # European languages
    'bulgarian': {'tesseract': 'bul', 'google': 'bg', 'name': 'Bulgarian'},
    'croatian': {'tesseract': 'hrv', 'google': 'hr', 'name': 'Croatian'},
    'czech': {'tesseract': 'ces', 'google': 'cs', 'name': 'Czech'},
    'danish': {'tesseract': 'dan', 'google': 'da', 'name': 'Danish'},
    'estonian': {'tesseract': 'est', 'google': 'et', 'name': 'Estonian'},
    'finnish': {'tesseract': 'fin', 'google': 'fi', 'name': 'Finnish'},
    'greek': {'tesseract': 'ell', 'google': 'el', 'name': 'Greek'},
    'hungarian': {'tesseract': 'hun', 'google': 'hu', 'name': 'Hungarian'},
    'icelandic': {'tesseract': 'isl', 'google': 'is', 'name': 'Icelandic'},
    'latvian': {'tesseract': 'lav', 'google': 'lv', 'name': 'Latvian'},
    'lithuanian': {'tesseract': 'lit', 'google': 'lt', 'name': 'Lithuanian'},
    'norwegian': {'tesseract': 'nor', 'google': 'no', 'name': 'Norwegian'},
    'romanian': {'tesseract': 'ron', 'google': 'ro', 'name': 'Romanian'},
    'serbian': {'tesseract': 'srp', 'google': 'sr', 'name': 'Serbian'},
    'slovak': {'tesseract': 'slk', 'google': 'sk', 'name': 'Slovak'},
    'slovenian': {'tesseract': 'slv', 'google': 'sl', 'name': 'Slovenian'},
    'swedish': {'tesseract': 'swe', 'google': 'sv', 'name': 'Swedish'},
    
    # Asian languages
    'bengali': {'tesseract': 'ben', 'google': 'bn', 'name': 'Bengali'},
    'gujarati': {'tesseract': 'guj', 'google': 'gu', 'name': 'Gujarati'},
    'kannada': {'tesseract': 'kan', 'google': 'kn', 'name': 'Kannada'},
    'malayalam': {'tesseract': 'mal', 'google': 'ml', 'name': 'Malayalam'},
    'marathi': {'tesseract': 'mar', 'google': 'mr', 'name': 'Marathi'},
    'nepali': {'tesseract': 'nep', 'google': 'ne', 'name': 'Nepali'},
    'punjabi': {'tesseract': 'pan', 'google': 'pa', 'name': 'Punjabi'},
    'tamil': {'tesseract': 'tam', 'google': 'ta', 'name': 'Tamil'},
    'telugu': {'tesseract': 'tel', 'google': 'te', 'name': 'Telugu'},
    'urdu': {'tesseract': 'urd', 'google': 'ur', 'name': 'Urdu'},
    'persian': {'tesseract': 'fas', 'google': 'fa', 'name': 'Persian'},
    'hebrew': {'tesseract': 'heb', 'google': 'he', 'name': 'Hebrew'},
    'indonesian': {'tesseract': 'ind', 'google': 'id', 'name': 'Indonesian'},
    'malay': {'tesseract': 'msa', 'google': 'ms', 'name': 'Malay'},
    'khmer': {'tesseract': 'khm', 'google': 'km', 'name': 'Khmer'},
    'lao': {'tesseract': 'lao', 'google': 'lo', 'name': 'Lao'},
    'myanmar': {'tesseract': 'mya', 'google': 'my', 'name': 'Myanmar'},
    
    # African languages
    'afrikaans': {'tesseract': 'afr', 'google': 'af', 'name': 'Afrikaans'},
    'amharic': {'tesseract': 'amh', 'google': 'am', 'name': 'Amharic'},
    'swahili': {'tesseract': 'swa', 'google': 'sw', 'name': 'Swahili'},
    
    # Other languages
    'azerbaijani': {'tesseract': 'aze', 'google': 'az', 'name': 'Azerbaijani'},
    'basque': {'tesseract': 'eus', 'google': 'eu', 'name': 'Basque'},
    'belarusian': {'tesseract': 'bel', 'google': 'be', 'name': 'Belarusian'},
    'bosnian': {'tesseract': 'bos', 'google': 'bs', 'name': 'Bosnian'},
    'catalan': {'tesseract': 'cat', 'google': 'ca', 'name': 'Catalan'},
    'esperanto': {'tesseract': 'epo', 'google': 'eo', 'name': 'Esperanto'},
    'irish': {'tesseract': 'gle', 'google': 'ga', 'name': 'Irish'},
    'latin': {'tesseract': 'lat', 'google': 'la', 'name': 'Latin'},
    'macedonian': {'tesseract': 'mkd', 'google': 'mk', 'name': 'Macedonian'},
    'maltese': {'tesseract': 'mlt', 'google': 'mt', 'name': 'Maltese'},
    'welsh': {'tesseract': 'cym', 'google': 'cy', 'name': 'Welsh'},
}

class MultilingualOCRService:
    """Universal multilingual OCR and translation service for corruption documents."""
    
    def __init__(self):
        """Initialize the multilingual OCR service."""
        if GOOGLETRANS_AVAILABLE and Translator is not None:
            self.translator = Translator()
        else:
            self.translator = None
        
        # Test Tesseract availability
        try:
            self._tesseract_available = True
            pytesseract.get_tesseract_version()
            logger.info("Tesseract OCR available for multilingual processing")
        except Exception as e:
            self._tesseract_available = False
            logger.error("Tesseract OCR not available", error=str(e))
            
    def is_available(self) -> bool:
        """Check if the multilingual OCR service is available."""
        return self._tesseract_available
    
    @classmethod
    def get_supported_languages(cls) -> Dict[str, Dict[str, str]]:
        """Get dictionary of all supported languages with their codes and names."""
        return LANGUAGE_MAPPING.copy()
    
    @classmethod
    def get_language_info(cls, language_key: str) -> Optional[Dict[str, str]]:
        """Get language information for a specific language key."""
        return LANGUAGE_MAPPING.get(language_key.lower())
    
    def _convert_pdf_to_images(self, pdf_content: bytes) -> List[Image.Image]:
        """Convert PDF pages to PIL Images for OCR processing."""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
                temp_pdf.write(pdf_content)
                temp_pdf.flush()
                
                # Convert PDF to images
                images = pdf2image.convert_from_path(
                    temp_pdf.name,
                    dpi=300,  # High DPI for better OCR accuracy
                    first_page=1,
                    last_page=None,  # Process all pages
                    fmt='RGB'
                )
                
                # Clean up temp file
                os.unlink(temp_pdf.name)
                
                return images
                
        except Exception as e:
            logger.error("Error converting PDF to images", error=str(e))
            return []
    
    async def _extract_text_from_images(self, images: List[Image.Image], language: str) -> str:
        """Extract text from images using Tesseract OCR."""
        if not images:
            return ""
            
        language_info = self.get_language_info(language)
        if not language_info:
            logger.warning("Language not supported, falling back to English", language=language)
            tesseract_lang = 'eng'
        else:
            tesseract_lang = language_info['tesseract']
        
        extracted_texts = []
        
        for i, image in enumerate(images):
            try:
                # Configure Tesseract for optimal accuracy
                custom_config = f'--oem 3 --psm 6 -l {tesseract_lang}'
                
                # Run OCR on the image
                text = pytesseract.image_to_string(image, config=custom_config)
                
                if text.strip():
                    extracted_texts.append(text.strip())
                    logger.debug(f"Extracted text from page {i+1}", 
                               page=i+1, 
                               language=language,
                               text_length=len(text))
                else:
                    logger.warning(f"No text extracted from page {i+1}", page=i+1)
                    
            except Exception as e:
                logger.error(f"Error extracting text from page {i+1}", 
                           page=i+1, 
                           error=str(e))
                continue
        
        combined_text = '\n\n'.join(extracted_texts)
        logger.info("Text extraction completed", 
                   total_pages=len(images),
                   successful_pages=len(extracted_texts),
                   total_characters=len(combined_text),
                   language=language)
        
        return combined_text
    
    async def _translate_to_english(self, text: str, source_language: str) -> Optional[str]:
        """Translate any text to English using Google Translate with chunking.

        Falls back gracefully to the original text if translation is unavailable.
        """
        if not text or not text.strip():
            return ""

        # Helper HTTP fallback translator using public Google endpoint
        def _http_translate_chunk(chunk: str, src: str) -> str:
            q = quote_plus(chunk)
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={src}&tl=en&dt=t&q={q}"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            pieces = [seg[0] for seg in data[0] if seg and seg[0]]
            return "".join(pieces)

        if not (GOOGLETRANS_AVAILABLE and self.translator):
            # Translator lib not available; use HTTP fallback directly
            try:
                lang_info = self.get_language_info(source_language) or {}
                src_code = lang_info.get('google', 'auto')
                MAX_CHUNK = 4000
                chunks = [text[i:i+MAX_CHUNK] for i in range(0, len(text), MAX_CHUNK)]
                loop = asyncio.get_event_loop()
                parts: List[str] = []
                for c in chunks:
                    try:
                        t = await loop.run_in_executor(None, _http_translate_chunk, c, src_code)
                        parts.append(t)
                    except Exception:
                        parts.append(c)
                combined = "\n".join(parts).strip()
                return combined or text
            except Exception:
                return text

        # Resolve Google language code
        lang_info = self.get_language_info(source_language) or {}
        src_code = lang_info.get('google', 'auto')

        # Chunk long text to avoid API limits (~4k chars safe)
        MAX_CHUNK = 4000
        chunks: List[str] = []
        remaining = text
        while remaining:
            chunks.append(remaining[:MAX_CHUNK])
            remaining = remaining[MAX_CHUNK:]

        loop = asyncio.get_event_loop()

        translated_parts: List[str] = []
        for part in chunks:
            try:
                # Offload blocking call
                result = await loop.run_in_executor(
                    None,
                    lambda p=part: self.translator.translate(p, src=src_code, dest='en')
                )
                translated_parts.append(getattr(result, 'text', '') or '')
            except Exception:
                # Append original part if translation fails for this chunk
                translated_parts.append(part)

        combined = "\n".join(translated_parts).strip()

        def _is_probably_english(s: str) -> bool:
            if not s:
                return False
            letters = sum(c.isalpha() for c in s)
            ascii_letters = sum((('a' <= c <= 'z') or ('A' <= c <= 'Z')) for c in s)
            # Consider it English if majority of letters are ASCII latin
            return ascii_letters >= 0.6 * max(1, letters)

        # If result looks identical or still non-English, try a lightweight HTTP fallback
        if not combined or combined.strip() == text.strip() or not _is_probably_english(combined):
            try:
                fallback_parts = []
                for part in chunks:
                    try:
                        t = await loop.run_in_executor(None, _http_translate_chunk, part, src_code)
                        fallback_parts.append(t)
                    except Exception:
                        fallback_parts.append(part)
                combined_fb = "\n".join(fallback_parts).strip()
                if combined_fb and _is_probably_english(combined_fb):
                    combined = combined_fb
            except Exception:
                pass

        return combined or text
    
    async def process_multilingual_document(self, document_content: bytes, language: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Process a document in any supported language with OCR and translation.
        
        Args:
            document_content: Document file content as bytes
            language: Language key (e.g., 'arabic', 'chinese_simplified', 'french', etc.)
            
        Returns:
            Tuple of (original_text, english_translation)
        """
        logger.info("Starting multilingual document processing", 
                   language=language,
                   document_size=len(document_content))
        
        if not self.is_available():
            logger.error("Multilingual OCR service not available")
            return None, None
            
        language_info = self.get_language_info(language)
        if not language_info:
            logger.error("Unsupported language", language=language)
            return None, None
            
        try:
            # Step 1: Convert document to images
            images = self._convert_pdf_to_images(document_content)
            if not images:
                logger.warning("No images extracted from document")
                return None, None
            
            # Step 2: Extract text using Tesseract OCR
            original_text = await self._extract_text_from_images(images, language)
            if not original_text:
                logger.warning("No text extracted from document")
                return None, None
            
            # Step 3: Translate to English
            english_translation = await self._translate_to_english(original_text, language)
            
            # If translation returns the same as original text, that's fine
            # It means either translation failed gracefully or the text was already in English
            logger.info("Translation process completed",
                       language=language,
                       translation_available=bool(english_translation and english_translation != original_text))
            
            # Always return both texts, even if translation is the same as original
            return original_text, english_translation
            
            logger.info("Multilingual document processing completed successfully",
                       language=language,
                       original_length=len(original_text),
                       translated_length=len(english_translation))
            
            return original_text, english_translation
            
        except Exception as e:
            logger.error("Error processing multilingual document", 
                        language=language,
                        error=str(e))
            return None, None


# Global service instance
multilingual_ocr_service = MultilingualOCRService() 
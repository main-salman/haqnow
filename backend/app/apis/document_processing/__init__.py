from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
import requests
import pytesseract
from pdf2image import convert_from_bytes
import spacy
import io
import re
import os
from collections import Counter
from typing import Optional, List
import structlog

# Import auth and database
from app.auth.user import AdminUser
from app.services.s3_service import s3_service
from app.services.email_service import email_service
from app.services.arabic_ocr_service import arabic_ocr_service  # Add Arabic OCR service import
from app.services.semantic_search_service import semantic_search_service
from app.services.ai_summary_service import ai_summary_service
from app.services.queue_service import queue_service
from app.database import get_db, Document, BannedTag, JobQueue

# Optional RAG service import
try:
    from app.services.rag_service import rag_service
    RAG_AVAILABLE = True
except ImportError:
    rag_service = None
    RAG_AVAILABLE = False

logger = structlog.get_logger()

router = APIRouter()

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
    logger.info("spaCy model loaded successfully")
except OSError:
    logger.warning("spaCy model 'en_core_web_sm' not found. Tagging will be limited.")
    nlp = None 

class ProcessDocumentRequest(BaseModel):
    document_id: int
    pdf_url: str | None = None
    storage_key: str | None = None

class ProcessDocumentResponse(BaseModel):
    document_id: int
    ocr_text: str
    generated_tags: List[str]
    message: str

class DocumentListResponse(BaseModel):
    documents: List[dict]
    total_count: int
    page: int
    per_page: int

def clean_text(text: str) -> str:
    """Clean and normalize text from OCR."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep alphanumeric, spaces, and common punctuation
    text = re.sub(r'[^\w\s\-.,;:!?()[\]{}"]', '', text)
    return text.strip()

def filter_banned_words(text: str, banned_words: List[str]) -> str:
    """Filter banned words from text content."""
    if not text or not banned_words:
        return text
    
    try:
        # Create a case-insensitive replacement pattern
        for banned_word in banned_words:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(banned_word.lower()) + r'\b'
            text = re.sub(pattern, '[REDACTED]', text, flags=re.IGNORECASE)
        
        return text
    except Exception as e:
        logger.error("Error filtering banned words", error=str(e))
        return text

def get_banned_words(db: Session) -> List[str]:
    """Get list of banned words from database."""
    try:
        banned_tags = db.query(BannedTag).all()
        return [tag.tag.lower() for tag in banned_tags]
    except Exception as e:
        logger.error("Error retrieving banned words", error=str(e))
        return []

def get_top_words_for_search(text: str, max_words: int = 1000) -> str:
    """
    Extract the top most important words from text for search purposes.
    Uses word frequency and importance scoring.
    """
    if not text:
        return ""
    
    try:
        # Clean and split text into words
        words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
        
        if len(words) <= max_words:
            return text
        
        # Define stop words to exclude from top words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'this', 'that', 'these', 'those', 'a', 'an', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'must', 'shall', 'it', 'he', 'she',
            'they', 'we', 'you', 'i', 'me', 'him', 'her', 'them', 'us', 'my', 'your',
            'his', 'her', 'its', 'our', 'their', 'who', 'what', 'where', 'when', 'why',
            'how', 'which', 'than', 'so', 'very', 'just', 'now', 'then', 'here', 'there'
        }
        
        # Count word frequencies, excluding stop words
        word_counts = Counter()
        for word in words:
            if word not in stop_words and len(word) >= 3:
                word_counts[word] += 1
        
        # Get top words by frequency
        top_words = [word for word, count in word_counts.most_common(max_words)]
        
        # Reconstruct text using only top words
        result_words = []
        word_set = set(top_words)
        
        for word in words:
            if word in word_set:
                result_words.append(word)
            if len(result_words) >= max_words:
                break
        
        return ' '.join(result_words)
        
    except Exception as e:
        logger.error("Error extracting top words for search", error=str(e))
        # Fallback to first 1000 words if processing fails
        words = text.split()
        return ' '.join(words[:max_words]) if len(words) > max_words else text

def extract_tags_from_text(text: str, max_tags: int = 50, db: Session = None) -> List[str]:
    """Extract meaningful tags from text using spaCy NLP, filtering out banned words."""
    if not nlp or not text:
        return []
    
    try:
        # Get banned words if database session is available
        banned_words = []
        if db:
            banned_words = get_banned_words(db)
        
        # Process text with spaCy
        doc = nlp(text)
        
        # Extract entities (organizations, locations, etc.)
        entities = [ent.text.lower() for ent in doc.ents if len(ent.text) > 2]
        
        # Extract meaningful nouns and noun phrases
        nouns = []
        for token in doc:
            if token.pos_ in ['NOUN', 'PROPN'] and len(token.text) > 2:
                nouns.append(token.lemma_.lower())
        
        # Extract noun chunks
        noun_chunks = [chunk.text.lower() for chunk in doc.noun_chunks if len(chunk.text) > 2]
        
        # Combine all potential tags
        all_tags = entities + nouns + noun_chunks
        
        # Filter out common stop words, very short tags, and banned words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'this', 'that', 'these', 'those'}
        filtered_tags = []
        for tag in all_tags:
            if (tag not in stop_words and 
                len(tag) > 2 and 
                tag.lower() not in banned_words):
                filtered_tags.append(tag)
        
        # Count frequency and return most common
        tag_counts = Counter(filtered_tags)
        return [tag for tag, count in tag_counts.most_common(max_tags)]
        
    except Exception as e:
        logger.error("Error extracting tags from text", error=str(e))
        return []

def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract text from PDF using OCR."""
    try:
        # Convert PDF to images
        images = convert_from_bytes(pdf_content)
        
        # Extract text from each page
        extracted_text = []
        for image in images:
            # Use pytesseract to extract text
            text = pytesseract.image_to_string(image)
            extracted_text.append(text)
        
        # Combine all pages
        full_text = '\n'.join(extracted_text)
        return clean_text(full_text)
        
    except Exception as e:
        logger.error("Error extracting text from PDF", error=str(e))
        return ""

def extract_text_from_image(image_content: bytes) -> str:
    """Extract text from image using OCR."""
    try:
        # Use pytesseract to extract text directly from image bytes
        import PIL.Image
        image = PIL.Image.open(io.BytesIO(image_content))
        text = pytesseract.image_to_string(image)
        return clean_text(text)
        
    except Exception as e:
        logger.error("Error extracting text from image", error=str(e))
        return ""

def extract_text_from_docx(docx_content: bytes) -> str:
    """Extract text from Word document (.docx)."""
    try:
        from docx import Document as DocxDocument
        document = DocxDocument(io.BytesIO(docx_content))
        
        text_parts = []
        for paragraph in document.paragraphs:
            text_parts.append(paragraph.text)
        
        full_text = '\n'.join(text_parts)
        return clean_text(full_text)
        
    except Exception as e:
        logger.error("Error extracting text from DOCX", error=str(e))
        return ""

def extract_text_from_csv(csv_content: bytes) -> str:
    """Extract text from CSV file."""
    try:
        import csv
        text_content = csv_content.decode('utf-8', errors='ignore')
        csv_reader = csv.reader(io.StringIO(text_content))
        
        text_parts = []
        for row in csv_reader:
            text_parts.append(' '.join(row))
        
        full_text = '\n'.join(text_parts)
        return clean_text(full_text)
        
    except Exception as e:
        logger.error("Error extracting text from CSV", error=str(e))
        return ""

def extract_text_from_excel(excel_content: bytes) -> str:
    """Extract text from Excel file (.xls/.xlsx)."""
    try:
        import pandas as pd
        
        # Try to read the Excel file
        df = pd.read_excel(io.BytesIO(excel_content), sheet_name=None)  # Read all sheets
        
        text_parts = []
        for sheet_name, sheet_df in df.items():
            text_parts.append(f"Sheet: {sheet_name}")
            # Convert all values to string and join
            for column in sheet_df.columns:
                text_parts.extend(sheet_df[column].astype(str).tolist())
        
        full_text = '\n'.join(text_parts)
        return clean_text(full_text)
        
    except Exception as e:
        logger.error("Error extracting text from Excel", error=str(e))
        return ""

def extract_text_from_document(file_content: bytes, content_type: str) -> str:
    """Extract text from various document types."""
    content_type = content_type.lower() if content_type else ""
    
    # PDF files
    if "pdf" in content_type:
        return extract_text_from_pdf(file_content)
    
    # Image files  
    elif any(img_type in content_type for img_type in ["image", "jpeg", "jpg", "png", "gif", "bmp", "tiff", "webp"]):
        return extract_text_from_image(file_content)
    
    # Word documents
    elif "wordprocessingml" in content_type or content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(file_content)
    
    # Excel files
    elif "spreadsheetml" in content_type or content_type in ["application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
        return extract_text_from_excel(file_content)
    
    # CSV files
    elif "csv" in content_type or content_type == "text/csv":
        return extract_text_from_csv(file_content)
    
    # Plain text files
    elif "text" in content_type:
        try:
            return clean_text(file_content.decode('utf-8'))
        except UnicodeDecodeError:
            return clean_text(file_content.decode('utf-8', errors='ignore'))
    
    # RTF files
    elif "rtf" in content_type:
        try:
            # Basic RTF handling - strip RTF codes
            text_content = file_content.decode('utf-8', errors='ignore')
            # Remove RTF control codes (basic cleanup)
            import re
            text_content = re.sub(r'\\[a-z]+\d*', '', text_content)
            text_content = re.sub(r'[{}]', '', text_content)
            return clean_text(text_content)
        except Exception as e:
            logger.error("Error extracting text from RTF", error=str(e))
            return ""
    
    # Default: try to decode as text
    else:
        try:
            return clean_text(file_content.decode('utf-8'))
        except UnicodeDecodeError:
            try:
                return clean_text(file_content.decode('latin-1', errors='ignore'))
            except Exception:
                logger.warning("Could not extract text from unknown file type", content_type=content_type)
                return ""

async def process_document_internal(document_id: int, db: Session) -> dict | None:
    """
    Internal function to process a document without requiring admin authentication.
    Used for automatic processing after upload.
    Returns processing result dict or None if failed.
    """
    
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            logger.error("Document not found for internal processing", document_id=document_id)
            return None
        
        # Get file content from S3
        file_path = document.file_path
        if not file_path:
            logger.error("Document file path not found", document_id=document_id)
            return None
        
        # Download file from S3
        file_url = s3_service.get_file_url(file_path)
        
        try:
            response = requests.get(file_url, timeout=30)
            response.raise_for_status()
            file_content = response.content
        except requests.RequestException as e:
            logger.error("Failed to download file from S3 for internal processing", 
                        file_path=file_path, error=str(e))
            return None
        
        # Extract text based on file type and document language
        content_type = document.content_type.lower() if document.content_type else ""
        document_language = getattr(document, 'document_language', 'english')
        
        # Import multilingual OCR service
        from app.services.multilingual_ocr_service import multilingual_ocr_service
        
        # Check if document language is supported for multilingual processing
        supported_languages = multilingual_ocr_service.get_supported_languages()
        language_key = document_language.lower().replace(' ', '_').replace('(', '').replace(')', '')
        
        # Try to find language in supported languages (handle common variations)
        language_mapping = {
            'chinese': 'chinese_simplified',
            'mandarin': 'chinese_simplified', 
            'cantonese': 'chinese_traditional',
            'farsi': 'persian',
            'dari': 'persian',
            'myanmar': 'myanmar',
            'burmese': 'myanmar'
        }
        
        if language_key in language_mapping:
            language_key = language_mapping[language_key]
        
        if language_key in supported_languages and multilingual_ocr_service.is_available():
            logger.info("Processing multilingual document with Tesseract OCR and Google Translate", 
                       document_id=document_id, 
                       language=document_language,
                       language_key=language_key)
            
            try:
                # Use multilingual OCR service for supported languages
                original_text, english_translation = await multilingual_ocr_service.process_multilingual_document(
                    file_content, language_key
                )
                
                if original_text:
                    # Store original text now; ensure we always attempt English translation
                    document.ocr_text_original = original_text

                    # If translation is missing, force a translation attempt now so that
                    # we always have English available for search and tags.
                    if not english_translation or not english_translation.strip():
                        try:
                            english_translation = await multilingual_ocr_service._translate_to_english(
                                original_text, language_key
                            )
                        except Exception as _force_trans_err:
                            logger.warning("Forced translation attempt failed", error=str(_force_trans_err))

                    # Ensure English translation is present; if not, keep trying with fallback HTTP translator
                    if not english_translation or not english_translation.strip():
                        try:
                            from app.services.multilingual_ocr_service import multilingual_ocr_service as _svc2
                            english_translation = await _svc2._translate_to_english(original_text, language_key)
                        except Exception:
                            english_translation = english_translation or ""

                    document.ocr_text_english = english_translation or ""

                    # Prefer English for search and for tag generation. Persist both fields.
                    extracted_text = (english_translation or original_text)
                    document.ocr_text_original = original_text
                    document.ocr_text_english = english_translation or ""
                    
                    logger.info("Multilingual document processed successfully",
                               document_id=document_id,
                               language=document_language,
                               original_length=len(original_text),
                               english_length=len(english_translation) if english_translation else 0)
                else:
                    logger.warning("No text extracted from multilingual document", 
                                 document_id=document_id, 
                                 language=document_language)
                    # Fallback to regular OCR
                    extracted_text = extract_text_from_document(file_content, content_type)
                    document.ocr_text_original = extracted_text
                    
            except Exception as e:
                logger.error("Error processing multilingual document", 
                           document_id=document_id, 
                           language=document_language,
                           error=str(e))
                # Fallback to regular OCR
                extracted_text = extract_text_from_document(file_content, content_type)
                document.ocr_text_original = extracted_text
        else:
            # Regular processing for unsupported languages or when service unavailable
            logger.info("Using regular OCR for unsupported language or service unavailable",
                       document_id=document_id,
                       language=document_language,
                       service_available=multilingual_ocr_service.is_available())
            extracted_text = extract_text_from_document(file_content, content_type)
            document.ocr_text_original = extracted_text
            document.ocr_text_english = extracted_text  # Same as original for unsupported languages
        
        if not extracted_text:
            logger.warning("No text extracted from document during internal processing", document_id=document_id)
            extracted_text = ""
        
        # Filter banned words from full OCR text first
        banned_words = get_banned_words(db)
        if banned_words:
            extracted_text = filter_banned_words(extracted_text, banned_words)
            logger.info("Banned words filtered from OCR text",
                       document_id=document_id,
                       banned_words_count=len(banned_words))
        
        # Get top 1000 most important words for database storage and search
        searchable_text = get_top_words_for_search(extracted_text, max_words=1000)
        original_word_count = len(extracted_text.split()) if extracted_text else 0
        searchable_word_count = len(searchable_text.split()) if searchable_text else 0
        
        logger.info("OCR text processed for search", 
                   document_id=document_id,
                   original_words=original_word_count,
                   searchable_words=searchable_word_count)
        
        # Generate tags from English text whenever possible to keep search English-first
        english_for_tags = None
        try:
            english_for_tags = getattr(document, 'ocr_text_english', None)
        except Exception:
            english_for_tags = None
        tags_source_text = english_for_tags if (english_for_tags and english_for_tags.strip()) else extracted_text
        generated_tags = extract_tags_from_text(tags_source_text, db=db)
        
        # Generate AI summary using Groq API
        ai_summary = None
        try:
            summary_text = tags_source_text[:5000]  # Use first 5000 chars for summary
            ai_summary = await ai_summary_service.generate_summary(
                text=summary_text,
                title=document.title,
                max_length=200
            )
            if ai_summary:
                logger.info("AI summary generated", document_id=document_id, length=len(ai_summary))
        except Exception as e:
            logger.warning("Failed to generate AI summary", error=str(e))
        
        # Update document in database with searchable text (top 1000 words)
        document.ocr_text = searchable_text
        document.generated_tags = generated_tags
        document.ai_summary = ai_summary
        document.processed_at = func.now()
        document.status = "processed"
        
        # Update combined search_text for full-text search optimization (English-first)
        search_text_parts = []
        if document.title:
            search_text_parts.append(document.title)
        if document.description:
            search_text_parts.append(document.description)
        if searchable_text:
            search_text_parts.append(searchable_text)
        if document.country:
            search_text_parts.append(document.country)
        if document.state:
            search_text_parts.append(document.state)
        if generated_tags:
            search_text_parts.extend(generated_tags)
        
        # Include English translation first if available, then original language for recall
        if hasattr(document, 'ocr_text_english') and document.ocr_text_english:
            search_text_parts.append(document.ocr_text_english)
        if hasattr(document, 'ocr_text_original') and document.ocr_text_original:
            search_text_parts.append(document.ocr_text_original)
        
        document.search_text = ' '.join(search_text_parts)
        
        # Generate semantic search embedding
        try:
            if semantic_search_service.is_available():
                document_dict = {
                    'id': document.id,
                    'title': document.title,
                    'description': document.description,
                    'search_text': document.search_text,
                    'generated_tags': generated_tags
                }
                
                embedding = semantic_search_service.generate_document_embedding(document_dict)
                if embedding:
                    import json
                    document.embedding = json.dumps(embedding)
                    logger.info("Generated semantic embedding", 
                               document_id=document.id,
                               embedding_dimensions=len(embedding))
                else:
                    logger.warning("Failed to generate embedding", document_id=document.id)
            else:
                logger.info("Semantic search service not available, skipping embedding generation")
        except Exception as embedding_error:
            logger.warning("Error generating embedding", 
                          document_id=document.id, 
                          error=str(embedding_error))
        
        try:
            db.commit()
            db.refresh(document)
        except Exception as db_error:
            db.rollback()
            logger.error("Database error during internal document processing", error=str(db_error))
            return None
        
        logger.info("Document processed internally", 
                   document_id=document_id,
                   tags_count=len(generated_tags),
                   text_length=len(searchable_text))
        
        return {
            "document_id": document_id,
            "ocr_text": searchable_text,
            "generated_tags": generated_tags,
            "status": "processed"
        }
        
    except Exception as e:
        logger.error("Unexpected error during internal document processing", 
                    document_id=document_id,
                    error=str(e))
        return None

@router.post("/process-document", response_model=ProcessDocumentResponse)
async def process_document(
    request: ProcessDocumentRequest, 
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Process a document by extracting text using OCR and generating tags.
    Only admin users can process documents.
    """
    
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == request.document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get file content from S3
        file_path = document.file_path
        if not file_path:
            raise HTTPException(status_code=400, detail="Document file path not found")
        
        # Download file from S3
        file_url = s3_service.get_file_url(file_path)
        
        try:
            response = requests.get(file_url, timeout=30)
            response.raise_for_status()
            file_content = response.content
        except requests.RequestException as e:
            logger.error("Failed to download file from S3", file_path=file_path, error=str(e))
            raise HTTPException(status_code=500, detail="Failed to download file from storage")
        
        # Extract text based on file type and document language
        content_type = document.content_type.lower() if document.content_type else ""
        document_language = getattr(document, 'document_language', 'english')
        
        # Import multilingual OCR service
        from app.services.multilingual_ocr_service import multilingual_ocr_service
        
        # Check if document language is supported for multilingual processing
        supported_languages = multilingual_ocr_service.get_supported_languages()
        language_key = document_language.lower().replace(' ', '_').replace('(', '').replace(')', '')
        
        # Try to find language in supported languages (handle common variations)
        language_mapping = {
            'chinese': 'chinese_simplified',
            'mandarin': 'chinese_simplified', 
            'cantonese': 'chinese_traditional',
            'farsi': 'persian',
            'dari': 'persian',
            'myanmar': 'myanmar',
            'burmese': 'myanmar'
        }
        
        if language_key in language_mapping:
            language_key = language_mapping[language_key]
        
        if language_key in supported_languages and multilingual_ocr_service.is_available():
            logger.info("Processing multilingual document with Tesseract OCR and Google Translate", 
                       document_id=request.document_id, 
                       language=document_language,
                       language_key=language_key)
            
            try:
                # Use multilingual OCR service for supported languages
                original_text, english_translation = await multilingual_ocr_service.process_multilingual_document(
                    file_content, language_key
                )
                
                if original_text:
                    # Store original text now; ensure we always attempt English translation
                    document.ocr_text_original = original_text

                    # If translation is missing, force a translation attempt now so that
                    # we always have English available for search and tags.
                    if not english_translation or not english_translation.strip():
                        try:
                            english_translation = await multilingual_ocr_service._translate_to_english(
                                original_text, language_key
                            )
                        except Exception as _force_trans_err:
                            logger.warning("Forced translation attempt failed", error=str(_force_trans_err))

                    document.ocr_text_english = english_translation or ""

                    # Prefer English for search when available; otherwise fallback to original
                    extracted_text = (english_translation or original_text)
                    
                    logger.info("Multilingual document processed successfully",
                               document_id=request.document_id,
                               language=document_language,
                               original_length=len(original_text),
                               english_length=len(english_translation) if english_translation else 0)
                else:
                    logger.warning("No text extracted from multilingual document", 
                                 document_id=request.document_id, 
                                 language=document_language)
                    # Fallback to regular OCR
                    extracted_text = extract_text_from_document(file_content, content_type)
                    document.ocr_text_original = extracted_text
                    
            except Exception as e:
                logger.error("Error processing multilingual document", 
                           document_id=request.document_id, 
                           language=document_language,
                           error=str(e))
                # Fallback to regular OCR
                extracted_text = extract_text_from_document(file_content, content_type)
                document.ocr_text_original = extracted_text
        else:
            # Regular processing for unsupported languages or when service unavailable
            logger.info("Using regular OCR for unsupported language or service unavailable",
                       document_id=request.document_id,
                       language=document_language,
                       service_available=multilingual_ocr_service.is_available())
            extracted_text = extract_text_from_document(file_content, content_type)
            document.ocr_text_original = extracted_text
            document.ocr_text_english = extracted_text  # Temporary; below we will try to translate when possible

            # Best-effort translation to English for non-English documents
            if document_language.lower() != "english" and extracted_text:
                try:
                    from app.services.multilingual_ocr_service import multilingual_ocr_service as _svc
                    lang_info = _svc.get_language_info(language_key) or {}
                    google_lang_code = lang_info.get('google', None)
                    if google_lang_code:
                        try:
                            from googletrans import Translator  # type: ignore
                            _translator = Translator()
                            result = _translator.translate(extracted_text, src=google_lang_code, dest='en')
                            if result and getattr(result, 'text', None):
                                document.ocr_text_english = result.text
                                extracted_text = result.text
                                logger.info("Translated unsupported-language document to English",
                                            document_id=request.document_id,
                                            source_language=document_language)
                        except Exception as trans_error:
                            logger.warning("Translation for unsupported language failed",
                                           document_id=request.document_id,
                                           error=str(trans_error))
                except Exception:
                    pass
        
        if not extracted_text:
            logger.warning("No text extracted from document", document_id=request.document_id)
            extracted_text = ""
        
        # Filter banned words from full OCR text first
        banned_words = get_banned_words(db)
        if banned_words:
            extracted_text = filter_banned_words(extracted_text, banned_words)
            logger.info("Banned words filtered from OCR text",
                       document_id=request.document_id,
                       banned_words_count=len(banned_words))
        
        # Get top 1000 most important words for database storage and search
        searchable_text = get_top_words_for_search(extracted_text, max_words=1000)
        original_word_count = len(extracted_text.split()) if extracted_text else 0
        searchable_word_count = len(searchable_text.split()) if searchable_text else 0
        
        logger.info("OCR text processed for search", 
                   document_id=request.document_id,
                   original_words=original_word_count,
                   searchable_words=searchable_word_count)
        
        # Generate tags from English text whenever possible to keep search English-first
        english_for_tags = None
        try:
            english_for_tags = getattr(document, 'ocr_text_english', None)
        except Exception:
            english_for_tags = None
        tags_source_text = english_for_tags if (english_for_tags and english_for_tags.strip()) else extracted_text
        generated_tags = extract_tags_from_text(tags_source_text, db=db)
        
        # Generate AI summary using Groq API
        ai_summary = None
        try:
            summary_text = tags_source_text[:5000]  # Use first 5000 chars for summary
            ai_summary = await ai_summary_service.generate_summary(
                text=summary_text,
                title=document.title,
                max_length=200
            )
            if ai_summary:
                logger.info("AI summary generated", document_id=document_id, length=len(ai_summary))
        except Exception as e:
            logger.warning("Failed to generate AI summary", error=str(e))
        
        # Update document in database with searchable text (top 1000 words)
        document.ocr_text = searchable_text
        document.generated_tags = generated_tags
        document.ai_summary = ai_summary
        document.processed_at = func.now()
        document.status = "processed"
        
        # Update combined search_text for full-text search optimization (English-first)
        search_text_parts = []
        if document.title:
            search_text_parts.append(document.title)
        if document.description:
            search_text_parts.append(document.description)
        if searchable_text:
            search_text_parts.append(searchable_text)
        if document.country:
            search_text_parts.append(document.country)
        if document.state:
            search_text_parts.append(document.state)
        if generated_tags:
            search_text_parts.extend(generated_tags)
        
        # Include English translation first if available, then original language for recall
        if hasattr(document, 'ocr_text_english') and document.ocr_text_english:
            search_text_parts.append(document.ocr_text_english)
        if hasattr(document, 'ocr_text_original') and document.ocr_text_original:
            search_text_parts.append(document.ocr_text_original)
        
        document.search_text = ' '.join(search_text_parts)
        
        # Generate semantic search embedding
        try:
            if semantic_search_service.is_available():
                document_dict = {
                    'id': document.id,
                    'title': document.title,
                    'description': document.description,
                    'search_text': document.search_text,
                    'generated_tags': generated_tags
                }
                
                embedding = semantic_search_service.generate_document_embedding(document_dict)
                if embedding:
                    import json
                    document.embedding = json.dumps(embedding)
                    logger.info("Generated semantic embedding", 
                               document_id=document.id,
                               embedding_dimensions=len(embedding))
                else:
                    logger.warning("Failed to generate embedding", document_id=document.id)
            else:
                logger.info("Semantic search service not available, skipping embedding generation")
        except Exception as embedding_error:
            logger.warning("Error generating embedding", 
                          document_id=document.id, 
                          error=str(embedding_error))
        
        try:
            db.commit()
            db.refresh(document)
        except Exception as db_error:
            db.rollback()
            logger.error("Database error during document update", error=str(db_error))
            raise HTTPException(status_code=500, detail="Failed to update document")
        
        logger.info("Document processed successfully", 
                   document_id=request.document_id,
                   tags_count=len(generated_tags),
                   text_length=len(searchable_text))
        
        return ProcessDocumentResponse(
            document_id=request.document_id,
            ocr_text=searchable_text,
            generated_tags=generated_tags,
            message="Document processed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error during document processing", 
                    document_id=request.document_id,
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during document processing"
        )

@router.post("/approve-document/{document_id}")
async def approve_document(
    document_id: int, 
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Approve a document for public display and trigger OCR processing.
    Only admin users can approve documents.
    """
    
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Allow approving pending or rejected documents
        if document.status not in ["pending", "rejected"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot approve document with status '{document.status}'. Only pending or rejected documents can be approved."
            )
        
        # Enqueue processing job instead of processing synchronously
        job = queue_service.enqueue_job(
            db=db,
            document_id=document_id,
            job_type='process_document',
            priority=0  # FIFO
        )
        
        if not job:
            # Queue is full - reject approval
            raise HTTPException(
                status_code=503,
                detail="Processing queue is full. Please try again later."
            )
        
        # Update document status to approved (processing will happen in background)
        document.status = "approved"
        document.approved_at = func.now()
        document.approved_by = admin_user.email
        
        # Clear rejection fields if document was previously rejected
        if document.rejected_at:
            document.rejected_at = None
            document.rejected_by = None
            document.rejection_reason = None
        
        try:
            db.commit()
            db.refresh(document)
        except Exception as db_error:
            db.rollback()
            logger.error("Database error during document approval", error=str(db_error))
            raise HTTPException(status_code=500, detail="Failed to approve document")
        
        # Send notification email
        try:
            email_service.notify_admin_document_approved(
                document_id=str(document_id),
                title=document.title or "Unknown"
            )
        except Exception as e:
            logger.warning("Failed to send approval notification", error=str(e))
        
        # Process document for RAG (Q&A system) in background
        if RAG_AVAILABLE and rag_service:
            try:
                # Process for RAG without blocking the approval
                await rag_service.process_document_for_rag(
                    document_id=document_id,
                    content=processing_result.get('ocr_text', ''),
                    title=document.title or "Untitled Document",
                    country=document.country or "Unknown"
                )
                logger.info(f"Document {document_id} processed for RAG successfully")
            except Exception as e:
                logger.warning(f"Failed to process document {document_id} for RAG: {e}")
                # Don't fail approval if RAG processing fails
        
        logger.info("Document approved and processed successfully", 
                   document_id=document_id,
                   approved_by=admin_user.email,
                   tags_count=len(processing_result.get('generated_tags', [])),
                   text_length=len(processing_result.get('ocr_text', '')))
        
        return {
            "message": "Document approved and processed successfully", 
            "document_id": document_id,
            "ocr_text_length": len(processing_result.get('ocr_text', '')),
            "tags_generated": len(processing_result.get('generated_tags', []))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error during document approval", 
                    document_id=document_id,
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during document approval"
        )

@router.post("/reject-document/{document_id}")
async def reject_document(
    document_id: int, 
    admin_user: AdminUser,
    reason: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """
    Reject a document.
    Only admin users can reject documents.
    """
    
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Allow rejecting pending or approved documents
        if document.status not in ["pending", "approved"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot reject document with status '{document.status}'. Only pending or approved documents can be rejected."
            )
        
        # Update document status to rejected
        document.status = "rejected"
        document.rejected_at = func.now()
        document.rejected_by = admin_user.email
        document.rejection_reason = reason
        
        # Clear approval fields if document was previously approved
        if document.approved_at:
            document.approved_at = None
            document.approved_by = None
        
        try:
            db.commit()
            db.refresh(document)
        except Exception as db_error:
            db.rollback()
            logger.error("Database error during document rejection", error=str(db_error))
            raise HTTPException(status_code=500, detail="Failed to reject document")
        
        # Send notification email
        try:
            email_service.notify_admin_document_rejected(
                document_id=str(document_id),
                title=document.title or "Unknown",
                reason=reason or ""
            )
        except Exception as e:
            logger.warning("Failed to send rejection notification", error=str(e))
        
        # Clean any existing RAG chunks so rejected docs don't appear in AI search
        try:
            from ...database.rag_database import rag_engine
            from sqlalchemy import text
            with rag_engine.begin() as rag_conn:
                rag_conn.execute(text("DELETE FROM document_chunks WHERE document_id = :document_id"), {"document_id": document_id})
            logger.info("Removed RAG chunks for rejected document", document_id=document_id)
        except Exception as rag_err:
            logger.warning("Failed to remove RAG chunks for rejected document", document_id=document_id, error=str(rag_err))

        logger.info("Document rejected successfully", 
                   document_id=document_id,
                   rejected_by=admin_user.email,
                   reason=reason)
        
        return {"message": "Document rejected successfully", "document_id": document_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error during document rejection", 
                    document_id=document_id,
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during document rejection"
        )

@router.delete("/delete-document/{document_id}")
async def delete_document(
    document_id: int, 
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Permanently delete a document and its associated file.
    Only admin users can delete documents.
    """
    
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Store document info for logging
        document_title = document.title
        file_path = document.file_path
        
        # Delete file from S3 if it exists
        if file_path:
            try:
                s3_service.delete_file(file_path)
                logger.info("File deleted from S3", file_path=file_path)
            except Exception as e:
                logger.warning("Failed to delete file from S3", file_path=file_path, error=str(e))
                # Continue with database deletion even if S3 deletion fails
        
        # Also delete RAG vector chunks from the PostgreSQL RAG database
        try:
            from ...database.rag_database import rag_engine
            from sqlalchemy import text
            with rag_engine.begin() as rag_conn:
                rag_conn.execute(text("DELETE FROM document_chunks WHERE document_id = :document_id"), {"document_id": document_id})
            logger.info("Deleted document chunks from RAG DB", document_id=document_id)
        except Exception as rag_err:
            # Do not fail hard on RAG cleanup, but log clearly for follow-up
            logger.error("Failed to delete document chunks from RAG DB", document_id=document_id, error=str(rag_err))

        # Delete document from database
        try:
            db.delete(document)
            db.commit()
        except Exception as db_error:
            db.rollback()
            logger.error("Database error during document deletion", error=str(db_error))
            raise HTTPException(status_code=500, detail="Failed to delete document from database")
        
        logger.info("Document deleted successfully", 
                   document_id=document_id,
                   title=document_title,
                   deleted_by=admin_user.email)
        
        return {"message": "Document deleted successfully", "document_id": document_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error during document deletion", 
                    document_id=document_id,
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during document deletion"
        )

@router.get("/documents", response_model=DocumentListResponse)
async def get_documents(
    admin_user: AdminUser,
    status: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected, processed"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
    db: Session = Depends(get_db)
):
    """
    Get documents with optional status filter.
    Only admin users can access this endpoint.
    """
    
    try:
        # Build query
        query_builder = db.query(Document)
        
        # Filter by status if provided
        if status:
            query_builder = query_builder.filter(Document.status == status)
        
        # Get total count before pagination
        total_count = query_builder.count()
        
        # Order by created_at descending
        query_builder = query_builder.order_by(Document.created_at.desc())
        
        # Apply pagination
        offset = (page - 1) * per_page
        query_builder = query_builder.offset(offset).limit(per_page)
        
        # Execute query
        documents_data = query_builder.all()
        
        # Convert to response format
        documents = []
        for doc in documents_data:
            documents.append({
                "id": doc.id,
                "title": doc.title,
                "country": doc.country,
                "state": doc.state,
                "description": doc.description,
                "file_path": doc.file_path,
                "file_url": doc.file_url,
                "original_filename": doc.original_filename,
                "file_size": doc.file_size,
                "content_type": doc.content_type,
                "status": doc.status,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                "processed_at": doc.processed_at.isoformat() if doc.processed_at else None,
                "approved_at": doc.approved_at.isoformat() if doc.approved_at else None,
                "rejected_at": doc.rejected_at.isoformat() if doc.rejected_at else None,
                "approved_by": doc.approved_by,
                "rejected_by": doc.rejected_by,
                "rejection_reason": doc.rejection_reason,
                "ocr_text": doc.ocr_text,
                "generated_tags": doc.generated_tags
            })
        
        logger.info("Documents retrieved successfully", 
                   status=status,
                   results_count=len(documents),
                   page=page)
        
        return DocumentListResponse(
            documents=documents,
            total_count=total_count,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error("Error retrieving documents", status=status, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving documents"
        )

@router.get("/document/{document_id}")
async def get_document_by_id(
    document_id: int, 
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Get a specific document by ID for admin purposes.
    Only admin users can access this endpoint.
    """
    
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Convert to response format
        document_data = {
            "id": document.id,
            "title": document.title,
            "country": document.country,
            "state": document.state,
            "description": document.description,
            "file_path": document.file_path,
            "file_url": document.file_url,
            "original_filename": document.original_filename,
            "file_size": document.file_size,
            "content_type": document.content_type,
            "status": document.status,
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "updated_at": document.updated_at.isoformat() if document.updated_at else None,
            "processed_at": document.processed_at.isoformat() if document.processed_at else None,
            "approved_at": document.approved_at.isoformat() if document.approved_at else None,
            "rejected_at": document.rejected_at.isoformat() if document.rejected_at else None,
            "approved_by": document.approved_by,
            "rejected_by": document.rejected_by,
            "rejection_reason": document.rejection_reason,
            "ocr_text": document.ocr_text,
            "generated_tags": document.generated_tags,
            "ai_summary": document.ai_summary
        }
        
        logger.info("Document retrieved successfully", document_id=document_id)
        
        return document_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving document", document_id=document_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving the document"
        )

@router.get("/download/{document_id}")
async def admin_download_document(
    document_id: int, 
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Download a document file for admin review.
    Admin users can download documents regardless of status.
    """
    
    try:
        # Get document from database (no status filter for admins)
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = document.file_path
        
        if not file_path:
            raise HTTPException(status_code=400, detail="Document file not available")
        
        # Get S3 service
        from app.services.s3_service import s3_service
        
        # Generate download URL (used internally to fetch file)
        download_url = s3_service.get_download_url(file_path)
        
        if not download_url:
            raise HTTPException(status_code=500, detail="Failed to generate download URL")
        
        # Fetch file from S3 and stream it to user
        try:
            import requests
            import os
            from fastapi.responses import StreamingResponse
            
            # Get file from S3
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            # Extract filename from file_path
            filename = os.path.basename(file_path)
            
            # Determine content type based on file extension
            content_type = "application/octet-stream"  # Default
            if filename.lower().endswith('.pdf'):
                content_type = "application/pdf"
            elif filename.lower().endswith(('.jpg', '.jpeg')):
                content_type = "image/jpeg"
            elif filename.lower().endswith('.png'):
                content_type = "image/png"
            elif filename.lower().endswith('.gif'):
                content_type = "image/gif"
            elif filename.lower().endswith('.doc'):
                content_type = "application/msword"
            elif filename.lower().endswith('.docx'):
                content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif filename.lower().endswith('.xls'):
                content_type = "application/vnd.ms-excel"
            elif filename.lower().endswith('.xlsx'):
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            elif filename.lower().endswith('.txt'):
                content_type = "text/plain"
            elif filename.lower().endswith('.csv'):
                content_type = "text/csv"
            
            # Create streaming response
            def generate():
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
            
            logger.info("Admin document download completed successfully", 
                       document_id=document_id,
                       filename=filename,
                       admin_user=admin_user.email)
            
            return StreamingResponse(
                generate(),
                media_type=content_type,
                headers={
                    "Content-Disposition": f"attachment; filename=\"{filename}\"",
                    "Content-Length": str(response.headers.get("content-length", "")),
                    "Cache-Control": "private, max-age=0, no-cache, no-store, must-revalidate"
                }
            )
            
        except requests.RequestException as req_error:
            logger.error("Error fetching file from S3 for admin download", 
                        document_id=document_id, error=str(req_error))
            raise HTTPException(status_code=500, detail="Failed to fetch document file")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in admin document download", document_id=document_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An error occurred while downloading the document"
        )

@router.get("/job-status/{job_id}")
async def get_job_status(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Get processing job status by job ID."""
    job_status = queue_service.get_job_status(db, job_id)
    if not job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    queue_position = queue_service.get_queue_position(db, job_id)
    job_status['queue_position'] = queue_position
    
    return job_status

@router.get("/job-status-by-document/{document_id}")
async def get_job_status_by_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get processing job status by document ID."""
    job = queue_service.get_job_by_document_id(db, document_id)
    if not job:
        raise HTTPException(status_code=404, detail="No job found for this document")
    
    job_status = job.to_dict()
    queue_position = queue_service.get_queue_position(db, job.id)
    job_status['queue_position'] = queue_position
    
    return job_status

@router.get("/queue-stats")
async def get_queue_stats(
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """Get queue statistics (admin only)."""
    stats = queue_service.get_queue_stats(db)
    return stats

@router.get("/failed-jobs")
async def get_failed_jobs(
    admin_user: AdminUser,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get failed jobs for admin review."""
    failed_jobs = queue_service.get_failed_jobs(db, limit=limit)
    
    # Include document information
    result = []
    for job in failed_jobs:
        document = db.query(Document).filter(Document.id == job.document_id).first()
        job_dict = job.to_dict()
        if document:
            job_dict['document'] = {
                'id': document.id,
                'title': document.title,
                'country': document.country,
                'state': document.state,
                'status': document.status
            }
        result.append(job_dict)
    
    return {
        'failed_jobs': result,
        'total': len(result)
    }

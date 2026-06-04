# SPEC-002: AI Features

> **Status**: Active  
> **Last Updated**: 2026-06-04  
> **Owner**: HaqNow Engineering

## Overview

HaqNow uses multiple AI/ML systems for document processing, search, and user interaction. All AI features use privacy-first, ethical AI services.

## Feature Matrix

| Feature | Technology | Runs On | Trigger |
|---------|-----------|---------|---------|
| OCR Text Extraction | Tesseract OCR | Worker pod (local) | Document approval |
| Multilingual OCR | Tesseract + Google Translate | Worker pod (local + API) | Non-English document approval |
| Tag Generation | spaCy NLP (`en_core_web_sm`) | Worker pod (local) | After OCR extraction |
| AI Summary | Thaura AI (LLM) | Remote API | After OCR extraction |
| Semantic Embeddings | Sentence-Transformers (`all-MiniLM-L6-v2`) | Worker pod (local) | After OCR extraction |
| RAG Q&A (Global) | Thaura AI + pgvector | Remote API + DB | User query |
| RAG Q&A (Document-scoped) | Thaura AI + pgvector | Remote API + DB | User query on document page |
| Semantic Search | Sentence-Transformers | Backend pod (local) | User search query |

## OCR Text Extraction

### Standard OCR (English)
- **Library**: `pytesseract` wrapping Tesseract OCR engine
- **Pipeline**: PDF → `pdf2image` → page images → `pytesseract.image_to_string()` → combined text
- **Supported formats**: PDF, images (JPEG, PNG, GIF, BMP, TIFF, WebP), DOCX, CSV, Excel, RTF, plain text
- **Post-processing**: `clean_text()` normalizes whitespace and removes special characters

### Multilingual OCR
- **Service**: `multilingual_ocr_service`
- **Supported languages**: Arabic, French, German, Spanish, Chinese (Simplified/Traditional), Russian, Persian, Hindi, Bengali, Urdu, Japanese, Korean, Turkish, Vietnamese, Thai, Myanmar, and more
- **Pipeline**:
  1. Detect language from user-specified document language
  2. Run Tesseract with language-specific trained data
  3. Translate to English via Google Translate API
  4. Store both original and English text
- **Fallback**: If multilingual service unavailable, falls back to standard English OCR

### Text Optimization
- **Function**: `get_top_words_for_search(text, max_words=1000)`
- **Purpose**: Extract top 1000 most important words by frequency (excluding stop words)
- **Stored in**: `Document.ocr_text` (searchable subset), `Document.ocr_text_original` (full text)

## Tag Generation

### Technology
- **Library**: spaCy with `en_core_web_sm` model (~50MB)
- **Requirement**: Model must be installed in the Docker image

### Pipeline
1. Process text with spaCy NLP pipeline
2. Extract named entities (ORG, GPE, PERSON, etc.)
3. Extract meaningful nouns and proper nouns via POS tagging
4. Extract noun chunks (multi-word phrases)
5. Filter out stop words, short tags (<3 chars), and banned words
6. Count frequency and return top 50 most common tags

### Banned Word Filtering
- Banned words stored in `banned_tags` database table
- Applied to both OCR text and generated tags
- Case-insensitive word boundary matching
- Replaced with `[REDACTED]` in OCR text

### Known Issue
> **WARNING**: The `en_core_web_sm` model must be installed in the production Docker image.
> If missing, tag generation silently returns an empty array `[]`.

## AI Summary Generation

### Technology
- **Service**: `ai_summary_service`
- **LLM**: Thaura AI (ethical, privacy-first LLM)
- **API**: OpenAI-compatible endpoint at `https://backend.thaura.ai/v1`
- **Auth**: `THAURA_API_KEY` environment variable

### Pipeline
1. Take first 5000 characters of OCR text (English preferred)
2. Minimum 50 characters required
3. Call Thaura AI with streaming enabled
4. Request concise 1-paragraph summary (~200 chars max)
5. Clean `<think>` reasoning tags from response
6. Store in `Document.ai_summary`

### Configuration
```
THAURA_API_KEY=<api-key>
THAURA_BASE_URL=https://backend.thaura.ai/v1
```

## Semantic Search Embeddings

### Technology
- **Library**: `sentence-transformers`
- **Model**: `all-MiniLM-L6-v2` (~90MB, 384 dimensions)
- **Storage**: JSON-serialized in `Document.embedding` column

### Pipeline
1. Combine title + description + search_text + tags into document representation
2. Generate 384-dimensional embedding vector
3. Store as JSON array in database
4. Used for cosine similarity search during user queries

### Memory Management
- Model loaded lazily on first use
- Explicitly unloaded after embedding generation (`unload_model()`)
- Critical for 1GB memory limit in production pods

## RAG (Retrieval-Augmented Generation) System

### Architecture
```
User Question
     │
     ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ Generate     │────►│ Search       │────►│ Generate    │
│ Query        │     │ pgvector for │     │ Answer via  │
│ Embedding    │     │ Similar      │     │ Thaura AI   │
│ (local)      │     │ Chunks       │     │ (streaming) │
└─────────────┘     └──────────────┘     └─────────────┘
```

### Document Indexing
- **Chunking**: Split document into ~500-char segments with 50-char overlap
- **Storage**: `document_chunks` table in PostgreSQL with pgvector extension
- **Schema**: `(document_id, chunk_index, content, embedding, document_title, document_country)`
- **Upsert**: ON CONFLICT by `(document_id, chunk_index)` for idempotent updates

### Query Pipeline (Global)
**Endpoint**: `POST /api/rag/ask`

1. Generate embedding for user query (Sentence-Transformers)
2. Search pgvector for top 20 similar chunks across all documents
3. Fallback: keyword-based ILIKE search if semantic search yields nothing
4. Pass relevant chunks as context to Thaura AI
5. Generate concise answer (1-2 paragraphs, streaming)
6. Return answer + source document references + confidence score

### Query Pipeline (Document-scoped)
**Endpoint**: `POST /api/rag/document-question`

Same as global but restricted to chunks from a single `document_id`. Returns up to 10 chunks.

### Frontend Integration
- "Ask AI about this document" button on document detail page
- "Ask AI across all documents" on search results page
- Streaming response display with typing animation
- Source document citations with links

## Dependencies

| Component | Package | Version Constraint |
|-----------|---------|-------------------|
| OCR | pytesseract, pdf2image | Tesseract 4+ |
| NLP Tags | spacy, en_core_web_sm | spaCy 3.x |
| AI Summary | openai (Thaura-compatible) | openai >= 1.0 |
| Embeddings | sentence-transformers | Latest |
| Vector DB | pgvector | PostgreSQL 14+ |
| Translation | googletrans | Optional |

## Invariants

1. **OCR text MUST be extracted** for every processed document (even if empty string)
2. **AI summary should be generated** when OCR text >= 50 characters
3. **RAG chunks MUST be created** for every successfully processed document
4. **Tag generation requires spaCy** — returns empty array if model not installed
5. **English translation preferred** for tags and summaries (enables cross-language search)
6. **Embedding model MUST be unloaded** after use to stay within memory limits

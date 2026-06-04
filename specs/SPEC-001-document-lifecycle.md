# SPEC-001: Document Lifecycle

> **Status**: Active  
> **Last Updated**: 2026-06-04  
> **Owner**: HaqNow Engineering

## Overview

This specification describes the complete lifecycle of a document in HaqNow, from upload through public availability, including all intermediate processing steps.

## Lifecycle States

```
┌─────────┐   ┌──────────┐   ┌────────────┐   ┌───────────┐   ┌────────────┐
│ Upload  │──►│ Pending  │──►│ Approved   │──►│Processing │──►│  Live      │
└─────────┘   └──────────┘   └────────────┘   └───────────┘   └────────────┘
                   │                                               │
                   ▼                                               │
              ┌──────────┐                                         │
              │ Rejected │◄────────────────────────────────────────┘
              └──────────┘
```

### State Definitions

| State | `status` Column | Description |
|-------|----------------|-------------|
| Pending | `pending` | Uploaded by user, awaiting admin review |
| Approved | `approved` | Admin approved, processing job enqueued |
| Rejected | `rejected` | Admin rejected with optional reason |
| Processing | `approved` (with active job) | Background worker is processing |
| Live | `approved` (with `processed_at` set) | Fully processed, publicly visible |

## Upload Phase

**Endpoint**: `POST /api/file-uploader/upload`

### Steps (synchronous, in request handler):
1. **Rate limit check** — 1 upload per IP per 2 minutes (skipped for API key clients)
2. **Captcha verification** — hCaptcha validation (if configured)
3. **File size validation** — Max 100MB per file
4. **File name validation** — Filename required
5. **Language validation** — Must be one of: english, arabic, french, german, spanish, chinese, russian, other
6. **Virus scanning** — VirusTotal API scan (see [SPEC-004](SPEC-004-upload-pipeline.md))
7. **Metadata stripping** — Remove all EXIF/metadata, convert to clean PDF
8. **S3 upload** — Upload clean PDF to Exoscale S3
9. **Database entry** — Create `Document` record with `status=pending`
10. **Email notification** — Notify configured admin recipients

### Multi-file Upload
**Endpoint**: `POST /api/file-uploader/upload-multiple`
- Max 10 files per batch
- Each file processed individually (virus scan, metadata strip)
- Single rate limit check for the batch
- Titles appended with "- Part N" for multiple files

## Approval Phase

**Endpoint**: `POST /api/document-processing/approve-document/{id}`  
**Auth**: Admin only (JWT)

### Steps:
1. Validate document exists and is in `pending` or `rejected` status
2. Enqueue a `process_document` job via `QueueService`
3. Set `status=approved`, `approved_at`, `approved_by`
4. Clear any rejection fields if previously rejected
5. Send approval notification email

## Processing Phase (Background Worker)

**Component**: `worker.py` running in dedicated Kubernetes pod

### Job Queue System

The queue is backed by the `job_queue` database table:

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Primary key |
| `document_id` | int | FK to documents |
| `job_type` | str | Always `process_document` |
| `status` | str | `pending`, `processing`, `completed`, `failed` |
| `priority` | int | Higher = processed first (default 0 = FIFO) |
| `retry_count` | int | Current retry count |
| `max_retries` | int | Default 3 |
| `progress_percent` | int | 0-100 |
| `current_step` | str | Human-readable step description |
| `error_message` | str | Error details on failure |

### Processing Steps:
1. **Download file** from S3 (10% progress)
2. **OCR extraction** (30% progress)
   - English: Tesseract OCR
   - Multilingual: Tesseract + Google Translate to English
3. **Banned word filtering** — Replace banned words with `[REDACTED]`
4. **Search text optimization** — Extract top 1000 important words
5. **Tag generation** (80% progress) — spaCy NLP entity extraction
6. **AI Summary** — Thaura AI generates 1-paragraph summary
7. **Semantic embedding** — Sentence-transformers generates 384-dim vector
8. **Database update** — Store `ocr_text`, `generated_tags`, `ai_summary`, `search_text`, `embedding`
9. **RAG indexing** — Chunk document and store with embeddings in pgvector

### Stale Job Recovery

**Critical**: When the worker pod is killed during processing (deployment, OOM, liveness probe), jobs get stuck in `processing` status forever.

**Recovery mechanism**:
- On worker startup: Reset any `processing` jobs older than 10 minutes to `pending`
- Periodic check: Every 5 minutes during main loop
- Method: `QueueService.recover_stale_jobs(db, timeout_minutes=10)`

### Retry Logic
- Failed jobs retry up to `max_retries` (default 3) times
- On retry, status reset to `pending`, progress reset to 0
- After max retries, status set to `failed` with error message

## RAG Indexing Phase

After successful document processing, the worker triggers RAG indexing:

1. Combine title + description + OCR text
2. Chunk into ~500-character segments with 50-char overlap
3. Generate embeddings for each chunk (Sentence-Transformers, 384-dim)
4. Store chunks + embeddings in PostgreSQL with pgvector extension
5. Enables document-scoped AI Q&A and global cross-document search

## Document Model

Key fields in the `documents` table:

| Field | Type | Purpose |
|-------|------|---------|
| `ocr_text` | MEDIUMTEXT | Top 1000 searchable words from OCR |
| `ocr_text_original` | TEXT | Full OCR text in original language |
| `ocr_text_english` | TEXT | English translation (if applicable) |
| `generated_tags` | JSON | Array of NLP-extracted tags |
| `search_text` | MEDIUMTEXT | Combined text for full-text search |
| `embedding` | JSON | 384-dim semantic search vector |
| `ai_summary` | TEXT | AI-generated 1-paragraph summary |
| `processed_at` | DATETIME | When processing completed |
| `approved_at` | DATETIME | When admin approved |
| `approved_by` | VARCHAR | Admin email who approved |

## Invariants

1. **Every approved document MUST have a job in the queue** (or already completed)
2. **No job should stay in `processing` for more than 10 minutes** without recovery
3. **After successful processing**: `ocr_text`, `search_text`, and `processed_at` MUST be populated
4. **RAG chunks MUST exist** for every successfully processed document
5. **Document status MUST NOT change** from `approved` during processing

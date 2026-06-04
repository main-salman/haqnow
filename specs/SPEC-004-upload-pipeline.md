# SPEC-004: Upload Pipeline

> **Status**: Active  
> **Last Updated**: 2026-06-04  
> **Owner**: HaqNow Engineering

## Overview

The upload pipeline handles secure, anonymous document submission with virus scanning, metadata removal, and PDF conversion. Privacy and security are the top priorities.

## Upload Flow

```
Client (Browser)
     │
     ▼ POST /api/file-uploader/upload (multipart/form-data)
     │
┌────┴──────────────────────────────────────────────────┐
│                  Upload Handler                        │
│                                                        │
│  1. Rate Limit Check ──► 429 if exceeded              │
│  2. Captcha Verify ──► 400 if failed                  │
│  3. File Size Check ──► 413 if > 100MB                │
│  4. Filename Validate ──► 400 if missing              │
│  5. Language Validate ──► default to 'english'        │
│  6. Virus Scan (VirusTotal) ──► 400 if infected       │
│  7. Metadata Strip + PDF Convert ──► 500 if failed    │
│  8. Upload to S3 ──► 500 if failed                    │
│  9. Create DB Entry (status=pending)                  │
│ 10. Send Email Notification                           │
│ 11. Return success + document_id                      │
│                                                        │
└───────────────────────────────────────────────────────┘
```

## Request Format

### Single File Upload
```
POST /api/file-uploader/upload
Content-Type: multipart/form-data

file: <binary>           # Required
title: string            # Required
country: string          # Required  
state: string            # Required
document_language: string # Optional (default: "english")
description: string      # Optional
captcha_token: string    # Optional (required if hCaptcha configured)
```

### Multi-file Upload
```
POST /api/file-uploader/upload-multiple
Content-Type: multipart/form-data

files: <binary[]>        # Required (1-10 files)
title: string            # Required (suffixed with "- Part N")
country: string          # Required
state: string            # Required
document_language: string # Optional
description: string      # Optional
captcha_token: string    # Optional
```

## Rate Limiting

| Scope | Limit | Window |
|-------|-------|--------|
| Upload (per IP) | 1 upload | 2 minutes |
| API key clients | Unlimited | N/A |

- Identified by client IP address
- Configurable via `UPLOAD_TIMEOUT_SECONDS` env var (default: 120)
- Status endpoint: `GET /api/file-uploader/rate-limit-status`

## Captcha Verification

- **Provider**: hCaptcha
- **Config**: `HCAPTCHA_SECRET_KEY` environment variable
- **Behavior**: 
  - If key configured: Captcha required for web uploads
  - If key not configured: Captcha skipped (frontend validation only)
  - API key clients: Captcha always skipped

## File Validation

### Size Limits

| Layer | Limit | Error |
|-------|-------|-------|
| Deflect CDN | Configured in dashboard | 413 |
| Nginx Ingress | 50MB (`proxy-body-size`) | 413 |
| Frontend Nginx | 50MB (`client_max_body_size`) | 413 |
| Backend code | 100MB | HTTP 413 |

> **NOTE**: The effective limit is the smallest: 50MB from ingress/nginx config.
> Backend allows 100MB to support future ingress limit increases.

### Accepted Formats
- PDF (`.pdf`)
- Word documents (`.doc`, `.docx`)
- Images: JPEG, PNG, GIF, BMP, TIFF, WebP
- Max file size: 50MB (infrastructure) / 100MB (application)

## Virus Scanning

### Service: VirusTotal API v3

**Pipeline**:
1. Calculate SHA-256 hash of uploaded file
2. Check if hash already exists in VirusTotal database (cached scan)
3. If not cached: Upload file to VirusTotal for scanning
4. Poll analysis results (max 60 seconds, 2-second intervals)
5. Parse results from 70+ antivirus engines
6. Reject if any engine flags as malicious or suspicious

**Rate limits**: 500 scans/day, 4 requests/minute (free tier)

**Failure behavior**:
- If VirusTotal API key not configured: Allow upload (log warning)
- If scan fails/times out: Reject upload (fail safe)
- If virus detected: Reject with virus name in error message

## Metadata Stripping

### Service: `metadata_service`

**Purpose**: Remove all identifiable metadata from uploaded files for privacy protection.

**Pipeline**:
1. **Detect file type** from content type and extension
2. **Process based on type**:
   - **PDF**: Remove metadata, flatten form fields, strip embedded files
   - **Images**: Remove EXIF data (camera, GPS, timestamps), convert to PDF
   - **DOCX**: Extract text, convert to clean PDF
   - **Other**: Convert to clean PDF
3. **Output**: Always a clean PDF with:
   - No original metadata
   - No embedded fonts that could identify origin
   - Randomized filename with timestamp
   - Only content text/images preserved

### Clean Filename Format
```
{sanitized_title}_{timestamp}.pdf
```

## S3 Storage

### Configuration
- **Provider**: Exoscale Object Storage (S3-compatible)
- **Region**: `ch-dk-2` (Switzerland)
- **Bucket**: Configured via `S3_BUCKET_NAME`

### Upload
- Content type: Always `application/pdf` (after conversion)
- Path format: Generated by S3 service
- Public URL: Direct S3 URL returned to client

## Response Format

### Single Upload Success (HTTP 200)
```json
{
  "file_url": "https://sos-ch-dk-2.exo.io/...",
  "file_path": "documents/...",
  "message": "File uploaded successfully...",
  "document_id": 140,
  "job_id": null
}
```

### Multi Upload Success (HTTP 200)
```json
{
  "uploaded_files": [...],
  "total_count": 3,
  "success_count": 2,
  "failed_count": 1,
  "message": "Uploaded 2 of 3 files successfully"
}
```

### Error Responses

| Status | Cause |
|--------|-------|
| 400 | Virus detected, captcha failed, missing filename |
| 413 | File too large |
| 429 | Rate limited |
| 500 | S3 upload failed, metadata stripping failed, DB error |
| 502 | Backend timeout (proxy timeout < processing time) |

## Infrastructure Timeout Chain

For a file upload to succeed, ALL timeouts in the chain must be long enough:

```
Deflect CDN ──► Nginx Ingress (300s) ──► Frontend Nginx ──► Backend Uvicorn
                     │                        │                    │
             proxy-read-timeout=300   client_max_body_size=50M   100MB code limit
             proxy-send-timeout=300
             proxy-body-size=50m
```

> **CRITICAL**: The Kubernetes liveness probe (`failureThreshold=18`, `period=10s` = 3 min)
> must tolerate the backend being unresponsive during synchronous virus scanning + metadata
> stripping. With 1 uvicorn worker, these blocking operations prevent health check responses.

## Privacy Guarantees

1. **No IP logging**: Upload IP is never stored in the database
2. **Metadata stripped**: All EXIF, GPS, camera, and document metadata removed
3. **Clean PDF**: Original file format not preserved (always converted)
4. **Anonymous upload**: No account required
5. **Zero-knowledge**: Server cannot determine who uploaded what

## Invariants

1. **Every uploaded file MUST be virus-scanned** (unless API key not configured)
2. **Every uploaded file MUST have metadata stripped** before storage
3. **Original files MUST NEVER be stored** — only clean PDFs
4. **Upload MUST create a database entry** with `status=pending`
5. **Rate limiting MUST be enforced** for anonymous/web clients
6. **Proxy timeouts MUST be >= 300s** to prevent 502 during processing

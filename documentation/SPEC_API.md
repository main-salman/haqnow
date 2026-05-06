# 📡 API Specification

**Complete REST API reference for the HaqNow platform.**

> **Base URLs**:
> - Production: `https://www.haqnow.com/api`
> - Development: `https://haqnow.click/api`
> - Local: `http://localhost:8000/api`
> - OpenAPI Docs: `{base}/docs`

---

## 🔐 Authentication

### Methods

| Method | Header | Usage |
|--------|--------|-------|
| **JWT Token** | `Authorization: Bearer <token>` | Admin session management |
| **OTP** | POST `/auth/verify-otp` | Passwordless admin login |
| **API Key** | `X-API-Key: <key>` | Programmatic server-to-server access |
| **Anonymous** | (none) | Public endpoints (upload, search, view) |

### Auth Flow
```
1. Admin requests OTP → POST /auth/request-otp { email }
2. OTP sent to admin email (or returned in dev)
3. Admin verifies OTP → POST /auth/verify-otp { email, otp_code }
4. JWT token returned → use in Authorization header
5. Token refresh as needed
```

---

## 📂 Endpoint Reference

### 🔓 Public Endpoints (No Auth Required)

#### Health & Status
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Backend health check |
| `GET` | `/rag/status` | AI/RAG system status |

#### File Upload
| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/file-uploader/upload` | Anonymous document upload |

**Upload Request** (multipart/form-data):
```
file: <binary>
title: string
description: string (optional)
country: string (ISO code)
tags: string (comma-separated)
language: string (ISO code, optional — auto-detected)
```

**Rate Limiting**: Anonymous time-bucket system (no IP tracking)

#### Search & Discovery
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/search/search` | Full-text document search |
| `GET` | `/search/document/{id}` | Get document details |
| `GET` | `/search/download/{id}` | Download document file |
| `GET` | `/search/countries` | List countries with documents |
| `GET` | `/search/statistics` | Platform statistics |

**Search Parameters**:
```
q: string          — Search query
country: string    — Filter by country code
language: string   — Filter by language
page: int          — Page number (default: 1)
per_page: int      — Results per page (default: 20)
sort: string       — Sort order (newest, oldest, relevant)
```

#### AI Q&A (RAG)
| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/rag/question` | Ask a natural language question |
| `GET` | `/rag/analytics` | RAG usage analytics |

**Question Request**:
```json
{
  "question": "What corruption cases involve Brazil?",
  "max_sources": 5
}
```

**Question Response**:
```json
{
  "answer": "Based on the available documents...",
  "confidence": 0.85,
  "sources": [
    {
      "document_id": 42,
      "title": "Brazil Infrastructure Fraud",
      "relevance_score": 0.92,
      "chunk_text": "..."
    }
  ],
  "processing_time_ms": 1200
}
```

#### Comments
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/comments/document/{id}` | Get comments for a document |
| `POST` | `/comments/document/{id}` | Add anonymous comment |

#### Translations
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/translations/{language}` | Get UI translations for language |

#### Site Settings
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/site-settings/announcement` | Get active announcement banner |

#### Statistics
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/statistics/word-cloud` | Word frequency data |
| `GET` | `/statistics/countries` | Country distribution data |

---

### 🔒 Admin Endpoints (JWT Required)

#### Authentication
| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/auth/request-otp` | Request OTP code for admin login |
| `POST` | `/auth/verify-otp` | Verify OTP and get JWT token |
| `GET` | `/auth/me` | Get current admin profile |

#### Document Management
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/admin-management/documents` | List all documents (pending/approved/rejected) |
| `PUT` | `/admin-management/documents/{id}/approve` | Approve a document |
| `PUT` | `/admin-management/documents/{id}/reject` | Reject a document |
| `DELETE` | `/admin-management/documents/{id}` | Delete a document |

#### Translation Management
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/translations/admin/all` | Get all translation keys |
| `PUT` | `/translations/admin/update` | Update translation values |

#### RAG Administration
| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/rag/process-all-documents` | Process/re-process all documents for AI |
| `POST` | `/rag/process-document/{id}` | Process specific document |

#### API Key Management
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/admin-management/api-keys` | List API keys |
| `POST` | `/admin-management/api-keys` | Create new API key |
| `DELETE` | `/admin-management/api-keys/{id}` | Revoke API key |

#### Site Settings
| Method | Path | Purpose |
|--------|------|---------|
| `PUT` | `/site-settings/announcement` | Update announcement banner |

#### Analytics
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/analytics/dashboard` | Admin analytics dashboard data |

---

### 🔑 API Key Endpoints (X-API-Key Required)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/file-uploader/upload` | Programmatic document upload |
| `GET` | `/search/download/{id}` | Programmatic document download |

API keys bypass anonymous rate limits but are tracked for usage auditing.

---

## ⚠️ Error Handling

### Standard Error Response
```json
{
  "detail": "Human-readable error message",
  "status_code": 400
}
```

### HTTP Status Codes

| Code | Usage |
|------|-------|
| `200` | Success |
| `201` | Created (uploads, new records) |
| `400` | Bad request (validation errors) |
| `401` | Unauthorized (missing/invalid auth) |
| `403` | Forbidden (insufficient permissions) |
| `404` | Not found |
| `429` | Rate limited |
| `500` | Internal server error |

---

## 🚦 Rate Limiting

| Endpoint Category | Limit | Method |
|-------------------|-------|--------|
| Document upload | Time-bucket (anonymous) | No IP tracking |
| Search queries | Generous (public) | Time-bucket |
| RAG questions | Moderate | Time-bucket |
| Comments | Strict | Per-document rate limit |
| Admin endpoints | No limit (authenticated) | JWT required |
| API key endpoints | Higher limits | Per-key tracking |

---

## 🔧 Development Testing

```bash
# Health check
curl -s http://localhost:8000/api/health | jq

# Upload a document
curl -X POST http://localhost:8000/api/file-uploader/upload \
  -F "file=@document.pdf" \
  -F "title=Test Document" \
  -F "country=US"

# Search
curl -s "http://localhost:8000/api/search/search?q=corruption&page=1" | jq

# AI question
curl -s -X POST http://localhost:8000/api/rag/question \
  -H "Content-Type: application/json" \
  -d '{"question": "What fraud cases are documented?"}' | jq

# Admin login
curl -s -X POST http://localhost:8000/api/auth/request-otp \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@haqnow.com"}'
```

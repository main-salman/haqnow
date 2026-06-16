# Traceability Matrix

> **Last Updated**: 2026-06-16
> **Purpose**: Maps specifications → implementation → tests to ensure full coverage

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Fully implemented and tested |
| ⚠️ | Implemented, tests incomplete |
| 🔲 | Specified, not yet implemented |
| ❌ | Missing or out of compliance |

---

## SPEC-001: Document Lifecycle

| Requirement | Implementation | Test | Status |
|-------------|---------------|------|--------|
| Upload rate limiting (1/2min) | `backend/app/apis/file_uploader.py` | TBD | ⚠️ |
| hCaptcha verification | `backend/app/apis/file_uploader.py` | TBD | ⚠️ |
| File size validation (100MB) | `backend/app/apis/file_uploader.py` | TBD | ⚠️ |
| Language validation | `backend/app/apis/file_uploader.py` | TBD | ⚠️ |
| Virus scanning (VirusTotal) | `backend/app/services/virus_scan_service.py` | TBD | ⚠️ |
| Metadata stripping | `backend/app/apis/file_uploader.py` | TBD | ⚠️ |
| S3 upload | `backend/app/apis/file_uploader.py` | TBD | ⚠️ |
| Admin approval workflow | `backend/app/apis/document_processing.py` | TBD | ⚠️ |
| Background processing (worker) | `backend/worker.py` | TBD | ⚠️ |
| Stale job recovery | `backend/app/services/queue_service.py` | TBD | ⚠️ |
| RAG indexing | `backend/app/services/rag_service.py` | TBD | ⚠️ |
| INV-1: Approved docs have jobs | `backend/app/apis/document_processing.py` | TBD | ⚠️ |
| INV-2: No stale processing > 10min | `backend/app/services/queue_service.py` | TBD | ⚠️ |

---

## SPEC-002: AI Features

| Requirement | Implementation | Test | Status |
|-------------|---------------|------|--------|
| RAG document chunking | `backend/app/services/rag_service.py` | TBD | ⚠️ |
| Semantic search (pgvector) | `backend/app/database/rag_database.py` | TBD | ⚠️ |
| Thaura.AI answer generation | `backend/app/services/rag_service.py` | TBD | ⚠️ |
| Embedding generation (sentence-transformers) | `backend/app/services/rag_service.py` | TBD | ⚠️ |
| Source attribution | `backend/app/services/rag_service.py` | TBD | ⚠️ |

---

## SPEC-003: Infrastructure

| Requirement | Implementation | Test | Status |
|-------------|---------------|------|--------|
| K8s namespace separation | `k8s/manifests/` | Manual | ⚠️ |
| Rolling deployments | `scripts/deploy.sh` | Manual | ⚠️ |
| Resource limits | `k8s/manifests/*.yaml` | Manual | ⚠️ |
| Health checks | `backend/main.py` | TBD | ⚠️ |
| HTTPS everywhere | `k8s/manifests/ingress.yaml` | Manual | ⚠️ |

---

## SPEC-004: Upload Pipeline

| Requirement | Implementation | Test | Status |
|-------------|---------------|------|--------|
| Multi-file upload (max 10) | `backend/app/apis/file_uploader.py` | TBD | ⚠️ |
| VirusTotal integration | `backend/app/services/virus_scan_service.py` | TBD | ⚠️ |
| EXIF metadata stripping | `backend/app/apis/file_uploader.py` | TBD | ⚠️ |
| File type validation | `backend/app/apis/file_uploader.py` | TBD | ⚠️ |
| Email notification on upload | `backend/app/services/email_service.py` | TBD | ⚠️ |

---

## CONSTITUTION.md: Privacy Mandates

| Mandate | Implementation | Test | Status |
|---------|---------------|------|--------|
| No IP logging | All services | TBD | ⚠️ |
| Anonymous uploads | `backend/app/apis/file_uploader.py` | TBD | ⚠️ |
| Metadata stripping | Upload pipeline | TBD | ⚠️ |
| Security headers | `backend/app/middleware/security_headers.py` | TBD | ⚠️ |
| Rate limiting (no IP tracking) | Rate limiter middleware | TBD | ⚠️ |

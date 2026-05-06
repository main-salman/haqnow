# 🧠 AI Assistant Skills Reference

**What the AI assistant can do for HaqNow** — structured skill inventory with context, files, and examples.

> **Read CURSOR_CONTEXT.md first** for file locations and deployment rules.

---

## 🏗️ Backend Development

### FastAPI Endpoint Creation
**Capability**: Create, modify, and debug FastAPI REST endpoints with proper routing, validation, and error handling.

| Item | Detail |
|------|--------|
| **Framework** | FastAPI with Pydantic models, async/await |
| **ORM** | SQLAlchemy with MySQL (primary) and PostgreSQL (RAG) |
| **Auth** | JWT tokens, OTP passwordless login, API key validation |
| **Key Files** | `backend/main.py`, `backend/app/apis/` |

```bash
# Test any endpoint locally
curl -s http://localhost:8000/docs    # OpenAPI docs
curl -s http://localhost:8000/api/health
```

### Service Layer Development
**Capability**: Build and extend backend services (RAG, OCR, email, caching, virus scanning, etc.).

| Service | File | Purpose |
|---------|------|---------|
| RAG/AI | `backend/app/services/rag_service.py` | Thaura.AI + sentence-transformers pipeline |
| OCR | `backend/app/services/multilingual_ocr_service.py` | Tesseract 60+ languages |
| Arabic OCR | `backend/app/services/arabic_ocr_service.py` | Specialized Arabic text extraction |
| Email | `backend/app/services/email_service.py` | SendGrid email delivery |
| Cache | `backend/app/services/cache_service.py` | Application-level caching |
| S3 Storage | `backend/app/services/s3_service.py` | Exoscale SOS object storage |
| OTP Auth | `backend/app/services/otp_service.py` | MySQL-backed OTP codes |
| Virus Scan | `backend/app/services/virus_scanning_service.py` | VirusTotal file scanning |
| Queue | `backend/app/services/queue_service.py` | Background job processing |
| AI Summary | `backend/app/services/ai_summary_service.py` | Document auto-summarization |
| Spam Filter | `backend/app/services/spam_filter_service.py` | Content spam detection |
| Metadata | `backend/app/services/metadata_service.py` | Document metadata extraction/stripping |
| View Track | `backend/app/services/view_tracking_service.py` | Document view analytics |
| Rate Limit | `backend/app/services/comment_rate_limit_service.py` | Comment rate limiting |

### Database Operations
**Capability**: Write migrations, queries, and manage both MySQL and PostgreSQL databases.

```bash
# MySQL (Primary) — documents, users, translations, OTP, API keys
DATABASE_URL=mysql+pymysql://...    # in .env

# PostgreSQL (RAG) — vector embeddings, document chunks, query logs
POSTGRES_RAG_URI=postgresql://...   # in .env
```

| Operation | Approach |
|-----------|----------|
| Schema changes | Create migration script in `backend/` (e.g., `create_rag_tables.py`) |
| Vector operations | Use pgvector extension (768-dim, cosine similarity) |
| ORM models | SQLAlchemy models in `backend/app/` |
| Connection management | Connection pooling via SQLAlchemy engine |

### Background Worker
**Capability**: Manage and extend the worker pod for document processing jobs.

| Item | Detail |
|------|--------|
| **Entry point** | `backend/worker.py` |
| **Tasks** | OCR processing, translation, RAG embedding, AI summarization |
| **Queue** | MySQL-backed job queue (`backend/app/services/queue_service.py`) |
| **K8s** | 1 dedicated worker pod (shared across dev/prod) |

---

## 🎨 Frontend Development

### React Component Development
**Capability**: Build and modify React 18 + TypeScript components with shadcn/ui.

| Item | Detail |
|------|--------|
| **Framework** | React 18, TypeScript, Vite |
| **UI Library** | shadcn/ui + Tailwind CSS |
| **Key Dir** | `frontend/src/components/` |
| **Pages** | `frontend/src/pages/` |
| **Routing** | `frontend/src/user-routes.tsx`, `frontend/src/router.tsx` |

### Internationalization (i18n)
**Capability**: Add and modify translations across 7 supported languages.

| Language | Code |
|----------|------|
| English | `en` |
| Arabic | `ar` |
| French | `fr` |
| German | `de` |
| Russian | `ru` |
| Polish | `pl` |
| Turkish | `tr` |

**Key Dir**: `frontend/src/i18n/`

### Build & Optimization
**Capability**: Vite build configuration, code splitting, asset optimization.

```bash
# Local development
cd frontend && npm run dev         # http://localhost:5173

# Production build (handled by deploy.sh)
cd frontend && npm run build       # outputs to frontend/dist/
```

---

## ☸️ Infrastructure & DevOps

### Kubernetes Management
**Capability**: Manage Exoscale SKS cluster — pods, deployments, services, secrets, CronJobs.

```bash
export KUBECONFIG=k8s/.kubeconfig

# Pod inspection
kubectl get pods -n haqnow            # Production
kubectl get pods -n haqnow-dev        # Development

# Logs
kubectl logs -n haqnow -l app=backend-api --tail=100

# Rolling restart
kubectl rollout restart deployment/backend-api -n haqnow

# Secrets management
kubectl get secrets -n haqnow
```

| Manifest | Location |
|----------|----------|
| Production | `k8s/manifests/` |
| Development | `k8s/manifests/dev/` |
| Secrets (prod) | `k8s/scripts/create-secrets.sh` |
| Secrets (dev) | `k8s/scripts/create-secrets-dev.sh` |
| Backup CronJob | `k8s/manifests/backup-cronjob.yaml` |

### Docker Image Management
**Capability**: Build, tag, and push container images to GHCR.

| Image | Dockerfile | Purpose |
|-------|-----------|---------|
| `backend-api` | `backend/Dockerfile` | FastAPI application |
| `worker` | `backend/Dockerfile.worker` | Background processor |
| `frontend` | `frontend/Dockerfile` | React app via nginx |
| `backup` | `backend/Dockerfile.backup` | DR backup jobs |

**Registry**: `ghcr.io/main-salman/`

### Deployment
**Capability**: Execute deployments via `scripts/deploy.sh` — the **only** deployment method.

```bash
# Development (main branch → haqnow.click)
./scripts/deploy.sh --env=dev patch

# Production (prod branch → haqnow.com)
./scripts/deploy.sh --env=prod patch   # bug fix
./scripts/deploy.sh --env=prod minor   # feature
./scripts/deploy.sh --env=prod major   # breaking
```

### Terraform IaC
**Capability**: Manage infrastructure as code for Exoscale resources.

| Directory | Purpose |
|-----------|---------|
| `terraform/` | Full infrastructure provisioning |
| `terraform_rag_only/` | RAG-specific PostgreSQL resources |

### Local Development
**Capability**: Set up and manage local dev environment.

```bash
./scripts/run-local.sh       # Start all services locally
./scripts/stop-local.sh      # Stop local services
./scripts/update-local.sh    # Update local environment
make install                 # Install all dependencies
```

---

## 🤖 AI/RAG Operations

### RAG Pipeline Management
**Capability**: Manage the full Retrieval-Augmented Generation pipeline.

```
Document → Chunking (500 chars) → Embedding (sentence-transformers, 768-dim)
    → Vector Storage (pgvector) → Similarity Search → LLM (Thaura.AI) → Response
```

| Component | Technology | Key File |
|-----------|-----------|----------|
| LLM | Thaura.AI (ethical, privacy-first) | `backend/app/services/rag_service.py` |
| Embeddings | sentence-transformers (`all-mpnet-base-v2`) | Local, 768-dim vectors |
| Vector DB | PostgreSQL + pgvector | `backend/app/database/rag_database.py` |
| Frontend | AI Q&A tab | `frontend/src/components/RAGQuestionAnswering.tsx` |

```bash
# Check RAG system status
curl -s "https://www.haqnow.com/api/rag/status" | jq

# Test AI search
curl -s -X POST "https://www.haqnow.com/api/rag/question" \
  -H "Content-Type: application/json" \
  -d '{"question": "test query"}'

# Reprocess all documents
curl -s -X POST "https://www.haqnow.com/api/rag/process-all-documents"
```

### Embedding Operations
**Capability**: Generate, migrate, and manage document embeddings.

| Script | Purpose |
|--------|---------|
| `scripts/reembed_all.py` | Re-embed all documents |
| `backend/migrate_to_sentence_transformers.py` | Migrate embedding models |
| `backend/migrate_to_openai_embeddings.py` | Migrate to OpenAI embeddings |

---

## 🔒 Security & Privacy

### Security Operations
**Capability**: Audit, configure, and maintain security posture.

| Area | Approach |
|------|----------|
| Penetration testing | Nuclei scanner (`documentation/penetration-testing.md`) |
| Security headers | Nginx + FastAPI middleware (`backend/app/middleware/security_headers.py`) |
| Virus scanning | VirusTotal API integration |
| Rate limiting | Anonymous time-bucket system |
| CORS | FastAPI CORS middleware |

### Privacy Compliance
**Capability**: Maintain privacy-first architecture.

| Principle | Implementation |
|-----------|----------------|
| No IP logging | All logs exclude IP addresses |
| Anonymous uploads | No user identification required |
| Metadata stripping | `metadata_service.py` removes identifying data |
| Ethical AI | Thaura.AI — privacy-first LLM |
| GDPR compliance | No cookies, no tracking, anonymous rate limiting |

---

## 🔍 Debugging & Troubleshooting

### Health Checks
```bash
curl -s "https://www.haqnow.com/api/health"         # Backend health
curl -s "https://www.haqnow.com/api/rag/status" | jq # AI system status
```

### Log Analysis
```bash
# Production logs
kubectl logs -n haqnow -l app=backend-api --tail=100

# Development logs
kubectl logs -n haqnow-dev -l app=backend-api --tail=100

# Worker logs
kubectl logs -n haqnow -l app=worker --tail=100
```

### Database Debugging
```bash
# Check MySQL connection
python -c "from backend.app.database.database import engine; print(engine.url)"

# Check PostgreSQL/RAG connection
python -c "from backend.app.database.rag_database import rag_engine; print(rag_engine.url)"
```

---

## 📊 Analytics & Monitoring

### Umami Analytics
**Capability**: Self-hosted, privacy-focused visitor analytics.

| Item | Detail |
|------|--------|
| **Dashboard** | https://analytics.haqnow.com |
| **Tracking script** | `frontend/index.html` |
| **Setup** | `scripts/setup-umami.sh` |
| **Config** | `UMAMI_WEBSITE_ID` in `.env` |

### Admin Analytics Dashboard
**Capability**: Built-in platform metrics at `/admin-analytics-page`.

---

## 📝 Documentation Management

### Existing Documentation
| File | Purpose |
|------|---------|
| `CURSOR_CONTEXT.md` | AI assistant quick reference |
| `.cursorrules` | Cursor AI behavior rules |
| `README.md` | Project overview |
| `documentation/ARCHITECTURE.md` | System architecture |
| `documentation/DEBUGGING_GUIDE.md` | Troubleshooting |
| `documentation/DEPLOYMENT_CHECKLIST.md` | Deployment verification |
| `documentation/DISASTER_RECOVERY.md` | DR runbook |
| `documentation/TEAM_ONBOARDING.md` | New member guide |
| `documentation/MIGRATION_GUIDE.md` | Migration procedures |
| `documentation/penetration-testing.md` | Security audit report |

---

## 🎯 Skill Priority Rules

1. **Always read CURSOR_CONTEXT.md first** before exercising any skill
2. **Always use deploy.sh** — never perform manual deployment steps
3. **Never hardcode credentials** — all secrets live in `.env`
4. **Privacy first** — never add IP logging, tracking, or user identification
5. **Test locally** before deploying (`./scripts/run-local.sh`)
6. **Check documentation/** before deep-diving into code
7. **Reference existing services** before creating new ones

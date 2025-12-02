# 🏗️ HaqNow Architecture Reference

**Quick architecture reference to understand system components and data flow.**

## 🗂️ **System Overview**

```
┌─ Frontend (React) ──── Port 80/443 ──── nginx (K8s pod)
├─ Backend (FastAPI) ─── Port 8000 ───── Python (2 K8s pods)
├─ Worker (Python) ───── Background ──── Document processing (1 K8s pod)
├─ AI/RAG (Thaura.AI) ── HTTPS ──────── Ethical LLM (privacy-first)
├─ Embeddings (Local) ── sentence-transformers ─ Local (768-dim)
├─ MySQL Database ────── Port 21699 ──── Exoscale DBaaS
├─ PostgreSQL RAG ───── Port 21699 ──── Exoscale DBaaS  
├─ S3 Storage ────────── HTTPS ─────── Exoscale SOS
└─ Analytics ─────────── HTTPS ─────── Umami (self-hosted)
```

## 💾 **Database Architecture**

### **Primary MySQL Database (Exoscale)**
- **Purpose**: Main application data
- **Tables**: documents, admins, translations, statistics, otp_codes, api_keys
- **Connection**: `DATABASE_URL` in .env
- **Location**: Exoscale DBaaS (managed service)

### **RAG PostgreSQL Database (Exoscale)**  
- **Purpose**: AI/vector operations
- **Tables**: document_chunks (with embeddings), rag_queries
- **Connection**: `POSTGRES_RAG_URI` in .env
- **Extension**: pgvector for similarity search (768-dim vectors)
- **Location**: Exoscale DBaaS (managed service)

## 🤖 **AI/RAG Pipeline**

### **Processing Flow**
```
Document Upload → Admin Approval → OCR Text Extraction
     ↓
Document Chunking (500 chars) → Local Embedding (sentence-transformers, 768-dim)
     ↓  
Vector Storage (PostgreSQL) → Index Building (pgvector)
     ↓
Ready for AI Q&A Search
```

### **Query Flow**
```
User Question → Local Embedding (sentence-transformers) → Vector Similarity (pgvector)
     ↓
Context Retrieval (top chunks) → LLM Processing (Thaura.AI - ethical, privacy-first)
     ↓
Answer + Sources + Confidence Score → User Response
```

### **AI Stack Components**
- **Thaura.AI**: Ethical, privacy-first LLM for answer generation
- **sentence-transformers**: Local embeddings (`all-mpnet-base-v2`, 768-dim)
- **pgvector**: PostgreSQL extension for vector similarity search
- **FastAPI RAG Service**: Orchestrates the entire pipeline

## ☸️ **Kubernetes Architecture (Exoscale SKS)**

### **Branch & Environment Strategy**
- **`main` branch** → Development (https://haqnow.click) → `haqnow-dev` namespace
- **`prod` branch** → Production (https://www.haqnow.com) → `haqnow` namespace

### **Cluster Components**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Exoscale SKS Cluster                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────┐  │
│  │  Namespace: haqnow (PROD)       │  │  Namespace: haqnow-dev      │  │
│  │  Domain: haqnow.com             │  │  Domain: haqnow.click       │  │
│  │                                 │  │                             │  │
│  │  ┌────────────┐ ┌────────────┐  │  │  ┌────────────┐             │  │
│  │  │backend-api │ │backend-api │  │  │  │backend-api │             │  │
│  │  │  Pod #1    │ │  Pod #2    │  │  │  │   Pod      │             │  │
│  │  └────────────┘ └────────────┘  │  │  └────────────┘             │  │
│  │                                 │  │                             │  │
│  │  ┌────────────┐ ┌────────────┐  │  │  ┌────────────┐             │  │
│  │  │  frontend  │ │   worker   │  │  │  │  frontend  │             │  │
│  │  │    Pod     │ │    Pod     │  │  │  │    Pod     │             │  │
│  │  └────────────┘ └────────────┘  │  │  └────────────┘             │  │
│  └─────────────────────────────────┘  └─────────────────────────────┘  │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐     │
│  │                   Network Load Balancer (NLB)                 │     │
│  │         Routes haqnow.com → prod, haqnow.click → dev          │     │
│  └───────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    Shared: MySQL + PostgreSQL + S3
```

### **Environment Differences**
| Feature | Production (haqnow) | Development (haqnow-dev) |
|---------|---------------------|--------------------------|
| Domain | haqnow.com | haqnow.click |
| Git Branch | prod | main |
| Backend Pods | 2 (HA) | 1 |
| Worker | Dedicated | Shared (uses prod worker) |
| Analytics | Enabled | Disabled |
| Image Tags | :latest | :dev |

### **Deployment Strategy**
- **Rolling updates**: Zero-downtime deployments
- **High availability**: 2 backend pods for prod redundancy
- **Resource limits**: CPU/memory limits per pod
- **Health checks**: Liveness and readiness probes
- **Shared resources**: Both environments share databases, S3, and worker

## 🌐 **Network Architecture**

### **Production Setup**
```
Internet → Deflect CDN → Network Load Balancer → K8s Ingress
                                    ↓
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              frontend pod    backend-api pods    worker pod
                    │               │               │
                    └───────────────┼───────────────┘
                                    ▼
                          External Services:
                          ├─ MySQL DBaaS
                          ├─ PostgreSQL DBaaS  
                          ├─ S3 Object Storage
                          ├─ Thaura.AI (LLM)
                          └─ Umami Analytics
```

### **Service Ports**
- **80/443**: Frontend (nginx via NLB)
- **8000**: FastAPI backend (internal)
- **21699**: Database connections (external)
- **External APIs**: Thaura.AI via HTTPS

## 📁 **File System Layout**

### **Container Directory Structure**
```
/app/
├── main.py ──────────── FastAPI application entry
├── app/
│   ├── services/
│   │   ├── rag_service.py ── AI functionality (Thaura + sentence-transformers)
│   │   ├── otp_service.py ── OTP authentication (MySQL-backed)
│   │   └── ai_summary_service.py ── Document summaries
│   ├── database/
│   │   ├── database.py ─── MySQL connection
│   │   └── rag_database.py ─ PostgreSQL connection
│   └── apis/ ─────────── API endpoints
└── requirements*.txt ── Dependencies
```

### **Local Development Structure**  
```
fadih/
├── .env ─────────────────── Main environment file (shared by dev/prod)
├── scripts/
│   └── deploy.sh ────────── Deployment automation (--env=dev|prod)
├── k8s/
│   ├── .kubeconfig ──────── Cluster credentials
│   ├── manifests/ ───────── Production K8s YAML files
│   │   └── dev/ ─────────── Development K8s YAML files
│   └── scripts/
│       ├── create-secrets.sh ─── Prod namespace secrets
│       └── create-secrets-dev.sh ─ Dev namespace secrets
├── documentation/
│   ├── ARCHITECTURE.md ──── This file
│   └── DEBUGGING_GUIDE.md ── Troubleshooting
├── backend/ ─────────────── FastAPI source
└── frontend/ ────────────── React source
```

## 🔄 **Data Flow**

### **Document Upload Flow**
```
1. User uploads file → Frontend → Backend API (any pod)
2. File saved to S3 → Metadata to MySQL
3. Admin approval → Job queued
4. Worker pod: OCR processing (Tesseract)
5. Translation (Google Translate) → Text extraction
6. RAG processing → Chunking + Embedding → PostgreSQL
7. Available for search + AI Q&A
```

### **AI Search Flow**
```
1. User asks question → Frontend → Backend /api/rag/question
2. Generate query embedding → sentence-transformers (local, 768-dim)
3. Vector similarity search → PostgreSQL pgvector (cosine similarity)
4. Retrieve top chunks → Context preparation
5. LLM processing → Thaura.AI (ethical, privacy-first)
6. Response + sources → Frontend display
```

### **Traditional Search Flow**
```
1. User searches keywords → Frontend → Backend /api/search/search
2. Full-text search → MySQL (documents table)
3. Filter by country/language → Results ranking
4. Return metadata + links → Frontend display
```

## 🚀 **Deployment Architecture**

### **Deployment Commands**
```bash
# Development deployment (from main branch)
./scripts/deploy.sh --env=dev patch    # Deploy to haqnow.click
./scripts/deploy.sh patch              # Default is dev

# Production deployment (from prod branch)
./scripts/deploy.sh --env=prod patch   # Bug fixes
./scripts/deploy.sh --env=prod minor   # New features
./scripts/deploy.sh --env=prod major   # Breaking changes
```

### **Deployment Process (deploy.sh)**
```
Local Changes → Version bump → Frontend build
     ↓
Git commit/push → Docker build (backend-api, frontend)
     ↓  
Push to GHCR → kubectl apply to appropriate namespace
     ↓
Health checks → Pods ready → Complete
```

### **Dev → Prod Workflow**
```bash
# 1. Development work on main branch
git checkout main
# Make changes...
./scripts/deploy.sh --env=dev patch
# Test on https://haqnow.click

# 2. Promote to production
git checkout prod
git merge main
./scripts/deploy.sh --env=prod patch
# Live on https://www.haqnow.com
```

### **Environment Management**
- **Local**: `.env` (main source of truth, shared by both environments)
- **Kubernetes**: ConfigMap + Secrets (created from .env by deploy.sh)
- **Sync**: deploy.sh converts .env to K8s secrets automatically
- **Dev ConfigMap**: Disabled analytics, debug mode enabled

## 🔒 **Security Architecture**

### **Authentication Flow**
- **OTP tokens**: Passwordless admin authentication (MySQL-backed)
- **JWT tokens**: For session management
- **Rate limiting**: Anonymous time-bucket system
- **Multi-pod safe**: OTP stored in database, not memory

### **Privacy Protection**
- **No IP logging**: All logs exclude IP addresses
- **Anonymous uploads**: No user identification required  
- **Encrypted storage**: S3 with encryption at rest
- **Secure transmission**: HTTPS everywhere
- **Ethical AI**: Thaura.AI respects privacy

## 📊 **Monitoring & Analytics**

### **Umami Analytics** (Self-hosted)
- **URL**: https://analytics.haqnow.com
- **Privacy**: No cookies, GDPR compliant
- **Metrics**: Page views, referrers, countries, devices
- **Integration**: Tracking script in frontend index.html

### **Admin Analytics Dashboard**
- **URL**: /admin-analytics-page
- **Metrics**: Upload trends, document status, RAG queries
- **Charts**: Country distribution, language breakdown

## 📊 **Performance Considerations**

### **Performance Metrics**
1. **AI processing**: ~1-2 second response times with Thaura.AI
2. **Embeddings**: ~1s per embedding (local sentence-transformers)
3. **Low memory**: sentence-transformers uses ~500MB RAM per pod
4. **High availability**: 2 backend pods handle load balancing

### **Optimization Features**
1. **Connection pooling**: SQLAlchemy connection pools
2. **Model caching**: sentence-transformers models cached after first load
3. **Vector indexing**: pgvector IVFFlat index for fast similarity search
4. **CDN caching**: Deflect CDN caches static assets

### **Resource Usage (per pod)**
- **Backend**: ~1GB RAM (app + embedding model)
- **Worker**: ~1.5GB RAM (OCR + embedding model)
- **Frontend**: ~100MB RAM (nginx + static files)

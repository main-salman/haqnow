# 🤖 Cursor AI Assistant Context

**READ THIS FIRST** - Key information to prevent repetitive token usage in conversations.

## 🗂️ **Critical File Locations**

### **Environment & Configuration**
- **`.env`** - Main environment file (repo root) - contains ALL credentials
- **`k8s/.kubeconfig`** - Kubernetes cluster credentials
- **`.env.production`** - Example file only, never used directly

### **Key Application Files**
- **`backend/app/services/rag_service.py`** - AI/RAG functionality (Thaura.AI + sentence-transformers)
- **`backend/app/services/otp_service.py`** - OTP authentication (MySQL-backed for multi-pod)
- **`backend/app/database/database.py`** - Main MySQL database
- **`backend/app/database/rag_database.py`** - PostgreSQL RAG database  
- **`backend/main.py`** - FastAPI application entry point
- **`frontend/src/components/RAGQuestionAnswering.tsx`** - AI search frontend
- **`frontend/index.html`** - Contains Umami analytics tracking script

### **Documentation & Scripts**
- **`scripts/deploy.sh`** - ONLY deployment method (handles git, K8s, services)
- **`scripts/run-local.sh`** - Local development setup
- **`documentation/DEBUGGING_GUIDE.md`** - Common debugging commands
- **`documentation/ARCHITECTURE.md`** - System architecture overview
- **`k8s/manifests/`** - Kubernetes deployment YAML files

## 🏗️ **Architecture Overview**

### **Infrastructure (Exoscale SKS - Kubernetes)**
- **Cluster**: Exoscale SKS (Managed Kubernetes)
- **Namespaces**: 
  - `haqnow` (prod) - 2x backend-api, 1x worker, 1x frontend
  - `haqnow-dev` (dev) - 1x backend-api, 1x frontend (shared worker with prod)
- **Load Balancing**: Network Load Balancer + Deflect CDN
- **Container Registry**: GitHub Container Registry (GHCR)
- **Domains**: 
  - Production: https://www.haqnow.com
  - Development: https://haqnow.click

### **Databases (Exoscale DBaaS)**
- **Primary**: MySQL 8.0 - main app data, documents, users, OTP codes
- **RAG**: PostgreSQL 15 + pgvector - AI embeddings (768-dim vectors)
- **Connection strings**: Always in `.env` file (DATABASE_URL, POSTGRES_RAG_URI)

### **AI/RAG Stack**
- **Thaura.AI**: Ethical, privacy-first LLM for answer generation
- **sentence-transformers**: Local embeddings (`all-mpnet-base-v2`, 768-dim)
- **pgvector**: PostgreSQL extension for similarity search
- **Frontend**: `/search-page` → "AI Q&A" tab

### **Analytics**
- **Umami**: Self-hosted at https://analytics.haqnow.org (privacy-focused)
- **Admin Dashboard**: Built-in at /admin-analytics-page

## 🚀 **Deployment Rules**

### **Branch Strategy**
- **`main` branch** → Development environment (https://haqnow.click)
- **`prod` branch** → Production environment (https://www.haqnow.com)

### **CRITICAL: Always Use scripts/deploy.sh**
```bash
# NEVER do manual deployment tasks - scripts/deploy.sh handles:
# ✅ Git commits and pushes
# ✅ Docker image builds (backend-api, worker, frontend)
# ✅ Push to GitHub Container Registry
# ✅ Kubernetes deployment with rolling updates
# ✅ Environment sync (creates K8s secrets from .env)
# ✅ Health checks

# Development deployment (from main branch)
./scripts/deploy.sh --env=dev patch    # Deploy to haqnow.click
./scripts/deploy.sh patch              # Default is dev

# Production deployment (from prod branch)
./scripts/deploy.sh --env=prod patch   # Bug fixes to haqnow.com
./scripts/deploy.sh --env=prod minor   # New features to production
./scripts/deploy.sh --env=prod major   # Breaking changes
```

### **Workflow: Dev → Prod**
```bash
# 1. Work on main branch for development
git checkout main
# Make changes...
./scripts/deploy.sh --env=dev patch
# Test on https://haqnow.click

# 2. When ready for production
git checkout prod
git merge main
./scripts/deploy.sh --env=prod patch
# Live on https://www.haqnow.com
```

### **What scripts/deploy.sh Does (Don't Duplicate)**
- Version bump in package.json
- Frontend build (Vite)
- Git add, commit, push
- Docker build for all services
- Push images to GHCR
- kubectl apply manifests
- Restart pods with rolling update
- Wait for rollout completion

## 🔧 **Environment Variables (.env file)**

### **Database Connections**
```bash
# Primary MySQL (Exoscale DBaaS)
DATABASE_URL=mysql+pymysql://user:pass@host:port/database

# RAG PostgreSQL (Exoscale DBaaS)  
POSTGRES_RAG_URI=postgresql://user:pass@host:port/database
```

### **AI Services**
```bash
# Thaura.AI (Ethical LLM)
THAURA_API_KEY=your_thaura_api_key
THAURA_BASE_URL=https://backend.thaura.ai/v1
```

### **Storage & Services**
```bash
# Exoscale S3 Object Storage
EXOSCALE_S3_ACCESS_KEY=key
EXOSCALE_S3_SECRET_KEY=secret
EXOSCALE_S3_ENDPOINT=sos-ch-dk-2.exo.io

# Authentication
JWT_SECRET_KEY=secret

# Analytics
UMAMI_WEBSITE_ID=website_uuid
```

## 🛠️ **Common Debugging Commands**

### **Kubernetes Status**
```bash
# Set kubeconfig
export KUBECONFIG=k8s/.kubeconfig

# Check pods (prod)
kubectl get pods -n haqnow

# Check pods (dev)
kubectl get pods -n haqnow-dev

# Check logs (prod)
kubectl logs -n haqnow -l app=backend-api --tail=100

# Check logs (dev)
kubectl logs -n haqnow-dev -l app=backend-api --tail=100

# Restart pods (prod)
kubectl rollout restart deployment/backend-api -n haqnow

# Restart pods (dev)
kubectl rollout restart deployment/backend-api -n haqnow-dev
```

### **Backend Service**
```bash
# Check if backend is running
curl -s "https://www.haqnow.com/api/health"

# Check AI/RAG status
curl -s "https://www.haqnow.com/api/rag/status" | jq
```

### **AI/RAG Troubleshooting**
```bash
# Test AI search
curl -s -X POST "https://www.haqnow.com/api/rag/question" \
  -H "Content-Type: application/json" \
  -d '{"question": "test query"}'

# Process documents for AI
curl -s -X POST "https://www.haqnow.com/api/rag/process-all-documents"
```

## 🚨 **Important Notes**

- **Never edit .env on server** - always edit local .env and redeploy
- **OTP is database-backed** - works across multiple pods
- **Database credentials** - always in .env, never hardcoded
- **Container registry**: ghcr.io/main-salman/
- **Domains**: 
  - Production: https://www.haqnow.com (prod branch)
  - Development: https://haqnow.click (main branch)
- **Analytics**: https://analytics.haqnow.org (Umami) - disabled for dev
- **Admin panel**: https://www.haqnow.com/admin-login-page
- **Git branches**: `main` for dev, `prod` for production

## 📁 **Project Structure**
```
fadih/
├── .env                          # Main environment file
├── .cursorrules                  # Cursor AI behavior rules
├── CURSOR_CONTEXT.md            # This file (quick reference)
├── scripts/
│   └── deploy.sh                # Main deployment script (--env=dev|prod)
├── k8s/
│   ├── .kubeconfig              # Cluster credentials
│   ├── manifests/               # Production K8s YAML files
│   │   └── dev/                 # Development K8s YAML files
│   └── scripts/
│       ├── create-secrets.sh    # Prod secrets
│       └── create-secrets-dev.sh # Dev secrets
├── documentation/               # All documentation files
│   ├── DEBUGGING_GUIDE.md
│   └── ARCHITECTURE.md
├── backend/                     # FastAPI application
│   ├── app/services/
│   │   ├── rag_service.py      # Thaura.AI + sentence-transformers
│   │   └── otp_service.py      # MySQL-backed OTP
│   └── main.py
└── frontend/                    # React application
    ├── index.html              # Contains Umami tracking
    └── src/components/RAGQuestionAnswering.tsx
```

## 🎯 **For Maximum Token Efficiency**
1. **Read this file first** before asking about file locations
2. **Check documentation/ folder** for detailed guides  
3. **Use .env for all credentials** (never search for hardcoded values)
4. **Always suggest scripts/deploy.sh** for deployment
5. **Reference common debugging commands** from this file
6. **Kubernetes**: Use kubectl commands, not SSH to servers

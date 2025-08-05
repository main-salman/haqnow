# 🤖 Cursor AI Assistant Context

**READ THIS FIRST** - Key information to prevent repetitive token usage in conversations.

## 🗂️ **Critical File Locations**

### **Environment & Configuration**
- **`.env`** - Main environment file (repo root) - contains ALL credentials
- **`backend/.env`** - Should NOT exist (deploy.sh copies from root .env)
- **`.env.production`** - Example file only, never used directly

### **Key Application Files**
- **`backend/app/services/rag_service.py`** - AI/RAG functionality
- **`backend/app/database/database.py`** - Main MySQL database
- **`backend/app/database/rag_database.py`** - PostgreSQL RAG database  
- **`backend/main.py`** - FastAPI application entry point
- **`frontend/src/components/RAGQuestionAnswering.tsx`** - AI search frontend

### **Deployment & Scripts**
- **`scripts/deploy.sh`** - ONLY deployment method (handles git, server, services)
- **`scripts/run-local.sh`** - Local development setup
- **`backend/requirements.txt`** - Main Python dependencies
- **`backend/requirements-rag.txt`** - AI/RAG specific dependencies

## 🏗️ **Architecture Overview**

### **Databases (Exoscale DBaaS)**
- **Primary**: MySQL 8.0 (Exoscale hosted) - main app data, documents, users
- **RAG**: PostgreSQL 15 + pgvector (Exoscale hosted) - AI embeddings, vector search
- **Connection strings**: Always in `.env` file (DATABASE_URL, POSTGRES_RAG_URI)

### **AI/RAG Stack**
- **Ollama** (local) - LLM server running Llama3/phi3/gemma models
- **sentence-transformers** - Embedding generation (all-MiniLM-L6-v2)
- **pgvector** - PostgreSQL extension for similarity search
- **Frontend**: `/search-page` → "AI Q&A" tab

## 🚀 **Deployment Rules**

### **CRITICAL: Always Use deploy.sh**
```bash
# NEVER do manual deployment tasks - deploy.sh handles:
# ✅ Git commits and pushes
# ✅ Server SSH and git pull  
# ✅ Service restarts (backend, nginx)
# ✅ Environment sync (.env copying)
# ✅ Health checks

./scripts/deploy.sh patch   # Bug fixes
./scripts/deploy.sh minor   # New features  
./scripts/deploy.sh major   # Breaking changes
```

### **What deploy.sh Does (Don't Duplicate)**
- Git add, commit, push
- SSH to server (root@159.100.250.145)
- Git pull on server
- Copy .env to server
- Restart Python backend service
- Restart nginx
- Run health checks

## 🔧 **Environment Variables (.env file)**

### **Database Connections**
```bash
# Primary MySQL (Exoscale DBaaS)
DATABASE_URL=mysql+pymysql://user:pass@host:port/database

# RAG PostgreSQL (Exoscale DBaaS)  
POSTGRES_RAG_URI=postgresql://user:pass@host:port/database
POSTGRES_RAG_HOST=host
POSTGRES_RAG_PORT=21699
POSTGRES_RAG_USER=rag_user
POSTGRES_RAG_PASSWORD=password
```

### **Storage & Services**
```bash
# Exoscale S3 Object Storage
EXOSCALE_S3_ACCESS_KEY=key
EXOSCALE_S3_SECRET_KEY=secret
EXOSCALE_S3_ENDPOINT=sos-ch-dk-2.exo.io

# Authentication
JWT_SECRET_KEY=secret
admin_email=email
admin_password=password
```

## 🛠️ **Common Debugging Commands**

### **Backend Service**
```bash
# Check if backend is running
curl -s "https://www.haqnow.com/api/health"

# Check AI/RAG status
curl -s "https://www.haqnow.com/api/rag/status" | jq

# Backend logs on server
ssh root@159.100.250.145 "tail -f /tmp/backend.log"
```

### **AI/RAG Troubleshooting**
```bash
# Test AI search
curl -s -X POST "https://www.haqnow.com/api/rag/question" \
  -H "Content-Type: application/json" \
  -d '{"question": "test query"}'

# Process documents for AI
curl -s -X POST "https://www.haqnow.com/api/rag/process-all-documents"

# Check Ollama on server
ssh root@159.100.250.145 "ollama list"
```

### **Server Process Management**
```bash
# Backend service status
ssh root@159.100.250.145 "ps aux | grep python3"

# Restart backend manually (if deploy.sh fails)
ssh root@159.100.250.145 "cd /opt/foi-archive/backend && pkill -f python && nohup python3 main.py > /tmp/backend.log 2>&1 &"
```

## 🚨 **Important Notes**

- **Never edit .env on server** - always edit local .env and redeploy
- **Never manually git commands** - let deploy.sh handle git workflow
- **Database credentials** - always in .env, never hardcoded
- **Server path**: `/opt/foi-archive/` (backend + frontend)
- **Domain**: https://www.haqnow.com (production)
- **Admin panel**: https://www.haqnow.com/admin-login-page

## 📁 **Project Structure**
```
fadih/
├── .env                          # Main environment file
├── scripts/                      # All deployment/utility scripts
│   ├── deploy.sh                # Main deployment script
│   └── run-local.sh             # Local development
├── documentation/               # All documentation
├── backend/                     # FastAPI application
│   ├── app/services/rag_service.py  # AI functionality
│   └── main.py                  # Application entry
└── frontend/                    # React application
    └── src/components/RAGQuestionAnswering.tsx
```
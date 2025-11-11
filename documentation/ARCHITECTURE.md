# 🏗️ HaqNow Architecture Reference

**Quick architecture reference to understand system components and data flow.**

## 🗂️ **System Overview**

```
┌─ Frontend (React) ──── Port 80/443 ──── nginx
├─ Backend (FastAPI) ─── Port 8000 ───── Python
├─ AI/RAG (Groq API) ─── HTTPS ──────── Cloud LLM (ultra-fast inference)
├─ Embeddings (Local) ── sentence-transformers ─ Local (384-dim, multilingual)
├─ MySQL Database ────── Port 21699 ──── Exoscale DBaaS
├─ PostgreSQL RAG ───── Port 21699 ──── Exoscale DBaaS  
└─ S3 Storage ────────── HTTPS ─────── Exoscale SOS
```

## 💾 **Database Architecture**

### **Primary MySQL Database (Exoscale)**
- **Purpose**: Main application data
- **Tables**: documents, users, admins, translations, statistics
- **Connection**: `DATABASE_URL` in .env
- **Location**: Exoscale DBaaS (managed service)

### **RAG PostgreSQL Database (Exoscale)**  
- **Purpose**: AI/vector operations
- **Tables**: document_chunks (with embeddings), rag_queries
- **Connection**: `POSTGRES_RAG_URI` in .env
- **Extension**: pgvector for similarity search (384-dim vectors)
- **Location**: Exoscale DBaaS (managed service)

## 🤖 **AI/RAG Pipeline**

### **Processing Flow**
```
Document Upload → Admin Approval → OCR Text Extraction
     ↓
Document Chunking (500 chars) → Local Embedding (sentence-transformers, 384-dim)
     ↓  
Vector Storage (PostgreSQL) → Index Building (pgvector)
     ↓
Ready for AI Q&A Search
```

### **Query Flow**
```
User Question → Local Embedding (sentence-transformers) → Vector Similarity (pgvector)
     ↓
Context Retrieval (top chunks) → LLM Processing (Groq API - Mixtral, ultra-fast)
     ↓
Answer + Sources + Confidence Score → User Response
```

### **AI Stack Components**
- **Groq API**: Ultra-fast cloud LLM inference (mixtral-8x7b-32768, ~2-5s responses)
- **sentence-transformers**: Local multilingual embeddings (paraphrase-multilingual-MiniLM-L12-v2, 384-dim)
- **pgvector**: PostgreSQL extension for vector similarity search
- **FastAPI RAG Service**: Orchestrates the entire pipeline

## 🌐 **Network Architecture**

### **Production Setup (Exoscale)**
```
Internet → Deflect CDN → nginx (production server) → FastAPI (8000)
                                 ↓
                            Static Files (dist/)
                                 ↓
                            External Services:
                            ├─ MySQL DBaaS
                            ├─ PostgreSQL DBaaS  
                            ├─ S3 Object Storage
                            └─ Groq API (LLM only)
```

### **Service Ports**
- **80/443**: nginx (frontend + proxy)
- **8000**: FastAPI backend (internal)
- **21699**: Database connections (external)
- **External APIs**: Groq (LLM only) via HTTPS

## 📁 **File System Layout**

### **Server Directory Structure**
```
/opt/foi-archive/
├── backend/
│   ├── .env ──────────── Environment variables (synced from local)
│   ├── main.py ───────── FastAPI application entry
│   ├── app/
│   │   ├── services/
│   │   │   └── rag_service.py ── AI functionality
│   │   ├── database/
│   │   │   ├── database.py ─── MySQL connection
│   │   │   └── rag_database.py ─ PostgreSQL connection
│   │   └── apis/ ─────────── API endpoints
│   └── requirements*.txt ── Dependencies
└── frontend/
    └── dist/ ────────────── Built React application
```

### **Local Development Structure**  
```
fadih/
├── .env ─────────────────── Main environment file
├── scripts/
│   └── deploy.sh ────────── Deployment automation
├── documentation/
│   ├── ARCHITECTURE.md ──── This file
│   └── DEBUGGING_GUIDE.md ── Troubleshooting
├── backend/ ─────────────── FastAPI source
└── frontend/ ────────────── React source
```

## 🔄 **Data Flow**

### **Document Upload Flow**
```
1. User uploads file → Frontend → Backend API
2. File saved to S3 → Metadata to MySQL
3. Admin approval → OCR processing (Tesseract)
4. Translation (Google Translate) → Text extraction
5. RAG processing → Chunking + Embedding → PostgreSQL
6. Available for search + AI Q&A
```

### **AI Search Flow**
```
1. User asks question → Frontend → Backend /api/rag/question
2. Generate query embedding → sentence-transformers (local, 384-dim)
3. Vector similarity search → PostgreSQL pgvector (cosine similarity)
4. Retrieve top chunks → Context preparation
5. LLM processing → Groq API (mixtral-8x7b-32768 - ultra-fast)
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

### **Deployment Process (deploy.sh)**
```
Local Changes → Git commit/push → Server git pull
     ↓
Environment sync (.env) → Dependency install
     ↓  
Frontend build → Backend restart → nginx reload
     ↓
Health checks → Service verification → Complete
```

### **Environment Management**
- **Local**: `.env` (main source of truth)
- **Server**: `/opt/foi-archive/backend/.env` (synced by deploy.sh)
- **Secrets**: All credentials in .env, never in code
- **Sync**: deploy.sh ensures local and server .env are identical

## 🔒 **Security Architecture**

### **Authentication Flow**
- **JWT tokens**: For admin authentication
- **Password hashing**: bcrypt with salt
- **Session management**: Stateless JWT approach
- **Rate limiting**: Anonymous time-bucket system

### **Privacy Protection**
- **No IP logging**: All logs exclude IP addresses
- **Anonymous uploads**: No user identification required  
- **Encrypted storage**: S3 with encryption at rest
- **Secure transmission**: HTTPS everywhere

## 📊 **Performance Considerations**

### **Performance Improvements (Hybrid Architecture)**
1. **AI processing**: ~2-5 second response times (was 20-30s with Ollama)
2. **Non-blocking**: All operations are async
3. **Groq speed**: Up to 625 tokens/second (50-100x faster than Ollama)
4. **Low memory**: sentence-transformers uses ~500MB RAM (vs 4GB+ for Ollama)
5. **Cost**: $0 with Groq free tier (no OpenAI costs)

### **Optimization Opportunities**
1. **Caching**: Redis for frequent queries and embeddings
2. **Database tuning**: pgvector index optimization
3. **Batch embeddings**: sentence-transformers supports efficient batching
4. **Model caching**: sentence-transformers models cached after first load

### **Resource Usage**
- **RAM**: ~1.5GB (backend + sentence-transformers model)
- **Storage**: ~2GB (documents + 500MB embedding model)
- **CPU**: 2 cores sufficient (embeddings are CPU-bound but fast)
- **Network**: Groq API + database connections only
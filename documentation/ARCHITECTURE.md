# 🏗️ HaqNow Architecture Reference

**Quick architecture reference to understand system components and data flow.**

## 🗂️ **System Overview**

```
┌─ Frontend (React) ──── Port 80/443 ──── nginx
├─ Backend (FastAPI) ─── Port 8000 ───── Python
├─ AI/RAG (Ollama) ───── Port 11434 ──── Local LLM
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
- **Extension**: pgvector for similarity search
- **Location**: Exoscale DBaaS (managed service)

## 🤖 **AI/RAG Pipeline**

### **Processing Flow**
```
Document Upload → Admin Approval → OCR Text Extraction
     ↓
Document Chunking (500 chars) → Embedding Generation (384-dim)
     ↓  
Vector Storage (PostgreSQL) → Index Building (pgvector)
     ↓
Ready for AI Q&A Search
```

### **Query Flow**
```
User Question → Embedding Generation → Vector Similarity Search
     ↓
Context Retrieval (top 5 chunks) → LLM Processing (Ollama)
     ↓
Answer + Sources + Confidence Score → User Response
```

### **AI Stack Components**
- **Ollama**: Local LLM server (models: llama3, phi3:mini, gemma:2b)
- **sentence-transformers**: Embedding model (all-MiniLM-L6-v2)
- **pgvector**: PostgreSQL extension for vector operations
- **FastAPI RAG Service**: Orchestrates the entire pipeline

## 🌐 **Network Architecture**

### **Production Setup (Exoscale)**
```
Internet → Cloudflare → nginx (159.100.250.145) → FastAPI (8000)
                                 ↓
                            Static Files (dist/)
                                 ↓
                            External Services:
                            ├─ MySQL DBaaS
                            ├─ PostgreSQL DBaaS  
                            ├─ S3 Object Storage
                            └─ Ollama (local:11434)
```

### **Service Ports**
- **80/443**: nginx (frontend + proxy)
- **8000**: FastAPI backend (internal)
- **11434**: Ollama LLM server (internal)
- **21699**: Database connections (external)

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
2. Generate query embedding → sentence-transformers
3. Vector similarity search → PostgreSQL pgvector
4. Retrieve top chunks → Context preparation
5. LLM processing → Ollama (local model)
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

### **Current Bottlenecks**
1. **AI processing**: 20-30 second response times
2. **Blocking operations**: AI queries block main thread
3. **Database queries**: Vector search can be slow
4. **Model loading**: Large LLM models consume memory

### **Optimization Opportunities**
1. **Async processing**: Background AI job queue
2. **Caching**: Redis for frequent queries
3. **Model optimization**: Use smaller/faster models
4. **Database tuning**: pgvector index optimization
5. **Service separation**: Dedicated AI service

### **Resource Usage**
- **RAM**: ~4GB (backend + Ollama models)
- **Storage**: ~10GB (models + documents)
- **CPU**: 2-4 cores recommended
- **Network**: External database connections
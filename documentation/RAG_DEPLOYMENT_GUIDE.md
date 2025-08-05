# 🤖 RAG Q&A System Deployment Guide

This guide covers deploying the complete open source RAG (Retrieval-Augmented Generation) system for intelligent document question answering on HaqNow.

## 🎯 Overview

The RAG system transforms HaqNow from simple keyword search to intelligent Q&A, allowing users to ask natural language questions about corruption documents and receive AI-powered answers with source citations.

**Key Features:**
- 🧠 Natural language Q&A about document content
- 🔍 Vector similarity search across document chunks  
- 📚 Source attribution with confidence scoring
- 🔒 Fully local processing (no external APIs)
- 🌍 Multi-language support (60+ languages)
- 📈 Usage analytics and feedback system

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG SYSTEM ARCHITECTURE                 │
├─────────────────────────────────────────────────────────────┤
│  User Question                                              │
│       ↓                                                     │
│  [Frontend Q&A Interface]                                   │
│       ↓                                                     │
│  [FastAPI RAG Endpoints]                                    │
│       ↓                                                     │
│  [sentence-transformers] → [PostgreSQL pgvector]           │
│       ↓                          ↓                         │
│  [Context Retrieval] ← [Vector Similarity Search]          │
│       ↓                                                     │
│  [Ollama LLM] → [Generated Answer + Sources]               │
│       ↓                                                     │
│  [User Feedback & Analytics]                                │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites

### System Requirements
- **OS**: Linux, macOS, or Windows
- **Python**: 3.8+ 
- **Memory**: 8GB+ RAM (for LLM models)
- **Storage**: 4GB+ for models and embeddings
- **Database**: PostgreSQL with pgvector extension

### Dependencies
- PostgreSQL with pgvector
- Ollama (for LLM hosting)
- Python packages (see requirements-rag.txt)

## 🚀 Quick Start Deployment

### Step 1: Install Ollama
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve &

# Pull Llama3 model (4GB download)
ollama pull llama3
```

### Step 2: Setup Python Environment
```bash
cd backend

# Option A: Use virtual environment (recommended)
python3 -m venv rag_env
source rag_env/bin/activate
pip install -r requirements-rag.txt

# Option B: Install with --user flag
pip3 install --user -r requirements-rag.txt
```

### Step 3: Setup Database
```bash
# Create RAG tables and indexes
python3 create_rag_tables.py
```

### Step 4: Test System
```bash
# Run comprehensive system test
python3 test_rag_system.py
```

### Step 5: Start Services
```bash
# Start backend server
python3 main.py

# Process existing documents for RAG
curl -X POST http://localhost:8000/api/rag/process-all-documents
```

### Step 6: Frontend Access
- Navigate to: `http://localhost:3000/search-page`
- Click "AI Q&A" tab
- Ask questions about documents!

## 🔧 Manual Installation Steps

### 1. PostgreSQL with pgvector

**Ubuntu/Debian:**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo -u postgres psql -c "CREATE EXTENSION vector;"
```

**macOS:**
```bash
brew install postgresql pgvector
psql -d your_database -c "CREATE EXTENSION vector;"
```

### 2. Python Dependencies

Install core RAG packages:
```bash
pip install sentence-transformers==2.2.2
pip install ollama==0.1.7  
pip install langchain==0.1.0
pip install langchain-community==0.0.12
pip install pypdf==3.17.4
pip install pgvector==0.2.4
pip install psycopg2-binary==2.9.9
```

### 3. Model Downloads

The system will automatically download:
- **sentence-transformers/all-MiniLM-L6-v2** (~90MB) - For embeddings
- **Llama3** (~4GB) - For answer generation

## 🎮 Usage Guide

### Basic Q&A Workflow

1. **Navigate to Search Page**
   - Go to `/search-page`
   - Click "AI Q&A" tab

2. **Ask Questions**
   ```
   Example questions:
   • "What corruption cases have been reported in Brazil?"
   • "What are the main types of government fraud mentioned?"
   • "Which countries have the most bribery cases?"
   • "What evidence was found in corruption investigations?"
   ```

3. **Review Answers**
   - AI provides detailed responses
   - Sources show relevant documents
   - Confidence score indicates reliability
   - Click sources to view full documents

4. **Provide Feedback**
   - Thumbs up/down for answer quality
   - Helps improve system over time

### API Usage

**Ask Question:**
```bash
curl -X POST http://localhost:8000/api/rag/question \
  -H "Content-Type: application/json" \
  -d '{"question": "What corruption cases involve Brazil?"}'
```

**Process Document:**
```bash
curl -X POST http://localhost:8000/api/rag/process-document \
  -H "Content-Type: application/json" \
  -d '{"document_id": 123}'
```

**Check System Status:**
```bash
curl http://localhost:8000/api/rag/status
```

**View Analytics:**
```bash
curl http://localhost:8000/api/rag/analytics
```

## 📊 Monitoring & Analytics

### System Health Dashboard

Access at `/api/rag/status`:
- Ollama connectivity status
- Embedding model status  
- Total document chunks indexed
- Latest query timestamp

### Usage Analytics

Access at `/api/rag/analytics`:
- Total queries processed
- Average confidence scores
- Response time statistics
- User feedback summary
- Recent query history

### Performance Metrics

Monitor these key metrics:
- **Response Time**: < 5 seconds typical
- **Confidence Score**: > 0.6 for reliable answers
- **User Feedback**: > 80% helpful ratings target

## 🐛 Troubleshooting

### Common Issues

**1. "ModuleNotFoundError: No module named 'sentence_transformers'"**
```bash
pip install sentence-transformers
```

**2. "Ollama connection failed"**
```bash
# Check if Ollama is running
ps aux | grep ollama

# Start Ollama
ollama serve &

# Pull model if missing
ollama pull llama3
```

**3. "Database connection failed"**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Create vector extension
psql -d your_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

**4. "No pgvector module"**
```bash
pip install pgvector
```

**5. Low confidence scores**
- Add more documents to improve context
- Check document quality and OCR accuracy
- Verify embeddings are being generated

### Performance Optimization

**1. Improve Response Times:**
- Use SSD storage for vector data
- Increase PostgreSQL shared_buffers
- Use faster embedding models
- Add more CPU cores for parallel processing

**2. Enhance Answer Quality:**
- Process more documents for better context
- Improve document OCR quality
- Fine-tune chunking parameters
- Use larger LLM models (llama3:70b)

**3. Scale for Production:**
- Use dedicated PostgreSQL server
- Deploy Ollama on GPU-enabled machines
- Implement caching for common queries
- Add load balancing for multiple instances

## 🔐 Security Considerations

### Data Privacy
- All processing happens locally
- No external API calls for AI
- User queries stored locally only
- Vector embeddings contain no raw text

### Access Control
- RAG endpoints inherit existing auth
- Admin-only document processing endpoints
- Rate limiting on Q&A queries
- Audit logging for all interactions

## 🚀 Production Deployment

### Docker Configuration

**Dockerfile for RAG components:**
```dockerfile
FROM python:3.9
RUN curl -fsSL https://ollama.ai/install.sh | sh
COPY requirements-rag.txt .
RUN pip install -r requirements-rag.txt
# ... rest of config
```

### Load Balancing

For high-traffic deployments:
- Multiple FastAPI instances
- Shared PostgreSQL database
- Dedicated Ollama servers
- Redis for caching frequent queries

### Monitoring

Essential monitoring:
- RAG query volume and latency
- Ollama model performance
- PostgreSQL vector query performance
- User satisfaction metrics

## 📈 Scaling Guidelines

### Document Volume
- **< 1,000 docs**: Single server setup
- **1K-10K docs**: Dedicated database server
- **10K+ docs**: Distributed vector storage

### Query Volume  
- **< 100/day**: Basic setup sufficient
- **100-1K/day**: Add caching layer
- **1K+ queries/day**: Multiple LLM instances

### User Base
- **< 50 users**: Single deployment
- **50-500 users**: Load balanced setup
- **500+ users**: Microservices architecture

## 📚 Additional Resources

- **Ollama Documentation**: https://ollama.ai/docs
- **sentence-transformers**: https://www.sbert.net/
- **pgvector**: https://github.com/pgvector/pgvector
- **LangChain**: https://python.langchain.com/

## 🎉 Success Checklist

- [ ] Ollama installed and running
- [ ] Llama3 model downloaded
- [ ] Python dependencies installed
- [ ] Database tables created
- [ ] Test script passes
- [ ] Frontend Q&A interface working
- [ ] Documents processed for RAG
- [ ] API endpoints responding
- [ ] Analytics dashboard accessible

## 🆘 Support

For deployment issues:
1. Run `python3 test_rag_system.py` for diagnostics
2. Check `backend/logs/` for error details  
3. Verify all services running: PostgreSQL, Ollama, FastAPI
4. Test individual components before full integration

---

**🎯 Goal**: Transform document search into intelligent Q&A while maintaining complete privacy and open source principles!
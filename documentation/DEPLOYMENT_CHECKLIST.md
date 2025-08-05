# 🚀 RAG-Enhanced Deployment Checklist

This checklist ensures successful deployment of HaqNow with the new AI Q&A (RAG) functionality.

## ✅ Pre-Deployment Checklist

### Backend Preparation
- [ ] **RAG Service** - All RAG components implemented in `app/services/rag_service.py`
- [ ] **Database Models** - `DocumentChunk` and `RAGQuery` models added to `models.py`
- [ ] **API Endpoints** - RAG endpoints in `app/apis/rag/` with proper routing
- [ ] **Dependencies** - `requirements-rag.txt` created with all necessary packages
- [ ] **Migration Script** - `create_rag_tables.py` ready to create vector storage tables
- [ ] **Test Suite** - `test_rag_system.py` validates all components

### Frontend Preparation  
- [ ] **Q&A Component** - `RAGQuestionAnswering.tsx` component implemented
- [ ] **Search Integration** - Search page updated with tabs (Document Search / AI Q&A)
- [ ] **UI Components** - Tabs, input, feedback, and source display components
- [ ] **API Integration** - Frontend calls to RAG API endpoints

### Deployment Scripts
- [ ] **Enhanced deploy.sh** - Updated with RAG installation and setup steps
- [ ] **Test Script** - `test_live_rag.sh` ready to validate live deployment
- [ ] **Setup Script** - `setup_rag.sh` for local/server RAG installation

## 🚀 Deployment Process

### Step 1: Deploy with Enhanced Script
```bash
./scripts/deploy.sh [patch|minor|major]
```

The updated `deploy.sh` now includes:
- ✅ RAG dependency installation (`requirements-rag.txt`)
- ✅ Ollama installation and LLM model download
- ✅ RAG database table creation
- ✅ System testing and validation
- ✅ Document processing for existing content

### Step 2: Monitor Deployment Progress
During deployment, watch for these key steps:
```
🤖 Installing RAG (AI Q&A) dependencies...
🧠 Setting up Ollama for AI Q&A...
📦 Downloading Llama3 model for AI Q&A...
🗄️ Setting up RAG database tables...
🧪 Testing RAG system components...
📚 Processing existing documents for AI Q&A...
```

### Step 3: Validate Deployment
```bash
./test_live_rag.sh
```

## 🧪 Post-Deployment Testing

### Automated Tests
The `test_live_rag.sh` script validates:
- [ ] **Website Accessibility** - Basic site functionality
- [ ] **RAG API Endpoints** - `/api/rag/status`, `/api/rag/question`, `/api/rag/analytics`
- [ ] **Frontend Components** - AI Q&A interface on search page
- [ ] **LLM Services** - Ollama status and model availability
- [ ] **Database** - Vector storage and embedding functionality

### Manual Testing Checklist
Visit `https://www.haqnow.com/search-page` and verify:

#### UI Components
- [ ] **Tabs Visible** - "Document Search" and "AI Q&A" tabs present
- [ ] **Q&A Interface** - Question input, submit button, help text
- [ ] **Styling** - Consistent with site theme and responsive design

#### Functionality Testing
- [ ] **Ask Basic Question** - "What types of corruption are mentioned?"
- [ ] **Check Response** - AI answer with sources and confidence score
- [ ] **Source Links** - Clickable links to original documents
- [ ] **Feedback System** - Thumbs up/down buttons working
- [ ] **Error Handling** - Graceful handling of empty/invalid questions

#### Advanced Testing
- [ ] **Multi-language Questions** - Ask in different languages
- [ ] **Complex Queries** - "What corruption cases involve government contracts in Brazil?"
- [ ] **Performance** - Response time under 10 seconds
- [ ] **Source Attribution** - Verify sources match query content

## 🔧 Troubleshooting Common Issues

### RAG API Not Accessible
**Symptoms:** `/api/rag/status` returns 404 or 500
**Solution:**
```bash
# Check if backend is running with RAG endpoints
curl http://159.100.250.145:8000/api/rag/status

# If failed, check backend logs
sudo journalctl -u foi-archive -f

# Restart backend service
sudo systemctl restart foi-archive
```

### Ollama Service Issues
**Symptoms:** Q&A returns "LLM service unavailable"
**Solution:**
```bash
# Check Ollama status
ps aux | grep ollama

# Restart Ollama
nohup ollama serve > /tmp/ollama.log 2>&1 &

# Pull model if missing
ollama pull llama3
```

### Database Vector Extension
**Symptoms:** "vector extension not found" errors
**Solution:**
```bash
# Connect to database and enable extension
psql -d your_database -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Re-run table creation
cd backend && python create_rag_tables.py
```

### Frontend Q&A Tab Missing
**Symptoms:** Only "Document Search" tab visible
**Solution:**
```bash
# Rebuild frontend with latest components
cd frontend
npm run build
sudo cp -r dist/* /var/www/html/
sudo systemctl reload nginx
```

### Poor Answer Quality
**Symptoms:** Low confidence scores or irrelevant answers
**Solution:**
```bash
# Process more documents for better context
curl -X POST http://159.100.250.145:8000/api/rag/process-all-documents

# Check document processing status
curl http://159.100.250.145:8000/api/rag/analytics
```

## 📊 Success Metrics

### Technical Metrics
- [ ] **Response Time** - Q&A responses under 5 seconds
- [ ] **Availability** - RAG endpoints return 200 status
- [ ] **Model Status** - Ollama and embedding models loaded
- [ ] **Document Coverage** - >80% approved documents processed for RAG

### User Experience Metrics
- [ ] **Interface Accessibility** - Q&A tab visible and functional
- [ ] **Answer Quality** - Confidence scores >0.6 for most queries
- [ ] **Source Attribution** - Every answer includes relevant sources
- [ ] **Error Handling** - Graceful degradation when AI unavailable

## 🎯 Production Readiness

### Performance Optimization
- [ ] **Database Indexing** - Vector similarity indexes created
- [ ] **Model Caching** - Ollama models cached locally
- [ ] **Response Caching** - Consider Redis for frequent queries
- [ ] **Load Balancing** - Multiple backend instances if high traffic

### Monitoring & Analytics
- [ ] **Usage Tracking** - Q&A query volume and patterns
- [ ] **Quality Metrics** - User feedback and confidence scores
- [ ] **System Health** - Ollama uptime and model performance
- [ ] **Error Monitoring** - Failed queries and system errors

### Security & Privacy
- [ ] **Data Privacy** - All AI processing happens locally
- [ ] **No External APIs** - Verify no data sent to external services
- [ ] **User Anonymity** - Q&A queries not linked to users
- [ ] **Content Filtering** - Inappropriate query handling

## 🎉 Deployment Success Criteria

### Core Functionality ✅
- AI Q&A interface accessible at `/search-page`
- Natural language questions return relevant answers
- Source attribution links to original documents
- Confidence scoring shows answer reliability

### Technical Stability ✅  
- RAG API endpoints operational (status, question, analytics)
- Ollama LLM service running and responding
- Database vector storage operational
- Frontend components loading and functional

### User Experience ✅
- Intuitive Q&A interface with clear instructions
- Fast response times (<5 seconds typical)
- Helpful error messages and graceful degradation
- Mobile-responsive design consistent with site

---

**🚀 Ready for Production:** HaqNow now features revolutionary AI-powered document Q&A while maintaining complete user privacy and open source principles!
# 👥 Team Onboarding Guide

**Quick start guide for new team members working on HaqNow.**

## 🚀 **Getting Started**

### **1. Essential Files to Read First**
- **CURSOR_CONTEXT.md** - Key locations and workflows (READ FIRST)
- **documentation/ARCHITECTURE.md** - System overview
- **documentation/DEBUGGING_GUIDE.md** - Common issues & solutions
- **.cursorrules** - Cursor AI assistant configuration

### **2. Development Setup**
```bash
# Clone the repository
git clone https://github.com/main-salman/haqnow.git
cd haqnow

# Install dependencies
make install

# Set up environment variables
cp .env.example .env
# Edit .env with provided credentials

# Start local development
./scripts/run-local.sh
```

### **3. Key Credentials**
**Request these from team lead:**
- **Exoscale credentials** (S3 storage + databases)
- **Database connection strings** (MySQL + PostgreSQL)
- **Admin credentials** for testing
- **SendGrid API key** (optional for email)

## 🗂️ **Important File Locations**

### **Must-Know Files**
```bash
/.env                                   # All credentials (never commit!)
/scripts/deploy.sh                      # Only deployment method
/CURSOR_CONTEXT.md                      # Quick reference for Cursor AI
/backend/app/services/rag_service.py    # AI/RAG functionality
/frontend/src/components/RAGQuestionAnswering.tsx  # AI frontend
```

### **Configuration Files**
```bash
/.cursorrules                           # Cursor AI behavior
/backend/requirements.txt               # Python dependencies
/backend/requirements-rag.txt           # AI-specific dependencies
/frontend/package.json                  # React dependencies
```

## 🛠️ **Development Workflow**

### **Daily Workflow**
1. **Pull latest changes**: `git pull origin main`
2. **Make changes**: Edit code, test locally
3. **Test locally**: `./scripts/run-local.sh`
4. **Deploy changes**: `./scripts/deploy.sh patch`

### **Feature Development**
1. **Create feature branch**: `git checkout -b feature/new-feature`
2. **Develop & test**: Make changes, test thoroughly
3. **Merge to main**: `git checkout main && git merge feature/new-feature`
4. **Deploy**: `./scripts/deploy.sh minor`

### **Bug Fixes**
1. **Identify issue**: Use documentation/DEBUGGING_GUIDE.md
2. **Fix locally**: Test with `./scripts/run-local.sh`
3. **Deploy fix**: `./scripts/deploy.sh patch`

## 🚀 **Deployment Rules**

### **CRITICAL: Always Use deploy.sh**
```bash
# NEVER do manual deployment - deploy.sh handles everything:
./scripts/deploy.sh patch   # Bug fixes, small changes
./scripts/deploy.sh minor   # New features, enhancements  
./scripts/deploy.sh major   # Breaking changes, major updates
```

### **What deploy.sh Does (Don't Duplicate)**
- ✅ Git commits and pushes changes
- ✅ SSH to production server  
- ✅ Pulls latest code from git
- ✅ Syncs .env file to server
- ✅ Restarts all services (backend, nginx)
- ✅ Runs health checks

## 🗄️ **Database Understanding**

### **Two Separate Databases**
1. **MySQL (Primary)** - Documents, users, translations, metadata
2. **PostgreSQL (RAG)** - AI embeddings, vector search, query logs

### **Database Access**
```bash
# Connection strings in .env file:
DATABASE_URL=mysql+pymysql://...        # Primary database
POSTGRES_RAG_URI=postgresql://...       # AI/RAG database

# Both are hosted on Exoscale DBaaS (managed services)
```

## 🤖 **AI/RAG System**

### **How It Works**
1. **Documents uploaded** → Admin approval → OCR text extraction
2. **RAG processing** → Document chunking → Embedding generation  
3. **Vector storage** → PostgreSQL with pgvector extension
4. **User queries** → Embedding → Similarity search → LLM response

### **AI Stack Components**
- **Ollama**: Local LLM server (models: llama3, phi3:mini, gemma:2b)
- **sentence-transformers**: Text embedding generation
- **pgvector**: PostgreSQL extension for vector similarity
- **Frontend**: Search page → "AI Q&A" tab

### **Testing AI Functionality**
```bash
# Check AI system status
curl -s "https://www.haqnow.com/api/rag/status" | jq

# Test AI search
curl -s -X POST "https://www.haqnow.com/api/rag/question" \
  -H "Content-Type: application/json" \
  -d '{"question": "test query"}' | jq
```

## 🔍 **Common Development Tasks**

### **Adding New Features**
1. **Backend API**: Add endpoints in `backend/app/apis/`
2. **Frontend UI**: Add components in `frontend/src/components/`
3. **Database changes**: Create migration scripts
4. **Testing**: Test locally before deployment

### **Debugging Issues**
1. **Check logs**: `ssh root@www.haqnow.com "tail -f /tmp/backend.log"`
2. **Test APIs**: Use curl commands from DEBUGGING_GUIDE.md
3. **Check services**: Verify backend, nginx, ollama are running
4. **Environment**: Ensure .env has all required variables

### **Working with AI/RAG**
1. **Model changes**: Edit `backend/app/services/rag_service.py`
2. **Frontend updates**: Modify `RAGQuestionAnswering.tsx`
3. **Performance tuning**: Check model selection, chunking parameters
4. **Database**: Monitor PostgreSQL pgvector performance

## 🔒 **Security & Best Practices**

### **Environment Variables**
- **Never commit .env** to git (it's in .gitignore)
- **All secrets in .env** - no hardcoded credentials
- **deploy.sh syncs .env** between local and server
- **Request credentials** from team lead

### **Code Quality**
- **Follow existing patterns** in codebase
- **Test locally first** before deploying
- **Use descriptive commit messages**
- **Reference CURSOR_CONTEXT.md** for file locations

### **Production Safety**
- **Always use deploy.sh** for deployments
- **Never edit files directly on server**
- **Test changes locally first**
- **Check health endpoints after deployment**

## 🆘 **Getting Help**

### **When Stuck**
1. **Check documentation/** folder first
2. **Use DEBUGGING_GUIDE.md** for common issues
3. **Ask Cursor AI** (it has context from .cursorrules)
4. **Reach out to team** for complex issues

### **Emergency Contacts**
- **Team Lead**: [Contact info]
- **DevOps Issues**: [Contact info] 
- **Database Problems**: [Contact info]

### **Useful Resources**
- **Production URL**: https://www.haqnow.com
- **Admin Panel**: https://www.haqnow.com/admin-login-page
- **API Docs**: https://www.haqnow.com/docs (when backend running)
- **Repository**: https://github.com/main-salman/haqnow

## 📈 **Performance Monitoring**

### **Key Metrics to Watch**
- **API response times**: <2s for regular endpoints
- **AI search performance**: <30s for RAG queries
- **Document processing**: Monitor chunk counts
- **Database performance**: Watch connection pools

### **Monitoring Commands**
```bash
# System health
curl -s "https://www.haqnow.com/api/health" | jq

# AI system status  
curl -s "https://www.haqnow.com/api/rag/status" | jq

# Server resources
ssh root@www.haqnow.com "htop"
```

---

**Welcome to the team! 🎉 You're now equipped to contribute to fighting corruption through technology.**
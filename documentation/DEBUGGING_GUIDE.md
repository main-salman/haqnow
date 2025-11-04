# 🐛 HaqNow Debugging Guide

**Quick reference for common debugging scenarios to prevent repetitive troubleshooting.**

## 🚨 **Common Issues & Solutions**

### **1. AI Search Not Working**
```bash
# Check AI system status
curl -s "https://www.haqnow.com/api/rag/status" | jq

# Test with simple query
curl -s -X POST "https://www.haqnow.com/api/rag/question" \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}' | jq

# Process documents if chunks are low
curl -s -X POST "https://www.haqnow.com/api/rag/process-all-documents" | jq
```

### **2. Backend API Down (504 Gateway Timeout)**
```bash
# Check backend health
curl -s "https://www.haqnow.com/api/health"

# Check if Python process is running
ssh root@www.haqnow.com "ps aux | grep python3"

# Restart backend service
ssh root@www.haqnow.com "cd /opt/foi-archive/backend && pkill -f python && nohup python3 main.py > /tmp/backend.log 2>&1 &"

# Check logs
ssh root@www.haqnow.com "tail -f /tmp/backend.log"
```

### **3. Frontend Not Loading**
```bash
# Check nginx status
ssh root@www.haqnow.com "systemctl status nginx"

# Restart nginx
ssh root@www.haqnow.com "systemctl restart nginx"

# Check if frontend files deployed
ssh root@www.haqnow.com "ls -la /opt/foi-archive/frontend/dist/"
```

### **4. Database Connection Issues**
```bash
# Test main database
python3 -c "from backend.app.database.database import engine; print(engine.execute('SELECT 1').fetchone())"

# Test RAG database  
python3 -c "from backend.app.database.rag_database import test_rag_db_connection; print(test_rag_db_connection())"

# Check .env file has correct credentials
grep DATABASE_URL .env
grep POSTGRES_RAG_URI .env
```

## 🔍 **Performance Debugging**

### **AI Search Taking Too Long (>30s)**
```bash
# Check Ollama models
ssh root@www.haqnow.com "ollama list"

# Switch to faster model (gemma:2b is fastest)
# Edit backend/app/services/rag_service.py: self.model_name = "gemma:2b"

# Check vector database performance
ssh root@www.haqnow.com "cd /opt/foi-archive/backend && python3 test_performance.py"
```

### **Website Slow/Unresponsive During AI Queries**
- **Root cause**: AI processing blocks main thread
- **Solution**: Implement async processing (see ARCHITECTURE.md)
- **Quick fix**: Reduce AI usage until async implementation

## 🗄️ **Database Debugging**

### **Check Document Processing Status**
```bash
# See how many documents are indexed for AI
curl -s "https://www.haqnow.com/api/rag/status" | jq '.total_chunks'

# Process all documents for AI
curl -s -X POST "https://www.haqnow.com/api/rag/process-all-documents"

# Check individual document processing
curl -s -X POST "https://www.haqnow.com/api/rag/process-document" \
  -H "Content-Type: application/json" \
  -d '{"document_id": 123}'
```

### **Database Migration Issues**
```bash
# Run migrations manually
cd backend && python3 run_migration.py

# Check table structure
ssh root@www.haqnow.com "mysql -u user -p database -e 'SHOW TABLES;'"
```

## 🔧 **Service Management**

### **Server Services Status**
```bash
# Check all key services
ssh root@www.haqnow.com "
systemctl status nginx
systemctl status ollama  
ps aux | grep python3
"
```

### **Restart All Services**
```bash
# Use deploy.sh for clean restart
./scripts/deploy.sh patch

# Or manual restart
ssh root@www.haqnow.com "
systemctl restart nginx
systemctl restart ollama
cd /opt/foi-archive/backend && pkill -f python && nohup python3 main.py > /tmp/backend.log 2>&1 &
"
```

## 📊 **Monitoring Commands**

### **Real-time Monitoring**
```bash
# Backend logs
ssh root@www.haqnow.com "tail -f /tmp/backend.log"

# System resources
ssh root@www.haqnow.com "htop"

# Network connections
ssh root@www.haqnow.com "netstat -tulpn | grep :8000"
```

### **Health Check Sequence**
```bash
# Run these in order for full system check
curl -s "https://www.haqnow.com/api/health" | jq
curl -s "https://www.haqnow.com/api/rag/status" | jq  
curl -s "https://www.haqnow.com/api/statistics/country-stats" | jq
curl -s "https://www.haqnow.com/api/search/search?q=test&per_page=5" | jq
```

## 🚨 **Emergency Recovery**

### **Complete System Recovery**
```bash
# 1. Ensure .env is synced
scp .env root@www.haqnow.com:/opt/foi-archive/backend/.env

# 2. Full redeploy
./scripts/deploy.sh patch

# 3. If deploy.sh fails, manual recovery:
ssh root@www.haqnow.com "
cd /opt/foi-archive/backend
git pull origin main
pkill -f python
nohup python3 main.py > /tmp/backend.log 2>&1 &
systemctl restart nginx
"
```

### **Database Recovery**
```bash
# Backup current state
ssh root@www.haqnow.com "cd /opt/foi-archive/backend && python3 -c 'from app.database.database import engine; print(engine.execute(\"SELECT COUNT(*) FROM documents\").fetchone())'"

# Reset RAG database if corrupted
ssh root@www.haqnow.com "cd /opt/foi-archive/backend && python3 create_rag_tables.py"
```

## 💡 **Pro Tips**

1. **Always check .env first** - 90% of issues are missing/wrong environment variables
2. **Use deploy.sh** - don't manually restart services
3. **Check both databases** - MySQL for app data, PostgreSQL for AI
4. **Monitor response times** - AI queries should be <30s, API calls <2s
5. **Test locally first** - use `scripts/run-local.sh` before deploying
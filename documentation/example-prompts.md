Based on your new optimized structure, here are **5 example prompts** that will maximize token efficiency:

## 🎯 **5 Token-Efficient Prompt Examples**

### **1. Debugging Issues** (Instead of: "AI search isn't working")
```
The AI search is returning 504 timeouts. Use the debugging commands from 
@CURSOR_CONTEXT.md to check backend health, RAG status, and server logs. 
Fix any issues found and deploy the solution.
```
**Why Efficient**: References specific debugging section, prevents searching for commands

---

### **2. Adding Features** (Instead of: "Add a new API endpoint")
```
Add a new API endpoint for document statistics. Follow the existing pattern 
in backend/app/apis/, update the frontend component, and deploy using 
scripts/deploy.sh minor when ready.
```
**Why Efficient**: Uses file paths from CURSOR_CONTEXT.md, specifies deployment method

---

### **3. Performance Optimization** (Instead of: "The site is slow")
```
AI queries are taking 30+ seconds and blocking the main site. Implement the 
async processing architecture suggested in documentation/ARCHITECTURE.md 
to separate AI processing from web requests.
```
**Why Efficient**: References specific documentation, avoids re-explaining architecture

---

### **4. Environment/Configuration** (Instead of: "Where are the database credentials?")
```
I need to update the PostgreSQL RAG database connection. Update the 
POSTGRES_RAG_URI in .env (repo root) and deploy the changes using 
scripts/deploy.sh patch.
```
**Why Efficient**: Uses known file locations, specified deployment workflow

---

### **5. Team Collaboration** (Instead of: "How do I work on this project?")
```
A new team member needs to understand the RAG system. Point them to 
documentation/TEAM_ONBOARDING.md and documentation/ARCHITECTURE.md 
for the AI/RAG workflow explanation.
```
**Why Efficient**: Direct file references, no searching required

---

## 📋 **Prompt Templates for Common Scenarios**

### **Quick Debugging Template:**
```
[Issue description]. Check @CURSOR_CONTEXT.md debugging section and run 
the standard health checks. Fix and deploy with scripts/deploy.sh patch.
```

### **Feature Development Template:**
```
Add [feature] to [component]. Follow existing patterns in [specific file path], 
 deploy with scripts/deploy.sh minor.
```

### **Architecture Questions Template:**
```
[Question about system]. Reference documentation/ARCHITECTURE.md [specific section] 
and explain how [component] works in our setup.
```

### **Environment Issues Template:**
```
[Environment issue]. Update .env file (repo root) with [changes], then 
redeploy using scripts/deploy.sh patch to sync with server.
```

### **Performance Optimization Template:**
```
[Performance issue]. Check documentation/ARCHITECTURE.md performance section 
and implement [specific optimization]. Monitor with the commands from 
@CURSOR_CONTEXT.md.
```

---

## 🚀 **Key Efficiency Tips:**

1. **Always reference specific files**: `@CURSOR_CONTEXT.md`, `documentation/ARCHITECTURE.md`
2. **Use known file paths**: `backend/app/services/rag_service.py` instead of "the AI service file"
3. **Specify deployment method**: `scripts/deploy.sh [patch|minor|major]`
4. **Mention standard workflows**: "debugging commands from CURSOR_CONTEXT.md"
5. **Be task-specific**: What you want done, not just what's wrong

The `.cursorrules` will automatically guide Cursor to check these references first, **saving you significant tokens** on every conversation! 🎯
# HaqNow - Global Corruption Document Exposure Platform

**HaqNow** (Arabic "Haq" meaning "truth" or "right") is a privacy-first platform for exposing corruption documents worldwide. Citizens and journalists can anonymously upload evidence of corruption in **60+ languages** with automatic English translation, making documents accessible to global audiences.

## 🤖 **AI-Powered Q&A System (RAG)**

**Revolutionary RAG (Retrieval-Augmented Generation) technology enables intelligent question answering about corruption documents:**

✨ **Ask Natural Language Questions**: "What corruption cases involve Brazil?" or "What types of government fraud are mentioned?"  
🔍 **AI-Powered Answers**: Get detailed responses synthesized from relevant documents  
📚 **Source Attribution**: Every answer includes clickable links to source documents  
🎯 **Confidence Scoring**: Know how reliable each answer is (High/Medium/Low confidence)  
🔒 **Privacy-Focused**: Embeddings processed locally with open source models (sentence-transformers)  
⚡ **Ethical AI**: Powered by [Thaura.AI](https://thaura.ai/) - privacy-first, ethical LLM  
🌍 **Multi-Language**: Works with documents in all 60+ supported languages  
📈 **Smart Discovery**: Find relevant information across thousands of documents instantly

### **RAG System Architecture**

The AI Q&A system uses a sophisticated Retrieval-Augmented Generation pipeline:

#### **Dual Database Architecture**
- **Primary MySQL Database**: Stores document metadata, user data, translations, and search indexes
- **PostgreSQL RAG Database**: Dedicated vector database with pgvector extension for AI embeddings and similarity search

#### **Ethical AI Stack**
- **Thaura.AI**: Ethical, privacy-first LLM for answer generation ([thaura.ai](https://thaura.ai/))
- **sentence-transformers**: Local open source embeddings (`all-mpnet-base-v2`, 768-dim)  
- **pgvector**: PostgreSQL extension for efficient vector similarity search
- **FastAPI RAG Service**: Custom Python service orchestrating the AI pipeline
- **Cost**: Minimal - local embeddings are free, Thaura.AI is competitively priced

#### **Document Processing Pipeline**
1. **Document Upload** → Admin approval → OCR text extraction
2. **RAG Processing** → Document chunking → Embedding generation → Vector storage
3. **Query Processing** → Question embedding → Similarity search → LLM answer generation
4. **Response Delivery** → Confidence scoring → Source attribution → User feedback collection

## 📊 **Analytics & Monitoring**

### **Umami Analytics** (Self-hosted)
- **Privacy-focused**: No cookies, GDPR compliant visitor tracking
- **Dashboard**: [analytics.haqnow.com](https://analytics.haqnow.com)
- **Metrics**: Page views, referrers, device types, countries (IP not stored)
- **Lightweight**: ~1KB tracking script, minimal performance impact

### **Admin Analytics Dashboard**
- Built-in metrics for uploads, documents, and engagement
- Upload trends, document status, RAG query statistics
- Country and language distribution charts

## 🌍 **Live Platform**
- **Website**: https://www.haqnow.com *(Designed for strong anonymity; no system is 100% guaranteed)*

---

## 🏗️ **System Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            HAQNOW PLATFORM ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐    ┌──────────────────────────────────────┐    ┌─────────────────┐
│     FRONTEND        │    │              BACKEND                 │    │   AI/RAG LAYER  │
│                     │    │                                      │    │                 │
│  React + TypeScript │◄──►│            FastAPI                   │◄──►│   Thaura.AI     │
│  Vite + shadcn/ui   │    │         SQLAlchemy ORM               │    │  (Ethical LLM)  │
│  Multi-language i18n│    │      JWT Authentication             │    │   Privacy-First │
│  Interactive Maps   │    │       Rate Limiting                  │    │                 │
│  AI Q&A Interface   │    │       RAG Service                    │    │ sentence-trans. │
│  Real-time Search   │    │                                      │    │(Local Embedding)│
└─────────────────────┘    └──────────────────────────────────────┘    └─────────────────┘
           │                                    │                                 │
           │               ┌────────────────────┼─────────────────────────────────┼──────────┐
           │               │                    │                                 │          │
           ▼               ▼                    ▼                                 ▼          ▼
┌─────────────────┐ ┌─────────────┐ ┌──────────────────┐ ┌─────────────────┐ ┌──────────────────┐
│    NGINX        │ │   PRIMARY   │ │   MULTILINGUAL   │ │    STORAGE      │ │  RAG DATABASE    │
│                 │ │  DATABASE   │ │   OCR SERVICE    │ │                 │ │                  │
│ ✅ IP Anonymity │ │             │ │                  │ │ Exoscale SOS    │ │ PostgreSQL 15    │
│ ✅ SSL/TLS      │ │ MySQL 8.0   │ │ ✅ Tesseract OCR │ │ S3-Compatible   │ │ + pgvector ext.  │
│ ✅ Compression  │ │ Exoscale    │ │ ✅ 60+ Languages │ │ Document Store  │ │ Vector Embeddings│
│ ✅ Static Files │ │ Main Data   │ │ ✅ Google Trans. │ │ Secure Storage  │ │ 768-dim vectors  │
│ ✅ RAG Proxy    │ │ User/Admin  │ │ ✅ Metadata Strip│ │ CDN Delivery    │ │ Similarity Search│
└─────────────────┘ └─────────────┘ └──────────────────┘ └─────────────────┘ └──────────────────┘
           │                                    │                                 │
           │               ┌────────────────────┼─────────────────────────────────┼──────────┐
           │               │                    │                                 │          │
           ▼               ▼                    ▼                                 ▼          ▼
┌─────────────────┐ ┌─────────────┐ ┌──────────────────┐ ┌─────────────────┐ ┌──────────────────┐
│   KUBERNETES    │ │   PRIVACY   │ │    MONITORING    │ │    SECURITY     │ │   AI PIPELINE    │
│   (SKS)         │ │   LAYER     │ │                  │ │                 │ │                  │
│ Exoscale SKS    │ │             │ │ Umami Analytics  │ │ OTP Admin Auth  │ │ 1. Doc Chunking  │
│ Multi-pod HA    │ │ ✅ No IP Log│ │ (Self-hosted)    │ │ Rate Limiting   │ │ 2. Embedding Gen │
│ Auto-scaling    │ │ ✅ Anonymous│ │ Error Tracking   │ │ CORS Protection │ │ 3. Vector Store  │
│ Load Balancing  │ │ ✅ Zero Track│ │ Performance Mon. │ │ Input Validation│ │ 4. Similarity    │
│ Rolling Deploy  │ │ ✅ AI Privacy│ │ Admin Dashboard  │ │ AI Model Sec.   │ │ 5. LLM Response  │
└─────────────────┘ └─────────────┘ └──────────────────┘ └─────────────────┘ └──────────────────┘

                        ┌─────────────────────────────────────────────┐
                        │              DATA FLOW                      │
                        │                                             │
                        │ 1. Anonymous Upload (PDF/Images/Docs)      │
                        │ 2. Admin Review & Approval                  │
                        │ 3. Multilingual OCR + Translation          │
                        │ 4. Document Chunking + Vector Embedding    │
                        │ 5. Traditional Search + AI Q&A Available   │
                        │ 6. Global Access (60+ languages)           │
                        └─────────────────────────────────────────────┘

                        ┌─────────────────────────────────────────────┐
                        │            RAG QUERY FLOW                   │
                        │                                             │
                        │ Question → Embedding → Vector Search →     │
                        │ Context Retrieval → LLM Generation →       │
                        │ Confidence Scoring → Source Attribution    │
                        └─────────────────────────────────────────────┘
```

---

## ✨ **Core Features**

### 🌐 **Multilingual Document Processing**
- **60+ Language Support**: Upload documents in French, Arabic, German, Spanish, Russian, Chinese, Japanese, and 50+ more languages
- **Automatic Translation**: All non-English documents get English translations via Google Translate
- **OCR Technology**: Tesseract OCR with comprehensive language packs for text extraction
- **Download Options**: Original document + English translation + original language text
- **Search Enhancement**: Documents searchable in both original language and English

### 🔒 **Privacy-First Architecture**
- **Complete Anonymity**: Zero IP logging, no user tracking, anonymous uploads
- **Privacy Compliance**: GDPR-compliant with infrastructure-wide anonymity
- **Secure Storage**: End-to-end encrypted document storage on Exoscale S3
- **Anonymous Rate Limiting**: Time-bucket system without IP tracking
- **Clean Logs**: No identifying information in any system logs

### 🔍 **Advanced Search & Discovery**
- **Global Search**: Search by country, keyword, organization, document content
- **Multilingual Search**: Find documents in original language or English translation
- **Interactive World Map**: Visual corruption document distribution
- **Country Statistics**: Real-time document counts by country/region
- **Full-Text Search**: Search within document content (OCR extracted text)
- **Smart Filtering**: Filter by document language, date, approval status

### 👨‍💼 **Admin Management System**
- **Document Review**: Approval workflow with admin dashboard
- **Translation Management**: Real-time website translation updates (7 languages)
- **Content Moderation**: Banned word filtering and tag management
- **User Management**: Secure admin authentication with OTP (passwordless)
- **Analytics Dashboard**: Document statistics and system monitoring
- **Site-wide Announcement Banner**: Toggle on/off and edit the global banner shown on all pages

---

## 🛠️ **Technology Stack**

### **Frontend**
- **Framework**: React 18 + TypeScript + Vite
- **UI Library**: shadcn/ui components with Tailwind CSS
- **Internationalization**: React i18n with 7 languages (EN, AR, FR, DE, RU, PL, TR)
- **State Management**: React hooks + context
- **Build Tool**: Vite with optimized production builds

### **Backend**
- **API Framework**: FastAPI with automatic OpenAPI documentation
- **Database**: MySQL 8.0 (Exoscale DBaaS) with SQLAlchemy ORM
- **RAG Database**: PostgreSQL 15 with pgvector extension for vector operations
- **Authentication**: JWT-based with OTP (passwordless) admin login
- **API Keys**: Admin-managed API keys for programmatic uploads/downloads
- **File Storage**: Exoscale S3-compatible object storage (SOS)
- **OCR Engine**: Tesseract 5.x with 60+ language packs
- **Translation**: Google Translate API for automatic translations
- **AI/RAG Stack**: Thaura.AI (LLM) + sentence-transformers (embeddings)
- **Site Settings**: Lightweight key/value settings for global controls

### **Infrastructure**
- **Cloud Provider**: Exoscale (Swiss-based, privacy-focused)
- **Container Orchestration**: Exoscale SKS (Managed Kubernetes)
- **Deployment**: Terraform Infrastructure as Code + Kubernetes manifests
- **Web Server**: Nginx with privacy-compliant logging
- **CDN/DDoS Protection**: Deflect.ca
- **Analytics**: Self-hosted Umami (privacy-focused)
- **Container Registry**: GitHub Container Registry (GHCR)

### **Security & Privacy**
- **Rate Limiting**: Anonymous time-bucket rate limiting
- **CORS**: Configured for secure cross-origin requests
- **SSL/TLS**: Automatic HTTPS with secure headers
- **Input Validation**: Comprehensive request validation
- **File Security**: Virus scanning (VirusTotal) and type validation

---

## 🚀 **Deployment**

### **Infrastructure Overview**

HaqNow runs on **Exoscale SKS (Managed Kubernetes)** with:
- **2 backend-api pods** (high availability)
- **1 worker pod** (document processing)
- **1 frontend pod** (React app via nginx)
- **Network Load Balancer** for traffic distribution
- **Deflect CDN** for DDoS protection and SSL termination

### **Environment & Branch Mapping**

| Environment | Domain | Git Branch | K8s Namespace | Image Tag |
|-------------|--------|------------|---------------|-----------|
| **Development** | `haqnow.click` | `main` | `haqnow-dev` | `:dev` |
| **Production** | `haqnow.com` | `prod` | `haqnow` | `:latest` |

### **Deployment Commands**

```bash
# Deploy to DEVELOPMENT (haqnow.click)
./scripts/deploy.sh --env=dev patch    # Bug fixes
./scripts/deploy.sh --env=dev minor    # New features  
./scripts/deploy.sh --env=dev major    # Breaking changes

# Deploy to PRODUCTION (haqnow.com)
./scripts/deploy.sh --env=prod patch   # Bug fixes
./scripts/deploy.sh --env=prod minor   # New features
./scripts/deploy.sh --env=prod major   # Breaking changes

# Default (no --env) deploys to dev
./scripts/deploy.sh patch              # Same as --env=dev patch
```

### **Deployment Workflow**

#### **Your Typical Workflow**
```bash
# 1. Work on main branch (for dev features)
git checkout main

# 2. Make your changes (no need to commit manually)
# ... edit files ...

# 3. Deploy - script handles commit, push, and deploy
./scripts/deploy.sh --env=dev patch
```

#### **What the Script Does**

```
┌─────────────────────────────────────────────────────────────┐
│                    DEPLOY SCRIPT FLOW                       │
├─────────────────────────────────────────────────────────────┤
│ 1. ✓ Verify you're on correct branch (main or prod)         │
│ 2. ✓ Stash your uncommitted changes temporarily             │
│ 3. ✓ Pull latest from remote (other developers' changes)    │
│ 4. ✓ For prod: merge main → prod                            │
│ 5. ✓ Restore your changes                                   │
│ 6. ✓ Commit everything together                             │
│ 7. ✓ Push to remote                                         │
│ 8. ✓ Build Docker images & deploy to Kubernetes             │
└─────────────────────────────────────────────────────────────┘
```

#### **Development Deployment (`--env=dev`)**
- **Requires**: You must be on `main` branch
- **Pulls**: Latest changes from `origin/main`
- **Commits**: Your uncommitted changes
- **Deploys to**: `haqnow.click` (haqnow-dev namespace)

#### **Production Deployment (`--env=prod`)**
- **Requires**: You must be on `prod` branch
- **Pulls**: Latest changes from `origin/prod`
- **Merges**: Latest `main` into `prod` (automatic)
- **Commits**: Your uncommitted changes
- **Deploys to**: `haqnow.com` (haqnow namespace)

### **Multi-Developer Support**

Multiple developers can work on `main` branch simultaneously:

```
Developer A                    GitHub                    Developer B
    │                            │                            │
    │── deploy.sh ──────────────►│                            │
    │   (commits v5.1.13)        │                            │
    │                            │                            │
    │                            │◄────────── deploy.sh ──────│
    │                            │  1. Pulls v5.1.13 first    │
    │                            │  2. Auto-merges            │
    │                            │  3. Commits v5.1.14        │
```

- **Auto-pull**: Script pulls remote changes before committing yours
- **Auto-merge**: Changes merge automatically (developers work on different parts)
- **Conflict handling**: If rare conflict occurs, script aborts with clear instructions

### **Branch Requirements**

⚠️ **Important**: The script requires you to be on the correct branch:

```bash
# If you try to deploy dev while on prod branch:
$ ./scripts/deploy.sh --env=dev patch

❌ ERROR: Wrong branch!
   You're on: prod
   Expected:  main (for dev deployment)
   
   Please switch: git checkout main
```

### **What the Deploy Script Handles**

1. ✅ Branch verification (errors if wrong branch)
2. ✅ Pull latest from remote (multi-developer support)
3. ✅ **Merge main→prod for production deploys**
4. ✅ Auto-commit your uncommitted changes
5. ✅ Version bumping in package.json
6. ✅ Frontend build (Vite)
7. ✅ Git push to remote
8. ✅ Docker image builds (backend-api, worker, frontend)
9. ✅ Push to GitHub Container Registry (GHCR)
10. ✅ Kubernetes deployment with rolling updates
11. ✅ Health checks and rollout status

### **Important Notes**

⚠️ **Always use deploy.sh** - it ensures:
- Your changes include other developers' recent commits
- Production always receives merged changes from main
- Proper version tracking and git history
- No accidental overwrites of teammates' work

⚠️ **The script will**:
- Verify you're on the correct branch (errors if not)
- Temporarily stash your changes to pull remote updates
- Auto-merge other developers' changes
- Abort cleanly if merge conflicts occur (with instructions)

### **Environment Configuration**

All configuration in `.env` file (never commit to git):

```bash
# Primary Database (MySQL - Exoscale DBaaS)
DATABASE_URL=mysql+pymysql://user:password@host:port/database

# RAG Database (PostgreSQL - Exoscale DBaaS)
POSTGRES_RAG_URI=postgresql://user:password@host:port/database

# S3 Storage (Exoscale SOS)
EXOSCALE_S3_ACCESS_KEY=your_access_key
EXOSCALE_S3_SECRET_KEY=your_secret_key
EXOSCALE_S3_ENDPOINT=sos-ch-dk-2.exo.io
EXOSCALE_BUCKET=your_bucket_name

# AI/RAG (Thaura.AI + Local Embeddings)
THAURA_API_KEY=your_thaura_api_key
THAURA_BASE_URL=https://backend.thaura.ai/v1

# Authentication
JWT_SECRET_KEY=your_jwt_secret

# Analytics (Self-hosted Umami)
UMAMI_WEBSITE_ID=your_website_id

# Virus Scanning
VIRUSTOTAL_API_KEY=your_virustotal_key
```

---

## 📊 **Supported Languages**

HaqNow supports document upload and processing in **60+ languages**:

| **Region** | **Languages** |
|------------|---------------|
| **Arabic** | Arabic (Standard, Egyptian, Moroccan, Gulf variants) |
| **European** | French, German, Spanish, Italian, Portuguese, Russian, Polish, Dutch, Turkish, Ukrainian |
| **Asian** | Chinese (Simplified/Traditional), Japanese, Korean, Thai, Vietnamese, Hindi, Tamil |
| **African** | Swahili, Amharic, Hausa, Yoruba |
| **Others** | English, Danish, Swedish, Norwegian, Finnish, Czech, Hungarian, Romanian, and more |

*All non-English documents automatically receive English translations for global accessibility.*

---

## 🚀 **Recent Major Updates**

### **Version 4.15+ - Kubernetes & Ethical AI Migration**
- ✅ **Exoscale SKS**: Migrated from VM to managed Kubernetes
- ✅ **Thaura.AI**: Switched from Groq to ethical, privacy-first LLM
- ✅ **sentence-transformers**: Local embeddings (768-dim, all-mpnet-base-v2)
- ✅ **Umami Analytics**: Self-hosted, privacy-focused visitor tracking
- ✅ **Multi-pod HA**: Backend runs on 2 pods for high availability
- ✅ **OTP Database**: Fixed multi-pod OTP authentication with MySQL storage
- ✅ **GitHub Actions**: Automated Docker image builds on push

### **Version 4.6.0 - API Keys for Programmatic Access**
- ✅ API key model and admin UI for key management
- ✅ `X-API-Key` support on upload/download endpoints
- ✅ Bypass anonymous rate limits for authorized keys

### **Version 4.5.0 - Global Announcement Banner**
- ✅ Added `SiteSetting` table and announcement endpoints
- ✅ Global banner rendered across all pages
- ✅ Admin UI to enable/disable and edit banner

### **Version 2.2.x - Multilingual Revolution** 
- ✅ **60+ Language Support**: Complete Tesseract language pack installation
- ✅ **Automatic Translation**: Google Translate integration
- ✅ **Database Migration**: Migrated to Exoscale DBaaS

---

## 🏃‍♂️ **Quick Start**

### **Local Development**

1. **Install Dependencies**:
```bash
make install
```

2. **Start Development Servers**:
```bash
# Terminal 1: Backend (FastAPI)
make run-backend

# Terminal 2: Frontend (React/Vite)  
make run-frontend
```

3. **Access Application**:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### **Production Deployment**

```bash
# Deploy with semantic versioning
./scripts/deploy.sh patch   # Bug fixes (1.2.3 → 1.2.4)
./scripts/deploy.sh minor   # Features (1.2.3 → 1.3.0)
./scripts/deploy.sh major   # Breaking (1.2.3 → 2.0.0)
```

---

## 🔑 **Programmatic API Access (API Keys)**

### **Overview**
Administrators can generate API keys for server-to-server access.

### **Endpoints**
```bash
# Upload a document
POST /api/file-uploader/upload
Headers: X-API-Key: <your_api_key>

# Download a document
GET /api/search/download/{document_id}
Headers: X-API-Key: <your_api_key>
```

### **Admin UI**
Navigate to `Admin Management` → `API Keys` to manage keys.

---

## 📣 **Site Settings & Announcement Banner**

### **API Endpoints**
```bash
# Get announcement (public)
GET /api/site-settings/announcement

# Update announcement (admin-only)
PUT /api/site-settings/announcement
```

---

## 🤝 **Contributing**

HaqNow is dedicated to fighting corruption through transparency. Contributions welcome!

### **Development Principles**
1. **Privacy First**: Never add IP logging or user tracking
2. **Global Accessibility**: Support for international users
3. **Anonymous by Design**: Maintain complete anonymity
4. **Open Source**: Transparent codebase for security auditing

### **Contribution Areas**
- 🌐 **Language Support**: Additional translations and OCR improvements
- 🔒 **Privacy Enhancement**: Advanced anonymity features
- 🎨 **UI/UX**: Improved user experience
- 🔍 **Search**: Enhanced search algorithms
- 🛡️ **Security**: Security auditing

---

## 🌍 **Global Impact**

HaqNow serves corruption document whistleblowers in **180+ countries** with:

- **📄 1000s of Documents**: Corruption evidence from around the world
- **🌐 60+ Languages**: Native language support for global users
- **🔒 Complete Anonymity**: Zero tracking or identification
- **⚡ Real-time Search**: Instant access to corruption evidence
- **📊 Open Data**: Transparent corruption statistics by country

*Fighting corruption through technology, transparency, and global collaboration.*

---

## 📜 **License**

This project is open source and available under the MIT License.

---

## 📚 **Open Source Acknowledgments**

HaqNow is built on open source. Key dependencies include:

### **Core Platform**
- React, Vite, TypeScript, Tailwind CSS, shadcn/ui
- FastAPI, SQLAlchemy, Pydantic

### **AI/RAG Stack**
- sentence-transformers (Apache-2.0)
- pgvector (PostgreSQL License)
- Thaura.AI (external service)

### **Infrastructure**
- Kubernetes, Terraform, Nginx
- MySQL, PostgreSQL

For full license information, see individual package documentation.

---

## 🆘 **Support**

For technical support, feature requests, or security reporting:
- **Issues**: GitHub Issues (for technical problems)

*Together, we make corruption transparent.*

# HaqNow - Global Corruption Document Exposure Platform

**HaqNow** (Arabic "Haq" meaning "truth" or "right") is a privacy-first platform for exposing corruption documents worldwide. Citizens and journalists can anonymously upload evidence of corruption in **60+ languages** with automatic English translation, making documents accessible to global audiences.

## 🤖 **NEW: AI-Powered Q&A System**

**Revolutionary RAG (Retrieval-Augmented Generation) technology now enables intelligent question answering about corruption documents using only open source components:**

✨ **Ask Natural Language Questions**: "What corruption cases involve Brazil?" or "What types of government fraud are mentioned?"  
🔍 **AI-Powered Answers**: Get detailed responses synthesized from relevant documents  
📚 **Source Attribution**: Every answer includes clickable links to source documents  
🎯 **Confidence Scoring**: Know how reliable each answer is (High/Medium/Low confidence)  
🔒 **Fully Private**: All AI processing happens locally with open source models (Ollama + sentence-transformers)  
🌍 **Multi-Language**: Works with documents in all 60+ supported languages  
📈 **Smart Discovery**: Find relevant information across thousands of documents instantly

## 🌍 **Live Platform**
- **Website**: https://www.haqnow.com *(Complete anonymity guaranteed)*
---

## 🏗️ **System Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                        HAQNOW PLATFORM                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────┐    ┌──────────────────────────────────────┐
│     FRONTEND        │    │              BACKEND                 │
│                     │    │                                      │
│  React + TypeScript │◄──►│            FastAPI                   │
│  Vite + shadcn/ui   │    │         SQLAlchemy ORM               │
│  Multi-language i18n│    │      JWT Authentication             │
│  Interactive Maps   │    │       Rate Limiting                  │
│  Real-time Search   │    │                                      │
└─────────────────────┘    └──────────────────────────────────────┘
           │                                    │
           │               ┌────────────────────┼────────────────────┐
           │               │                    │                    │
           ▼               ▼                    ▼                    ▼
┌─────────────────┐ ┌─────────────┐ ┌──────────────────┐ ┌─────────────────┐
│    NGINX        │ │  EXOSCALE   │ │   MULTILINGUAL   │ │    STORAGE      │
│                 │ │   DBaaS     │ │   OCR SERVICE    │ │                 │
│ ✅ IP Anonymity │ │             │ │                  │ │ Exoscale SOS    │
│ ✅ SSL/TLS      │ │ MySQL 8.0   │ │ ✅ Tesseract OCR │ │ S3-Compatible   │
│ ✅ Compression  │ │ Managed DB  │ │ ✅ 60+ Languages │ │ Secure Storage  │
│ ✅ Static Files │ │ Auto Backup │ │ ✅ Google Trans. │ │ CDN Delivery    │
└─────────────────┘ └─────────────┘ └──────────────────┘ └─────────────────┘
           │                                    │
           │               ┌────────────────────┼────────────────────┐
           │               │                    │                    │
           ▼               ▼                    ▼                    ▼
┌─────────────────┐ ┌─────────────┐ ┌──────────────────┐ ┌─────────────────┐
│   TERRAFORM     │ │   PRIVACY   │ │    MONITORING    │ │    SECURITY     │
│                 │ │   LAYER     │ │                  │ │                 │
│ Infrastructure  │ │             │ │ Structured Logs  │ │ 2FA Admin Auth  │
│ as Code (IaC)   │ │ ✅ No IP Log│ │ Error Tracking   │ │ Rate Limiting   │
│ Exoscale Cloud  │ │ ✅ Anonymous│ │ Performance Mon. │ │ CORS Protection │
│ Auto Deployment │ │ ✅ Zero Track│ │ Health Checks    │ │ Input Validation│
└─────────────────┘ └─────────────┘ └──────────────────┘ └─────────────────┘

                        ┌─────────────────────────────┐
                        │       DATA FLOW             │
                        │                             │
                        │ 1. Anonymous Upload (PDF)   │
                        │ 2. Admin Review & Approval  │
                        │ 3. Multilingual OCR + Trans │
                        │ 4. Searchable + Downloadable│
                        │ 5. Global Access (60+ langs)│
                        └─────────────────────────────┘
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
- **User Management**: Secure admin authentication with 2FA
- **Analytics Dashboard**: Document statistics and system monitoring

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
- **Authentication**: JWT-based with bcrypt password hashing
- **File Storage**: Exoscale S3-compatible object storage (SOS)
- **OCR Engine**: Tesseract 5.x with 60+ language packs
- **Translation**: Google Translate API for automatic translations

### **Infrastructure**
- **Cloud Provider**: Exoscale (Swiss-based, privacy-focused)
- **Deployment**: Terraform Infrastructure as Code
- **Web Server**: Nginx with privacy-compliant logging
- **Process Management**: systemd with environment isolation
- **Monitoring**: Structured logging with structured + journald

### **Security & Privacy**
- **Rate Limiting**: Anonymous time-bucket rate limiting
- **CORS**: Configured for secure cross-origin requests
- **SSL/TLS**: Automatic HTTPS with secure headers
- **Input Validation**: Comprehensive request validation
- **File Security**: Virus scanning and type validation

---

## 🚀 **Recent Major Updates**

### **Version 2.2.x - Multilingual Revolution** 
- ✅ **60+ Language Support**: Complete Tesseract language pack installation
- ✅ **Automatic Translation**: Google Translate integration for all languages
- ✅ **Enhanced OCR**: French, German, Spanish, Russian, Chinese, Arabic support
- ✅ **Database Migration**: Migrated from local MySQL to Exoscale DBaaS
- ✅ **Download Options**: 3-way downloads (PDF + English + Original language)
- ✅ **Search Improvements**: Multilingual search with translation support

### **Version 2.1.x - Privacy Enhancement**
- ✅ **Complete IP Anonymity**: Removed all IP logging and tracking
- ✅ **Anonymous Rate Limiting**: Time-bucket system without user identification
- ✅ **Privacy-Compliant Nginx**: Custom log formats excluding IP addresses
- ✅ **Database Cleanup**: Migrated production database to remove all IP data
- ✅ **URL Masking**: Hidden S3 URLs behind website domain

### **Version 2.0.x - Platform Migration**
- ✅ **Exoscale Migration**: Complete migration from proprietary platform
- ✅ **JWT Authentication**: Industry-standard admin authentication
- ✅ **S3 Storage**: Secure file storage with Exoscale SOS
- ✅ **Terraform Deployment**: Infrastructure as Code with automated deployment
- ✅ **Email Notifications**: SendGrid integration for admin notifications

---

## 📊 **Supported Languages**

HaqNow.com supports document upload and processing in **60+ languages**:

| **Region** | **Languages** |
|------------|---------------|
| **Arabic** | Arabic (Standard, Egyptian, Moroccan, Gulf variants) |
| **European** | French, German, Spanish, Italian, Portuguese, Russian, Polish, Dutch, Turkish, Ukrainian |
| **Asian** | Chinese (Simplified/Traditional), Japanese, Korean, Thai, Vietnamese, Hindi, Tamil |
| **African** | Swahili, Amharic, Hausa, Yoruba |
| **Others** | English, Danish, Swedish, Norwegian, Finnish, Czech, Hungarian, Romanian, and more |

*All non-English documents automatically receive English translations for global accessibility.*

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

The `deploy.sh` script handles automated deployment to production with semantic versioning and comprehensive deployment workflows.

#### **Deployment Script Usage**

The `deploy.sh` script uses semantic versioning (`major.minor.patch`) to manage releases:

```bash
# Patch Release (bug fixes, small updates) - increments 1.2.3 → 1.2.4
./deploy.sh patch

# Minor Release (new features, non-breaking changes) - increments 1.2.3 → 1.3.0  
./deploy.sh minor

# Major Release (breaking changes, major updates) - increments 1.2.3 → 2.0.0
./deploy.sh major
```

#### **When to Deploy**

**Always run deployment after making code changes:**

1. **Bug Fixes & Small Updates** → Use `patch`
   ```bash
   # After fixing search functionality, UI improvements, etc.
   ./deploy.sh patch
   ```

2. **New Features & Enhancements** → Use `minor`
   ```bash
   # After adding new language support, admin features, etc.
   ./deploy.sh minor
   ```

3. **Breaking Changes & Major Overhauls** → Use `major`
   ```bash
   # After database schema changes, API breaking changes, etc.
   ./deploy.sh major
   ```

#### **Deployment Process**

The `deploy.sh` script performs the following automated tasks:

1. **Version Management**
   - Updates version numbers in package.json and relevant files
   - Creates git tags for release tracking
   - Commits version changes to repository

2. **Build Process**
   - Builds optimized production frontend (React/Vite)
   - Prepares backend with all dependencies
   - Generates static assets and documentation

3. **Infrastructure Deployment**
   - Runs Terraform to provision/update cloud resources
   - Deploys application to Exoscale cloud servers
   - Updates database schemas if needed
   - Configures SSL/TLS and domain settings

4. **Service Management**
   - Restarts backend services (FastAPI + Gunicorn)
   - Updates nginx configuration
   - Restarts frontend serving
   - Verifies all services are running

5. **Health Checks**
   - Tests API endpoints and database connectivity
   - Verifies file upload and OCR functionality
   - Checks translation services and search features
   - Confirms admin authentication and security

#### **Example Deployment Workflows**

```bash
# Scenario 1: Fixed country search bug
git add .
git commit -m "Fix country search functionality for Saudi Arabia/Switzerland"
./deploy.sh patch
# → Deploys as version 1.2.4

# Scenario 2: Added new admin translation management
git add .
git commit -m "Add comprehensive translation management for About/FOI pages"  
./deploy.sh minor
# → Deploys as version 1.3.0

# Scenario 3: Migrated to new database system
git add .
git commit -m "Migrate from MySQL to PostgreSQL with new schema"
./deploy.sh major
# → Deploys as version 2.0.0
```

#### **Local Testing**

Before production deployment, test locally:

```bash
# Run locally with production-like setup
./run-local.sh

# Test specific components
make test-backend
make test-frontend
```

#### **Deployment Requirements**

- **Terraform Setup**: Exoscale credentials configured in `.env`
- **Server Access**: SSH keys configured for production server
- **Environment Variables**: All production env vars set in `.env.production`
- **Database Access**: Production database credentials and connectivity

---

## ⚙️ **Environment Configuration**

### **Required Environment Variables**

```bash
# Database Configuration
DATABASE_URL=mysql://user:password@host:port/database

# S3 Storage (Exoscale SOS)
EXOSCALE_S3_ACCESS_KEY=your_access_key
EXOSCALE_S3_SECRET_KEY=your_secret_key
EXOSCALE_S3_ENDPOINT=sos-ch-dk-2.exo.io
EXOSCALE_S3_REGION=ch-dk-2
EXOSCALE_BUCKET=your_bucket_name

# Authentication
JWT_SECRET_KEY=your_jwt_secret_key
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=secure_admin_password

# Email Notifications (Optional)
SENDGRID_API_KEY=your_sendgrid_api_key

# OCR Configuration
TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata
```

See `.env.example` for complete configuration template.

---

## 🤝 **Contributing**

HaqNow.com is dedicated to fighting corruption through transparency and global accessibility. All contributions that advance this mission are welcome.

### **Development Principles**

1. **Privacy First**: Never add IP logging or user tracking
2. **Global Accessibility**: Support for international users and languages  
3. **Anonymous by Design**: Maintain complete anonymity for whistleblowers
4. **Open Source**: Transparent codebase for security auditing
5. **Performance**: Optimize for users worldwide with varying internet speeds

### **Contribution Areas**

- 🌐 **Language Support**: Additional language translations and OCR improvements
- 🔒 **Privacy Enhancement**: Advanced anonymity and security features
- 🎨 **UI/UX**: Improved user experience and accessibility
- 🔍 **Search**: Enhanced search algorithms and discovery features
- 📱 **Mobile**: Mobile application development
- 🛡️ **Security**: Security auditing and penetration testing

---

## 🌍 **Global Impact**

HaqNow.com serves corruption document whistleblowers in **180+ countries** with:

- **📄 1000s of Documents**: Corruption evidence from around the world
- **🌐 60+ Languages**: Native language support for global users
- **🔒 Complete Anonymity**: Zero tracking or identification
- **⚡ Real-time Search**: Instant access to corruption evidence
- **📊 Open Data**: Transparent corruption statistics by country

*Fighting corruption through technology, transparency, and global collaboration.*

---

## 📜 **License**

This project is open source and available under the MIT License for fighting corruption worldwide.

---

## 🆘 **Support**

For technical support, feature requests, or security reporting:
- **Issues**: GitHub Issues (for technical problems)

*Together, we make corruption transparent.*

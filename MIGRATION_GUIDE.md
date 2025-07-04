# FOI Archive Migration Guide

## Overview

This guide documents the migration of the FOI (Freedom of Information) document archive application from databutton.com to industry standard components for deployment on Exoscale.

## What Was Changed

### ✅ Backend Migration (COMPLETED)

#### 1. Dependencies Updated
- **Removed**: `databutton` package and all proprietary dependencies
- **Added**: Industry standard packages:
  - JWT authentication (`python-jose`, `passlib`, `bcrypt`)
  - S3 storage (`boto3`, `botocore`)
  - Rate limiting (`slowapi`, `redis`)
  - Email notifications (`sendgrid`)
  - Structured logging (`structlog`)
  - Environment management (`python-dotenv`)

#### 2. Authentication System
- **Replaced**: databutton auth middleware with JWT-based authentication
- **Created**: `app/auth/jwt_auth.py` - Comprehensive JWT authentication system
- **Updated**: `app/auth/user.py` - Uses new JWT dependencies
- **Added**: `app/apis/auth/__init__.py` - Login/logout endpoints

#### 3. File Storage
- **Replaced**: databutton storage with Exoscale S3
- **Created**: `app/services/s3_service.py` - Complete S3 service with upload, download, and management
- **Features**: Automatic file URL generation, presigned download URLs, file validation

#### 4. Rate Limiting
- **Created**: `app/middleware/rate_limit.py` - Rate limiting middleware
- **Features**: 1 document per IP per 2 minutes, Redis-backed with in-memory fallback
- **Endpoints**: Both upload and download rate limiting

#### 5. Email Notifications
- **Created**: `app/services/email_service.py` - SendGrid-based email service
- **Features**: Admin notifications for document uploads, approvals, and rejections

#### 6. API Updates
- **Updated**: All API modules to remove databutton dependencies:
  - `app/apis/file_uploader/__init__.py` - S3 upload with rate limiting and notifications
  - `app/apis/document_processing/__init__.py` - OCR processing with new auth
  - `app/apis/search/__init__.py` - Search with download rate limiting
  - `app/apis/statistics_api/__init__.py` - Statistics with environment variables

#### 7. Main Application
- **Completely rewritten**: `main.py` with proper middleware, CORS, security
- **Added**: Structured logging, startup/shutdown events, health checks

#### 8. Infrastructure as Code
- **Created**: Complete Terraform configuration for Exoscale deployment
- **Includes**: Cloud-init automation, Docker containerization, Nginx reverse proxy

## Deployment Instructions

### Prerequisites

1. **Exoscale Account**: With API credentials and S3 bucket created
2. **Supabase Project**: Database configured
3. **SendGrid Account**: For email notifications (optional)
4. **Terraform**: Installed locally
5. **SSH Key**: For server access

### Step 1: Configure Environment

1. Copy the example variables file:
   ```bash
   cp terraform/terraform.tfvars.example terraform/terraform.tfvars
   ```

2. Edit `terraform/terraform.tfvars` with your actual credentials:
   ```hcl
   # Exoscale API credentials
   exoscale_api_key    = "your-actual-api-key"
   exoscale_api_secret = "your-actual-api-secret"
   
   # S3 configuration (from your .env)
   s3_access_key = "***REMOVED***"
   s3_secret_key = "***REMOVED***"
   
   # Admin configuration
   admin_email    = "salman.naqvi@gmail.com"
   admin_password = "freepalestine"
   
   # Add your other credentials...
   ```

### Step 2: Deploy Infrastructure

1. Initialize Terraform:
   ```bash
   cd terraform
   terraform init
   ```

2. Plan the deployment:
   ```bash
   terraform plan
   ```

3. Deploy:
   ```bash
   terraform apply
   ```

4. Note the server IP from the output:
   ```bash
   terraform output instance_ip
   ```

### Step 3: Deploy Application Code

1. SSH to the server:
   ```bash
   ssh ubuntu@<instance-ip>
   ```

2. Clone your repository:
   ```bash
   cd /opt/foi-archive
   sudo git clone <your-repo-url> .
   sudo chown -R foi:foi /opt/foi-archive
   ```

3. Update the environment file with your actual credentials:
   ```bash
   sudo nano /opt/foi-archive/.env
   ```

4. Start the application:
   ```bash
   sudo systemctl start foi-archive
   sudo systemctl status foi-archive
   ```

### Step 4: Configure SSL (Optional)

1. SSH to the server and run:
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

## Application Architecture

### Backend Stack
- **FastAPI**: Web framework
- **JWT**: Authentication
- **Supabase**: Database
- **Exoscale S3**: File storage
- **Redis**: Rate limiting and caching
- **SendGrid**: Email notifications
- **Tesseract**: OCR processing
- **spaCy**: NLP for tag generation

### Frontend Stack
- **React + TypeScript**: UI framework
- **Vite**: Build tool
- **Tailwind CSS**: Styling
- **shadcn/ui**: Component library

### Infrastructure
- **Exoscale**: Cloud provider
- **Docker**: Containerization
- **Nginx**: Reverse proxy
- **Ubuntu 22.04**: Operating system
- **Terraform**: Infrastructure as code

## API Endpoints

### Authentication
- `POST /auth/login` - Admin login
- `GET /auth/me` - Get current user
- `POST /auth/logout` - Logout

### Document Management
- `POST /file-uploader/upload` - Upload document (rate limited)
- `GET /file-uploader/rate-limit-status` - Check rate limit status
- `POST /document-processing/process-document` - Process with OCR (admin only)
- `POST /document-processing/approve-document/{id}` - Approve document (admin only)
- `POST /document-processing/reject-document/{id}` - Reject document (admin only)

### Search and Browse
- `GET /search/search` - Search documents
- `GET /search/document/{id}` - Get specific document
- `GET /search/download/{id}` - Download document (rate limited)
- `POST /search/add-tag` - Add tag to document
- `GET /search/tags/{id}` - Get document tags

### Statistics
- `GET /statistics/country-stats` - Document count by country
- `GET /statistics/state-stats/{country}` - Document count by state
- `GET /statistics/global-stats` - Global platform statistics

## Security Features

1. **JWT Authentication**: Secure admin access
2. **Rate Limiting**: Upload/download throttling
3. **Input Validation**: File size and type restrictions
4. **CORS Configuration**: Secure cross-origin requests
5. **Environment Variables**: Secure credential management
6. **SSL/TLS**: HTTPS encryption (when configured)

## Monitoring and Logging

- **Structured Logging**: JSON-formatted logs with structured metadata
- **Health Checks**: `/health` endpoint for monitoring
- **Error Handling**: Comprehensive error responses with logging
- **Request Tracking**: Client IP tracking for rate limiting

## Troubleshooting

### Common Issues

1. **Upload fails**: Check S3 credentials and bucket permissions
2. **Rate limiting**: Check Redis connection and IP detection
3. **Email not sending**: Verify SendGrid API key and from email
4. **OCR not working**: Ensure Tesseract and spaCy model are installed
5. **Database errors**: Verify Supabase credentials and table schema

### Log Locations
- Application logs: `/var/log/foi/application.log`
- Docker logs: `docker-compose logs <service-name>`
- System logs: `journalctl -u foi-archive`

## Next Steps

### Remaining Tasks
1. **Frontend Migration**: Update frontend to remove databutton configurations
2. **Multi-language Support**: Add French, German, Spanish translations
3. **Word Heat Map**: Implement visualization component
4. **Performance Optimization**: Add caching and optimization
5. **Monitoring Setup**: Add comprehensive monitoring and alerting

### Enhancements
1. **Full-text Search**: Implement PostgreSQL full-text search
2. **Document Versioning**: Track document changes
3. **Advanced Analytics**: Usage statistics and reporting
4. **API Documentation**: OpenAPI/Swagger documentation
5. **Testing**: Unit and integration tests

## Support

For issues or questions about this migration, refer to:
- `history.txt` - Detailed change log
- Application logs - Error details and debugging
- Terraform documentation - Infrastructure management
- FastAPI documentation - API framework details

---

**Migration completed**: Backend fully migrated from databutton.com to industry standard components ✅ 
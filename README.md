# HaqNow.com - Global Corruption Document Exposure Platform

**Fadih** (Arabic for "reveal" or "make apparent") is an anonymous platform for exposing corruption documents worldwide. Citizens and journalists can upload evidence of corruption, which is reviewed by administrators and made searchable by anyone globally.

## Features

- **Anonymous Document Upload**: Secure, anonymous submission of corruption evidence
- **Admin Review System**: Document approval workflow with admin dashboard
- **Global Search**: Search corruption documents by country, keyword, organization
- **Country Statistics**: View corruption document distribution worldwide
- **Secure Storage**: Documents stored securely on Exoscale S3
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Privacy Compliance & Anonymity Guarantees

**HaqNow.com provides COMPLETE ANONYMITY for corruption document whistleblowers.** We have implemented comprehensive privacy protections at every level of the infrastructure to ensure zero tracking or identification of users.

### 🔒 **Application-Level Privacy**

#### Database Privacy
- ✅ **Zero IP Storage**: Completely removed `uploader_ip` column from database schema
- ✅ **Anonymous Documents**: All documents show "Anonymous" as submitter
- ✅ **No User Tracking**: No personally identifiable information stored
- ✅ **Privacy Migration**: Production database migrated to remove all IP data

#### Upload Process Privacy
- ✅ **Anonymous Uploads**: No IP address capture during document submission
- ✅ **Privacy-First API**: Upload endpoints do not store identifying information
- ✅ **Clean Console**: Browser console logs no sensitive information
- ✅ **Masked URLs**: Download URLs use website domain, not cloud storage URLs

#### Admin Interface Privacy
- ✅ **Anonymous Display**: All admin pages show "Anonymous" for document submitters
- ✅ **Privacy-Compliant Emails**: Admin notifications show anonymous submissions
- ✅ **No IP References**: Complete removal of IP address fields from admin interface

### 🛡️ **Server-Level Privacy**

#### Web Server Privacy (Nginx)
- ✅ **IP-Free Logs**: Custom log format excludes IP addresses completely
- ✅ **No IP Forwarding**: Removed `X-Real-IP` and `X-Forwarded-For` headers
- ✅ **Privacy Log Format**: `$time_local "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"`
- ✅ **Clean Access Logs**: Web server logs contain no identifying information

#### System-Level Privacy
- ✅ **Filtered System Logs**: Rsyslog configured to filter application logs with IPs
- ✅ **Limited Log Retention**: Maximum 7-day retention for all system logs
- ✅ **Network Isolation**: Disabled network log forwarding to prevent IP leakage
- ✅ **Application Log Filtering**: Nginx and uvicorn logs filtered from system storage

### ⚡ **Advanced Privacy Features**

#### Anonymous Rate Limiting
- ✅ **Time-Bucket System**: Global 2-minute time buckets instead of per-IP tracking
- ✅ **Anonymous Protection**: Rate limiting without identifying users
- ✅ **Privacy-Compliant Abuse Prevention**: Protection without compromising anonymity

#### Secure Downloads
- ✅ **URL Masking**: S3 URLs hidden behind website domain
- ✅ **Proxy Downloads**: Server streams files to hide cloud storage infrastructure
- ✅ **Professional URLs**: `http://159.100.250.145/api/search/download/13` instead of S3 URLs
- ✅ **No Storage Exposure**: Cloud provider details completely hidden

### 📋 **Privacy Compliance Verification**

**All 8 Privacy Tasks Completed:**
1. ✅ Remove uploader_ip column from Document model and database schema
2. ✅ Remove IP address storage from file upload API endpoint
3. ✅ Remove IP address from admin email notifications
4. ✅ Remove IP address from application logging throughout codebase
5. ✅ Remove IP address display from all admin interface pages
6. ✅ Update rate limiting to use session-based or alternative non-IP method
7. ✅ Configure nginx to not log IP addresses
8. ✅ Configure system logs to not store IP addresses

### 🌍 **Privacy Guarantees**

**We guarantee that HaqNow.com:**
- **NEVER** stores IP addresses in any database
- **NEVER** logs IP addresses in web server logs
- **NEVER** forwards IP addresses to backend applications
- **NEVER** includes identifying information in admin interfaces
- **NEVER** exposes cloud storage infrastructure to users
- **NEVER** tracks or identifies document uploaders

**Maximum protection for whistleblowers exposing corruption worldwide.**

### 🔧 **Technical Implementation**

Privacy protections implemented across:
- **Database Layer**: Complete IP storage removal and migration
- **Application Layer**: Anonymous APIs and interfaces
- **Web Server Layer**: Custom log formats and header filtering
- **System Layer**: Log filtering and retention policies
- **Network Layer**: Proxy downloads and URL masking
- **Client Layer**: Clean browser console and masked URLs

**Total infrastructure-wide anonymity achieved.**

## Stack

- **Frontend**: React + TypeScript with Vite, shadcn/ui components
- **Backend**: FastAPI with SQLAlchemy, MySQL database
- **Storage**: Exoscale S3 for document storage
- **Infrastructure**: Terraform for cloud deployment on Exoscale
- **Authentication**: JWT-based admin authentication
- **Package Managers**: `yarn` (frontend), `uv` (backend)

## Local Development

1. Install dependencies:

```bash
make
```

2. Start the backend and frontend servers in separate terminals:

```bash
make run-backend
make run-frontend
```

The backend server runs on port 8000 and the frontend development server runs on port 5173. The frontend Vite server proxies API requests to the backend on port 8000.

Visit <http://localhost:5173> to view the application.

## Production Deployment

This project is deployed on Exoscale cloud infrastructure using Terraform with **complete privacy compliance**:

- **Live Site**: http://159.100.250.145 *(Privacy-compliant, no IP tracking)*
- **API Documentation**: http://159.100.250.145/api/docs
- **Admin Login**: http://159.100.250.145/admin-login-page

### Deployment Commands

```bash
# Deploy to production server (includes privacy configurations)
./deploy.sh

# Run locally with production-like setup
./run-local.sh
```

The deployment process automatically configures:
- ✅ **Privacy-compliant nginx logs** without IP addresses
- ✅ **System log filtering** to prevent IP storage  
- ✅ **Anonymous rate limiting** and security measures
- ✅ **Database migration** to remove all IP data
- ✅ **Complete anonymity infrastructure** for whistleblowers

## Environment Variables

Key environment variables needed:

- `DATABASE_URL`: MySQL connection string
- `EXOSCALE_S3_*`: S3 storage credentials
- `JWT_SECRET_KEY`: JWT token signing key
- `ADMIN_EMAIL` / `ADMIN_PASSWORD`: Admin credentials
- `SENDGRID_API_KEY`: Email notifications

See `.env.example` for complete configuration.

## Contributing

HaqNow.com is dedicated to fighting corruption through transparency. All contributions that advance this mission are welcome.

### Privacy-First Development

When contributing to HaqNow.com, please maintain our privacy-first approach:

- **Never add IP logging** or tracking functionality
- **Avoid storing identifying information** about users
- **Maintain anonymity** in all user-facing interfaces
- **Test privacy compliance** with any new features
- **Follow the privacy guarantees** outlined above

All contributions must maintain the complete anonymity standards established for whistleblower protection.

## License

This project is open source and available for use in fighting corruption worldwide.

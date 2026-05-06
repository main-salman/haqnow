# 🛡️ Security & Privacy Specification

**Security architecture, privacy principles, and compliance reference for HaqNow.**

---

## 🔒 Security Philosophy

HaqNow protects whistleblowers and corruption document submitters. Security failures can put **lives at risk**. Every decision must prioritize user safety above all else.

### Threat Model
| Threat Actor | Capability | Mitigation |
|-------------|-----------|------------|
| Corrupt government | Subpoena, traffic analysis | No logs, no IP storage, anonymous uploads |
| State-level attacker | Network surveillance | HTTPS everywhere, Deflect CDN, metadata stripping |
| Malicious uploader | Malware via documents | VirusTotal scanning, file type validation |
| Script kiddie | Automated attacks | Rate limiting, security headers, DDoS protection |
| Insider threat | Database access | Minimal PII storage, encrypted connections |

---

## 🕵️ Privacy Architecture

### Core Principle: Zero-Knowledge Design
The platform is designed so that **operators cannot identify who uploaded any document**, even with full database and server access.

### Privacy Guarantees

| Guarantee | Implementation |
|-----------|----------------|
| **No IP logging** | All nginx logs exclude client IP; FastAPI logs anonymized |
| **No user accounts** | Public features (upload, search, view) require zero registration |
| **No cookies** | No tracking cookies; analytics via Umami (cookieless) |
| **No fingerprinting** | No browser fingerprinting, canvas, or WebGL tracking |
| **Metadata stripping** | `metadata_service.py` removes EXIF, author, GPS from uploads |
| **Anonymous rate limiting** | Time-bucket system — limits requests per time window, not per IP |
| **Anonymous comments** | No user identification for document comments |

### Data Flow Privacy Map
```
Upload Flow:
  User → Deflect CDN (IP seen, not logged) → NLB (IP not logged)
      → Backend Pod (IP not logged) → S3 (no IP metadata)
      → MySQL (no IP stored) → Admin review (anonymous)

Search Flow:
  User → CDN → Backend → MySQL/PostgreSQL → Response (no tracking)

RAG Flow:
  User → Question → Local embedding → pgvector search
      → Thaura.AI (question + context only, no user data)
      → Response (query stored without user identification)
```

---

## 🔐 Authentication System

### Admin Authentication (OTP + JWT)

```
1. Admin → POST /auth/request-otp { email }
2. System → Generate 6-digit OTP → Store in MySQL (otp_codes table)
3. System → Send OTP via email (SendGrid)
4. Admin → POST /auth/verify-otp { email, otp_code }
5. System → Validate OTP → Issue JWT token
6. Admin → Use JWT in Authorization header for subsequent requests
```

| Property | Value |
|----------|-------|
| OTP length | 6 digits |
| OTP expiry | 5 minutes |
| OTP storage | MySQL `otp_codes` table (multi-pod safe) |
| JWT algorithm | HS256 |
| JWT secret | `JWT_SECRET_KEY` in `.env` |
| JWT expiry | Configurable (default: 24h) |

### API Key Authentication
- Created via admin dashboard
- Sent via `X-API-Key` header
- Bypasses anonymous rate limits
- Usage tracked per key
- Can be revoked instantly

### Public Access (No Auth)
- Document upload — fully anonymous
- Document search — no authentication required
- Document viewing — no authentication required
- AI Q&A — no authentication required
- Comments — anonymous, rate limited

---

## 🚦 Rate Limiting

### Strategy: Anonymous Time-Bucket
Traditional rate limiting tracks by IP address. HaqNow uses a **time-bucket** approach that limits total requests per time window without identifying individual users.

| Endpoint | Limit | Window |
|----------|-------|--------|
| Document upload | Conservative | Per time bucket |
| Search queries | Generous | Per time bucket |
| RAG questions | Moderate | Per time bucket |
| Comments | Strict | Per document + time bucket |
| Admin endpoints | No limit | JWT required |
| API key endpoints | Higher | Per-key tracking |

### Deflect CDN Rate Limiting
Deflect.ca provides additional rate limiting at the CDN layer:
- DDoS protection with challenge system
- Bot detection and mitigation
- 429 responses for excessive requests

---

## 🔰 Security Headers

### Nginx Headers (`frontend/nginx.conf`)

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Frame-Options` | `SAMEORIGIN` | Clickjacking prevention |
| `X-Content-Type-Options` | `nosniff` | MIME sniffing prevention |
| `X-XSS-Protection` | `1; mode=block` | Legacy XSS filter |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` | Force HTTPS |
| `Content-Security-Policy` | Allowlist (self, Umami, fonts) | Resource loading control |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Referrer leakage prevention |
| `Permissions-Policy` | Disabled: geolocation, camera, mic, etc. | Feature restriction |
| `Cross-Origin-Opener-Policy` | `same-origin` | Cross-origin window isolation |
| `Cross-Origin-Embedder-Policy` | `credentialless` | Embedding control |
| `Cross-Origin-Resource-Policy` | `same-origin` | Resource loading restriction |
| `X-Permitted-Cross-Domain-Policies` | `none` | Flash/PDF policy |

### FastAPI Middleware (`backend/app/middleware/security_headers.py`)
Same headers applied to all API responses via custom middleware. Additionally:
- `Server: HaqNow` (hides server version)
- `Cache-Control: no-store, no-cache` for sensitive endpoints
- `Pragma: no-cache` for API and auth routes

---

## 🦠 Virus Scanning

### VirusTotal Integration
**File**: `backend/app/services/virus_scanning_service.py`

| Property | Value |
|----------|-------|
| Provider | VirusTotal API |
| Trigger | Every file upload |
| Timeout | Configurable |
| Action on detect | Reject upload, log alert |
| API key | `VIRUSTOTAL_API_KEY` in `.env` |

### File Validation
- Allowed file types: PDF, images (JPG, PNG, TIFF), Office documents
- Maximum file size enforced
- MIME type verification (not just extension)
- File content inspection

---

## 🌐 CORS Policy

### FastAPI CORS Configuration
```python
allowed_origins = [
    "https://www.haqnow.com",
    "https://haqnow.com",
    "https://haqnow.click",
    "http://localhost:5173",   # Local dev
]
```

| Setting | Value |
|---------|-------|
| Allow Origins | Production + dev domains |
| Allow Methods | GET, POST, PUT, DELETE, OPTIONS |
| Allow Headers | Authorization, Content-Type, X-API-Key |
| Allow Credentials | Yes |
| Max Age | 600 seconds |

---

## 🔏 Data Encryption

| Layer | Encryption |
|-------|-----------|
| **In Transit** | TLS 1.2+ (Deflect CDN terminates SSL) |
| **Database** | TLS connections to Exoscale DBaaS |
| **S3 Storage** | Encryption at rest (Exoscale SOS) |
| **Backups** | Encrypted S3 in DR region |

---

## 📋 Compliance

### GDPR Alignment
| Requirement | Implementation |
|-------------|----------------|
| Data minimization | No PII collected from public users |
| Right to erasure | Admin can delete documents |
| Privacy by design | Zero-knowledge architecture |
| Consent | No cookies = no consent needed |
| Data protection | Swiss hosting (Exoscale), encrypted storage |

### Privacy-Focused Technology Choices
| Choice | Privacy Benefit |
|--------|----------------|
| Exoscale (Swiss) | Swiss privacy laws, strong data protection |
| Deflect.ca | Non-profit CDN aligned with press freedom |
| Umami (self-hosted) | No third-party analytics, no cookies |
| Thaura.AI | Ethical, privacy-first LLM |
| sentence-transformers | Local embeddings, no data leaves server |

---

## 🚨 Incident Response

### Response Procedure
1. **Detect** — monitoring alerts, user reports, security scans
2. **Contain** — isolate affected pods (`kubectl scale deployment/X --replicas=0`)
3. **Assess** — determine scope, data impact, user exposure
4. **Remediate** — fix vulnerability, update dependencies
5. **Deploy** — push fix via `./scripts/deploy.sh patch`
6. **Document** — update `documentation/penetration-testing.md`
7. **Review** — post-incident analysis, update security spec

### Emergency Commands
```bash
# Isolate a compromised pod
kubectl scale deployment/backend-api --replicas=0 -n haqnow

# Check for unauthorized access
kubectl logs -n haqnow -l app=backend-api --tail=500 | grep -i "error\|unauthorized\|forbidden"

# Rotate JWT secret (forces all sessions to expire)
# 1. Generate new secret
# 2. Update .env JWT_SECRET_KEY
# 3. Redeploy: ./scripts/deploy.sh --env=prod patch

# Revoke all API keys (via admin dashboard or database)
```

---

## 🔍 Security Scanning

### Automated Scanning
```bash
# Full vulnerability scan
nuclei -u https://www.haqnow.com -severity critical,high,medium

# Security headers check
nuclei -u https://www.haqnow.com -t http/misconfiguration/http-missing-security-headers.yaml

# Verify headers manually
curl -sI https://www.haqnow.com | grep -iE "^(x-frame|x-content|strict-transport|content-security|referrer-policy)"
```

### Schedule
| Scan Type | Frequency |
|-----------|-----------|
| Nuclei full scan | Monthly |
| Security headers | After every deployment |
| Dependency audit | Quarterly |
| Penetration test | Annually |

---

## 📐 Security Checklist for New Features

Before merging any new feature:

- [ ] No IP addresses logged in any code path
- [ ] No user tracking or identification added
- [ ] No hardcoded secrets or credentials
- [ ] No new external service calls without privacy review
- [ ] Input validation on all user-provided data
- [ ] Proper auth (JWT/OTP/API key) on admin endpoints
- [ ] Rate limiting applied to public endpoints
- [ ] File uploads validated and virus-scanned
- [ ] CORS not broadened without justification
- [ ] Security headers not weakened
- [ ] No PII stored in databases or logs

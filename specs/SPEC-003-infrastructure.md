# SPEC-003: Infrastructure

> **Status**: Active  
> **Last Updated**: 2026-06-04  
> **Owner**: HaqNow Engineering

## Overview

HaqNow runs on Exoscale SKS (Managed Kubernetes) behind a Deflect CDN/DDoS protection proxy.

## Architecture

```
Users ──► Deflect CDN (DDoS protection, SSL termination)
              │
              ▼ (HTTP port 80 - Flexible TLS)
         Exoscale NLB
              │
              ▼
         Nginx Ingress Controller
              │
         ┌────┴────┐
         ▼         ▼
    Frontend    Backend API
    (Nginx)     (Uvicorn)
                   │
              ┌────┴────┐
              ▼         ▼
           MySQL     PostgreSQL
           (main)    (RAG/pgvector)
              
         Worker Pod (background processing)
         Umami Pod (analytics)
```

## Kubernetes Namespace Layout

| Namespace | Components |
|-----------|-----------|
| `haqnow` | Production: frontend, backend-api, worker, umami |
| `haqnow-dev` | Development: frontend, backend-api, worker |
| `ingress-nginx` | Nginx ingress controller |
| `cert-manager` | Let's Encrypt TLS certificates |
| `umami` | Analytics service |

## Pods and Deployments

### Backend API
- **Image**: `ghcr.io/main-salman/backend-api:latest`
- **Replicas**: 1 (reduced for cost)
- **Server**: Uvicorn with **1 worker** (single-threaded)
- **Resources**: 100m-800m CPU, 256Mi-1Gi memory
- **Liveness probe**: `GET /health:8000`, period=10s, timeout=10s, failureThreshold=18 (3 min tolerance)
- **Readiness probe**: `GET /health:8000`, period=5s, timeout=5s, failureThreshold=6
- **Volumes**: `/tmp` emptyDir for temporary file processing

> **IMPORTANT**: The single-worker Uvicorn means long-running operations (like upload processing
> in the request handler) block the health endpoint. Liveness probe tolerance was increased to
> 3 minutes (failureThreshold=18 × period=10s) to prevent pod kills during uploads.

### Frontend
- **Image**: `ghcr.io/main-salman/frontend:latest`
- **Server**: Nginx Alpine
- **Config**: `/etc/nginx/conf.d/default.conf`
- **Key settings**:
  - `client_max_body_size 50M` (for upload proxy)
  - Gzip compression enabled
  - Security headers (HSTS, CSP, X-Frame-Options)
  - SPA routing: `try_files $uri $uri/ /index.html`
  - API proxy: `/api/` → `backend-service:8000/`

### Worker
- **Image**: `ghcr.io/main-salman/worker:latest`
- **Replicas**: 1
- **Purpose**: Background document processing (OCR, tags, summary, RAG indexing)
- **Stale job recovery**: On startup and every 5 minutes

### Umami Analytics
- **Namespace**: `umami`
- **Domain**: `analytics.haqnow.org`
- **Purpose**: Privacy-first visitor analytics

## Ingress Configuration

### Frontend Ingress
- **Host**: `haqnow.org`
- **TLS**: Let's Encrypt via cert-manager
- **Annotations**: SSL redirect off (Deflect handles HTTPS)

### Backend Ingress
- **Host**: `haqnow.org`
- **Path**: `/api(/|$)(.*)`
- **Rewrite**: `/$2` (strips `/api` prefix)
- **Annotations**:
  - `proxy-body-size: 50m`
  - `proxy-read-timeout: 300` (5 min for upload processing)
  - `proxy-send-timeout: 300`
  - `proxy-connect-timeout: 60`
  - `ssl-redirect: false`

### Redirect Ingress
- **Hosts**: `haqnow.com`, `www.haqnow.com`
- **Action**: Permanent redirect to `https://haqnow.org$request_uri`

## Deflect CDN

- **Provider**: Deflect.ca (nonprofit DDoS protection)
- **TLS Mode**: Flexible (HTTPS to client, HTTP to origin)
- **Origin IP**: Exoscale NLB IP
- **Features**: DDoS protection, Baskerville bot detection, caching

> **NOTE**: Deflect terminates TLS at edge. Traffic from Deflect to origin is HTTP on port 80.
> The ingress `ssl-redirect: false` annotation is required for this to work.

## Storage

### Exoscale S3 (Object Storage)
- **Bucket**: Document PDFs (clean, metadata-stripped)
- **Region**: `ch-dk-2`
- **Access**: Via `s3_service` with boto3

### MySQL (Main Database)
- **Purpose**: Documents, users, settings, translations, comments, job queue
- **Tables**: `documents`, `job_queue`, `admin_users`, `site_settings`, `translations`, `document_comments`, etc.

### PostgreSQL (RAG Database)
- **Purpose**: Document chunks with vector embeddings
- **Extension**: pgvector for similarity search
- **Table**: `document_chunks` (document_id, chunk_index, content, embedding vector(384))

## Deployment

### Deploy Script
- **Path**: `scripts/deploy.sh`
- **Usage**: `./scripts/deploy.sh --env=prod patch`
- **Steps**:
  1. Switch to correct git branch (`main` for dev, `prod` for prod)
  2. Build frontend locally with Vite
  3. Commit and push to GitHub
  4. Build Docker images (backend-api, worker, frontend)
  5. Push to GHCR
  6. Apply Kubernetes manifests
  7. Restart pods and wait for rollout
  8. Deploy Umami analytics

### Image Build Strategy
- **Base image**: `ghcr.io/main-salman/backend-base:latest` (pre-built with dependencies)
- **App images**: Just copy code onto base (fast, ~10 seconds)
- **Frontend**: Built locally with Vite, served by Nginx Alpine

### Version Scheme
- Format: `v{backend}.{frontend}` (e.g., `v5.2.42 5.2.28`)
- Bumped by deploy script based on `patch`, `minor`, or `major` argument

## Monitoring

### Health Checks
- **Backend**: `GET /health` (HTTP 200)
- **Kubernetes**: Liveness and readiness probes

### Cross-Region Backup
- **CronJob**: `cross-region-backup` runs every 24 hours
- **Purpose**: Backup data to secondary region

## Environment Variables

Key configuration via ConfigMap and Secrets:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | MySQL connection string |
| `RAG_DATABASE_URL` | PostgreSQL connection string |
| `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY` | Object storage |
| `THAURA_API_KEY` | AI summary and RAG |
| `VIRUSTOTAL_API_KEY` | Virus scanning |
| `GITHUB_TOKEN` | GHCR image push |
| `SMTP_*` | Email notifications |
| `HCAPTCHA_SECRET_KEY` | Upload captcha |

## Invariants

1. **Deflect Flexible TLS** requires `ssl-redirect: false` on all ingresses
2. **Single uvicorn worker** means health probes need high failure tolerance
3. **Proxy timeouts** must be >= 300s to handle large document uploads
4. **Worker pod must run stale job recovery** on startup
5. **Frontend nginx** must have `client_max_body_size 50M` for upload proxy

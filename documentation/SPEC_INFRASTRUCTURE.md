# ☸️ Infrastructure & Deployment Specification

**Exoscale SKS Kubernetes infrastructure, deployment pipeline, and operational reference for HaqNow.**

---

## 🏗️ Infrastructure Overview

```
┌────────────────────────────────────────────────────────────┐
│                    Exoscale Cloud (Swiss)                    │
├────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌── SKS Cluster ──────────────────────────────────────┐   │
│  │  Namespace: haqnow (PROD)   haqnow-dev (DEV)       │   │
│  │  ├── backend-api (2 pods)   backend-api (1 pod)     │   │
│  │  ├── worker (1 pod)         frontend (1 pod)        │   │
│  │  ├── frontend (1 pod)       (shared worker)         │   │
│  │  └── backup CronJob                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌── DBaaS ────────────────────────────────────────────┐   │
│  │  MySQL 8.0       — Primary application data          │   │
│  │  PostgreSQL 15   — RAG vectors (pgvector)            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌── SOS (S3) ─────────────────────────────────────────┐   │
│  │  foi-archive-terraform — Document storage (Primary)  │   │
│  │  foi-archive-dr        — DR backups (Vienna)         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Network Load Balancer → Routes to K8s pods                 │
└────────────────────────────────────────────────────────────┘
         │
         ▼
  Deflect CDN (DDoS Protection + SSL Termination)
         │
         ▼
  Internet → haqnow.com / haqnow.click
```

---

## 🌐 Environment Matrix

| Property | Production | Development |
|----------|-----------|-------------|
| **Domain** | `haqnow.com` | `haqnow.click` |
| **Git branch** | `prod` | `main` |
| **K8s namespace** | `haqnow` | `haqnow-dev` |
| **Image tag** | `:latest` | `:dev` |
| **Backend pods** | 2 (HA) | 1 |
| **Worker** | Dedicated | Shared with prod |
| **Analytics** | Enabled (Umami) | Disabled |
| **Debug mode** | Off | On |

---

## 🐳 Container Images

**Registry**: `ghcr.io/main-salman/`

| Image | Dockerfile | Purpose | Size |
|-------|-----------|---------|------|
| `backend-api` | `backend/Dockerfile` | FastAPI application | ~1GB |
| `worker` | `backend/Dockerfile.worker` | Background processor | ~1.5GB |
| `frontend` | `frontend/Dockerfile` | React app via nginx | ~100MB |
| `backup` | `backend/Dockerfile.backup` | DR backup jobs | ~200MB |

### Build Pipeline
```
Code change → deploy.sh → Docker build (multi-platform amd64)
    → Push to GHCR → kubectl apply → Rolling restart
```

---

## 📦 Kubernetes Manifests

### File Structure
```
k8s/
├── .kubeconfig                     # Cluster credentials (NEVER commit)
├── manifests/                      # Production manifests
│   ├── backend-deployment.yaml     # backend-api Deployment + Service
│   ├── frontend-deployment.yaml    # frontend Deployment + Service
│   ├── worker-deployment.yaml      # worker Deployment
│   ├── backup-cronjob.yaml         # DR backup CronJob
│   ├── configmap.yaml              # Environment configuration
│   ├── ingress.yaml                # Ingress rules
│   └── dev/                        # Development overrides
│       ├── backend-deployment.yaml
│       ├── frontend-deployment.yaml
│       └── configmap-dev.yaml
└── scripts/
    ├── create-secrets.sh           # Create prod K8s secrets from .env
    └── create-secrets-dev.sh       # Create dev K8s secrets from .env
```

### Resource Limits (per pod)

| Pod | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-----|------------|-----------|---------------|--------------|
| backend-api | 250m | 1000m | 512Mi | 1Gi |
| worker | 500m | 2000m | 1Gi | 2Gi |
| frontend | 100m | 500m | 64Mi | 128Mi |

### Health Probes
- **Liveness**: HTTP GET `/api/health` (backend), TCP port 80 (frontend)
- **Readiness**: Same as liveness
- **Startup**: 30s initial delay, 5s period

---

## 🚀 Deployment Pipeline

### deploy.sh — The Single Source of Truth

**Location**: `scripts/deploy.sh`

```bash
# Syntax
./scripts/deploy.sh [--env=dev|prod] [patch|minor|major]

# Examples
./scripts/deploy.sh --env=dev patch    # Dev deployment
./scripts/deploy.sh --env=prod minor   # Prod feature release
./scripts/deploy.sh patch              # Default → dev
```

### Pipeline Steps
```
 1. ✅ Branch verification (main for dev, prod for prod)
 2. ✅ Stash uncommitted changes
 3. ✅ Pull latest from remote (multi-developer support)
 4. ✅ Merge main → prod (for prod deploys only)
 5. ✅ Restore stashed changes
 6. ✅ Version bump in package.json
 7. ✅ Frontend build (npm run build)
 8. ✅ Git add, commit, push
 9. ✅ Docker build (backend-api, worker, frontend)
10. ✅ Push images to GHCR
11. ✅ kubectl apply manifests
12. ✅ Restart pods (rolling update)
13. ✅ Wait for rollout completion
14. ✅ Health check verification
```

### Dev → Prod Workflow
```bash
# 1. Develop on main branch
git checkout main
# Make changes...
./scripts/deploy.sh --env=dev patch
# Test on https://haqnow.click

# 2. Promote to production
git checkout prod
git merge main
./scripts/deploy.sh --env=prod patch
# Live on https://www.haqnow.com
```

---

## 🌐 Network Architecture

### Traffic Flow
```
User → DNS → Deflect CDN → Exoscale NLB → K8s Ingress → Pod
```

### Ports

| Service | Internal Port | External Port | Protocol |
|---------|--------------|---------------|----------|
| Frontend (nginx) | 80 | 443 (via NLB) | HTTPS |
| Backend (FastAPI) | 8000 | Proxied via nginx | HTTP |
| MySQL | 21699 | 21699 (Exoscale) | TLS |
| PostgreSQL | 21699 | 21699 (Exoscale) | TLS |

### DNS Configuration
- `haqnow.com` → Deflect CDN → NLB
- `haqnow.click` → NLB (direct)
- `analytics.haqnow.com` → Umami server

---

## 💾 Database Infrastructure

### MySQL (Primary) — Exoscale DBaaS

| Property | Value |
|----------|-------|
| **Version** | 8.0 |
| **Plan** | Managed (Exoscale DBaaS) |
| **Region** | ch-dk-2 (Zurich) |
| **Port** | 21699 |
| **Connection** | `DATABASE_URL` in `.env` |
| **Encryption** | TLS in transit, encrypted at rest |

**Tables**: documents, admins, translations, statistics, otp_codes, api_keys, collaborators, comments, annotations, job_queue, site_settings

### PostgreSQL (RAG) — Exoscale DBaaS

| Property | Value |
|----------|-------|
| **Version** | 15 |
| **Extension** | pgvector |
| **Region** | ch-dk-2 (Zurich) |
| **Port** | 21699 |
| **Connection** | `POSTGRES_RAG_URI` in `.env` |

**Tables**: document_chunks (with 768-dim vector embeddings), rag_queries

---

## 🔄 Disaster Recovery

See `documentation/DISASTER_RECOVERY.md` for full runbook.

| Property | Value |
|----------|-------|
| **RPO** | 24 hours (daily backups) |
| **RTO** | 2-4 hours (manual restore) |
| **Backup schedule** | Daily at 3:00 AM UTC |
| **Backup location** | `foi-archive-dr` bucket, Vienna (at-vie-1) |
| **Retention** | 30 days |
| **Restore script** | `scripts/restore-from-backup.sh` |

---

## 📊 Monitoring

### Health Endpoints
```bash
curl -s https://www.haqnow.com/api/health          # Backend
curl -s https://www.haqnow.com/api/rag/status       # AI/RAG
```

### Kubernetes Monitoring
```bash
export KUBECONFIG=k8s/.kubeconfig

kubectl get pods -n haqnow                          # Pod status
kubectl top pods -n haqnow                          # Resource usage
kubectl logs -n haqnow -l app=backend-api --tail=50 # Backend logs
kubectl get events -n haqnow --sort-by='.lastTimestamp' # Recent events
```

### Analytics
- **Umami**: https://analytics.haqnow.com
- **Admin Dashboard**: `/admin-analytics-page`

---

## 💰 Cost Overview

| Component | Monthly Estimate |
|-----------|-----------------|
| SKS Cluster (nodes) | ~€40-60 |
| MySQL DBaaS | ~€15 |
| PostgreSQL DBaaS | ~€15 |
| S3 Storage (primary) | ~€5 |
| S3 DR Backups (Vienna) | ~€10-15 |
| NLB | ~€10 |
| Deflect CDN | Free (non-profit) |
| GHCR | Free (public repo) |
| **Total** | **~€95-120/month** |

---

## 🔧 Operational Scripts

| Script | Purpose |
|--------|---------|
| `scripts/deploy.sh` | Main deployment (ONLY method) |
| `scripts/run-local.sh` | Local development environment |
| `scripts/stop-local.sh` | Stop local services |
| `scripts/update-local.sh` | Update local environment |
| `scripts/restore-from-backup.sh` | DR restore tool |
| `scripts/setup-umami.sh` | Umami analytics setup |
| `scripts/update-version.sh` | Manual version bump |
| `k8s/scripts/create-secrets.sh` | Create prod K8s secrets |
| `k8s/scripts/create-secrets-dev.sh` | Create dev K8s secrets |

---

## 📐 Infrastructure Rules

1. **Never bypass deploy.sh** for deployments
2. **Never edit .env on the server** — edit locally, redeploy
3. **Never commit .kubeconfig** or `.env` to git
4. **All databases are managed** — never self-host databases
5. **Rolling updates only** — zero-downtime deployments
6. **Shared resources** — dev and prod share databases, S3, and worker
7. **Terraform for provisioning** — use IaC for infrastructure changes

# Disaster Recovery Runbook

**HaqNow Cross-Region Backup & Recovery Guide**

## Overview

HaqNow implements a cost-effective disaster recovery strategy using daily backups to a secondary Exoscale region:

| Component | Primary Region | DR Region |
|-----------|---------------|-----------|
| MySQL Database | ch-dk-2 (Zurich) | Backup to at-vie-1 (Vienna) |
| PostgreSQL RAG | ch-dk-2 (Zurich) | Backup to at-vie-1 (Vienna) |
| S3 Documents | ch-dk-2 (Zurich) | Synced to at-vie-1 (Vienna) |

**Recovery Objectives:**
- **RPO (Recovery Point Objective):** 24 hours (daily backups)
- **RTO (Recovery Time Objective):** 2-4 hours (manual restore)

## Architecture

```
Primary (ch-dk-2 Zurich)              Secondary (at-vie-1 Vienna)
┌─────────────────────┐               ┌─────────────────────┐
│ MySQL DBaaS         │──daily dump──▶│                     │
│ PostgreSQL DBaaS    │──daily dump──▶│  foi-archive-dr     │
│ foi-archive-terraform│──daily sync──▶│  (S3 Bucket)        │
└─────────────────────┘               └─────────────────────┘
         │                                      │
         │                                      │
    K8s CronJob                           Backup Storage
    (3 AM UTC daily)                      (30-day retention)
```

## Backup Schedule

- **Frequency:** Daily at 3:00 AM UTC
- **Retention:** 30 days
- **Storage:** S3 bucket `foi-archive-dr` in Vienna (at-vie-1)

### What Gets Backed Up

1. **MySQL Database** (`backups/mysql/mysql-YYYY-MM-DD-HHMMSS.sql.gz`)
   - All tables: documents, admins, translations, statistics, otp_codes, api_keys
   - Includes stored procedures, triggers, and routines

2. **PostgreSQL RAG Database** (`backups/postgres/postgres-rag-YYYY-MM-DD-HHMMSS.sql.gz`)
   - Vector embeddings (768-dim)
   - Document chunks
   - RAG query history

3. **S3 Documents** (`documents/`)
   - All uploaded PDFs, images, and documents
   - Synced incrementally (only changed files)

## Setup Instructions

### 1. Create DR Bucket in Exoscale Console

1. Log in to [Exoscale Console](https://portal.exoscale.com)
2. Go to **Storage** → **Object Storage**
3. Click **Add Bucket**
4. Configure:
   - **Name:** `foi-archive-dr`
   - **Zone:** `at-vie-1` (Vienna, Austria)
   - **Access:** Private
5. Click **Create**

### 2. Build and Push Backup Image

```bash
cd /path/to/fadih

# Build the backup image
docker buildx build \
  --platform linux/amd64 \
  -f backend/Dockerfile.backup \
  -t ghcr.io/main-salman/backup:latest \
  --push \
  backend/
```

### 3. Deploy CronJob to Kubernetes

```bash
# Apply the CronJob manifest
kubectl apply -f k8s/manifests/backup-cronjob.yaml

# Verify it was created
kubectl get cronjobs -n haqnow
```

### 4. Test the Backup Manually

```bash
# Trigger a manual backup job
kubectl create job --from=cronjob/cross-region-backup manual-backup-test -n haqnow

# Watch the job progress
kubectl logs -f job/manual-backup-test -n haqnow

# Check job status
kubectl get jobs -n haqnow
```

## Monitoring Backups

### Check CronJob Status

```bash
# View CronJob schedule and last run
kubectl get cronjobs -n haqnow

# View recent backup jobs
kubectl get jobs -n haqnow --sort-by=.metadata.creationTimestamp | tail -5

# View logs from last backup
kubectl logs job/$(kubectl get jobs -n haqnow -o jsonpath='{.items[-1].metadata.name}') -n haqnow
```

### List Available Backups

```bash
# Using the restore script
./scripts/restore-from-backup.sh list

# Or directly via AWS CLI
export AWS_ACCESS_KEY_ID=$EXOSCALE_S3_ACCESS_KEY
export AWS_SECRET_ACCESS_KEY=$EXOSCALE_S3_SECRET_KEY
aws s3 ls s3://foi-archive-dr/backups/mysql/ --endpoint-url https://sos-at-vie-1.exo.io
aws s3 ls s3://foi-archive-dr/backups/postgres/ --endpoint-url https://sos-at-vie-1.exo.io
```

## Disaster Recovery Procedures

### Scenario 1: Primary Region Outage (Full DR)

If the Zurich region (ch-dk-2) becomes unavailable:

#### Step 1: Assess the Situation
```bash
# Check if primary services are down
curl -s https://www.haqnow.com/api/health

# Check Exoscale status page
# https://status.exoscale.com/
```

#### Step 2: Create New Infrastructure in Vienna

```bash
# Option A: Use Terraform to create new resources in at-vie-1
cd terraform
terraform workspace new vienna-dr
# Edit terraform.tfvars to use zone = "at-vie-1"
terraform apply

# Option B: Manually create via Exoscale Console
# 1. Create MySQL DBaaS (hobbyist-2) in at-vie-1
# 2. Create PostgreSQL DBaaS (startup-4) in at-vie-1
# 3. Create SKS cluster in at-vie-1
```

#### Step 3: Restore Databases

```bash
# Run the restore script
./scripts/restore-from-backup.sh

# Select option 5 for full restore
# Or specify a date:
./scripts/restore-from-backup.sh restore 2025-01-15-030015
```

#### Step 4: Update Configuration

Edit `.env` with new database connection strings:

```bash
# Update MySQL connection
MYSQL_HOST=<new-mysql-host-in-vienna>
DATABASE_URL=mysql+pymysql://user:pass@<new-mysql-host-in-vienna>:21699/defaultdb

# Update PostgreSQL connection
POSTGRES_RAG_HOST=<new-postgres-host-in-vienna>
POSTGRES_RAG_URI=postgresql://user:pass@<new-postgres-host-in-vienna>:21699/defaultdb
```

#### Step 5: Deploy Application

```bash
# Deploy to new infrastructure
./scripts/deploy.sh patch
```

#### Step 6: Update DNS

Update DNS records to point to new infrastructure:
- `www.haqnow.com` → New NLB IP
- `haqnow.com` → New NLB IP

### Scenario 2: Database Corruption

If data is corrupted but infrastructure is intact:

```bash
# Restore only the affected database
./scripts/restore-from-backup.sh mysql 2025-01-14-030015

# Or for PostgreSQL:
./scripts/restore-from-backup.sh postgres 2025-01-14-030015
```

### Scenario 3: Accidental Document Deletion

If documents were accidentally deleted from S3:

```bash
# Sync documents back from DR bucket
./scripts/restore-from-backup.sh documents
```

### Scenario 4: Point-in-Time Recovery

To restore to a specific date:

```bash
# List available backups
./scripts/restore-from-backup.sh list

# Restore from specific backup
./scripts/restore-from-backup.sh restore 2025-01-10-030045
```

## Validation Checklist

After any restore, verify:

- [ ] API health check passes: `curl https://www.haqnow.com/api/health`
- [ ] RAG status returns OK: `curl https://www.haqnow.com/api/rag/status`
- [ ] Admin can log in
- [ ] Documents are accessible and downloadable
- [ ] AI Q&A returns results
- [ ] Search works correctly

## Cost Breakdown

| Component | Monthly Cost |
|-----------|-------------|
| S3 Storage (Vienna, ~50GB) | ~€1-2 |
| S3 Egress (daily sync) | ~€5-10 |
| Compute (uses existing K8s) | €0 |
| **Total** | **~€10-15/month** |

## Troubleshooting

### Backup Job Failed

```bash
# Check job logs
kubectl logs job/cross-region-backup-<timestamp> -n haqnow

# Check if secrets are configured
kubectl get secrets haqnow-secrets -n haqnow

# Verify S3 credentials work
aws s3 ls s3://foi-archive-dr/ --endpoint-url https://sos-at-vie-1.exo.io
```

### Cannot Connect to DR Bucket

```bash
# Verify bucket exists
# Go to Exoscale Console → Storage → Object Storage
# Check that foi-archive-dr exists in at-vie-1

# Test S3 access
export AWS_ACCESS_KEY_ID=$EXOSCALE_S3_ACCESS_KEY
export AWS_SECRET_ACCESS_KEY=$EXOSCALE_S3_SECRET_KEY
aws s3 ls s3://foi-archive-dr/ --endpoint-url https://sos-at-vie-1.exo.io
```

### Restore Taking Too Long

- Database restores typically take 5-15 minutes depending on size
- Document sync may take longer for large datasets
- Consider restoring only critical data first

## Files Reference

| File | Purpose |
|------|---------|
| `backend/Dockerfile.backup` | Docker image for backup jobs |
| `backend/scripts/backup-cross-region.sh` | Daily backup script |
| `scripts/restore-from-backup.sh` | Interactive restore tool |
| `k8s/manifests/backup-cronjob.yaml` | Kubernetes CronJob definition |

## Contact & Escalation

For critical DR situations:
1. Check [Exoscale Status](https://status.exoscale.com/)
2. Contact Exoscale support via console
3. Review this runbook and execute appropriate recovery procedure

---

*Last updated: December 2024*

























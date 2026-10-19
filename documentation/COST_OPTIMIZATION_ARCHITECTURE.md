# 💰 Low-Cost Infrastructure & Disaster Recovery Architecture

> **Target Monthly Cost**: **~38 CHF / month** (down from ~150 CHF / month, **~75% reduction**)  
> **Key Decisions**: Eliminate Kubernetes (SKS), NLB, and Managed DBaaS in favor of a single standalone Exoscale VM with local databases and automated Object Storage (SOS) cross-region backups.  
> **RTO (Recovery Time Objective)**: 15–30 minutes (well under the 1–2 hours tolerance)  
> **RPO (Recovery Point Objective)**: 12 hours (scheduled automated snapshots)

---

## 1. 📊 Cost Comparison & Financial Breakdown

| Component | SKS + DBaaS Architecture | Standalone VM Architecture | Savings |
|---|---|---|---|
| **Compute / Orchestration** | SKS Node (`standard.medium`: 2 vCPU, 4GB, 50GB) = **~33 CHF/mo** | Standalone VM (`standard.medium`: 2 vCPU, 4GB, 50GB) = **~33 CHF/mo** | 0 CHF |
| **Load Balancer** | Exoscale NLB = **~15 CHF/mo** | Direct Nginx on VM + Certbot SSL = **0 CHF** | **-15 CHF/mo** |
| **Relational Database** | Exoscale MySQL DBaaS (`hobbyist-2`) = **~44 CHF/mo** | Local MySQL on VM = **0 CHF** | **-44 CHF/mo** |
| **RAG / Vector Database** | Exoscale PostgreSQL DBaaS (`hobbyist-2`) = **~44 CHF/mo** | Local PostgreSQL + `pgvector` on VM = **0 CHF** | **-44 CHF/mo** |
| **Static IP Address** | Included in NLB | Exoscale Elastic IP = **~3.50 CHF/mo** | +3.50 CHF/mo |
| **Object Storage (SOS)** | Zurich (`ch-dk-2`) + Vienna (`at-vie-1`) = **~1.50 CHF/mo** | Zurich (`ch-dk-2`) + Vienna (`at-vie-1`) = **~1.50 CHF/mo** | 0 CHF |
| **Network Egress / Add-ons**| ~10 CHF/mo | ~1.00 CHF/mo | **-9 CHF/mo** |
| **TOTAL** | **~148–150 CHF / month** | **~38 CHF / month** | **~112 CHF / month (~75% reduction)** |

---

## 2. 🏗️ Architecture Design

```
                     ┌───────────────────────────────┐
                     │   Deflect CDN / Users         │
                     └──────────────┬────────────────┘
                                    │ HTTPS (443)
                                    ▼
         ┌───────────────────────────────────────────────────────────────┐
         │       Exoscale Standalone VM (standard.medium - 4GB RAM)      │
         │       Static Elastic IP (retained across any rebuild)         │
         │                                                               │
         │  ┌─────────────────────────────────────────────────────────┐  │
         │  │ Nginx (Static Frontend /var/www/html, Let's Encrypt SSL)│  │
         │  └──────┬──────────────────────┬───────────────────────────┘  │
         │         │ /api/                │                              │
         │         ▼                      ▼                              │
         │  ┌──────────────┐       ┌──────────────┐                      │
         │  │ FastAPI App  │       │ Worker       │                      │
         │  │ (port 8000)  │       │ (Doc / OCR)  │                      │
         │  └──────┬───────┘       └──────┬───────┘                      │
         │         │                      │                              │
         │         ▼                      ▼                              │
         │  ┌─────────────────────────────────────────────────────────┐  │
         │  │ Local MySQL 8.0 (3306) & Local PostgreSQL 16 (5432)     │  │
         │  │ (with pgvector extension enabled for RAG embeddings)    │  │
         │  └─────────────────────────────┬───────────────────────────┘  │
         └────────────────────────────────┼──────────────────────────────┘
                                          │
                    Twice-Daily Cron      │  Disaster Recovery Restore
                    (/opt/.../backup.sh)  ▼  (scripts/restore-from-backup.sh)
         ┌───────────────────────────────────────────────────────────────┐
         │     Exoscale Object Storage (SOS) S3-Compatible Buckets       │
         │      • Primary: foi-archive-terraform (Zurich)                │
         │      • DR Backup: foi-archive-dr (Vienna)                     │
         └───────────────────────────────────────────────────────────────┘
```

---

## 3. 💾 Data Protection & Disaster Recovery SLA

### Backup Flow (`scripts/backup-vm.sh`)
1. **Automated Schedule**: Runs every 12 hours (`0 2,14 * * *`) via `/etc/cron.d/haqnow-backup`.
2. **Database Dumps**:
   - `mysqldump` exports the entire `foi_archive` database with `--single-transaction --routines --triggers` and gzips it.
   - `pg_dump` exports the `rag_vectors` database with all vector embeddings and gzips it.
3. **Offsite Upload**: Uploaded directly to the Vienna SOS bucket (`s3://${DR_BUCKET}/backups/mysql/` and `s3://${DR_BUCKET}/backups/postgres/`).
4. **Retention**: Automatically purges dumps older than 30 days.

### Disaster Recovery Outage Scenario (Target RTO < 30 min)
If the virtual machine suffers catastrophic hardware failure or is corrupted:
1. **Step 1 (2 min)**: Run `terraform apply` in `terraform/`. It spins up a fresh Ubuntu 24.04 `standard.medium` instance and re-attaches the existing Elastic IP.
2. **Step 2 (3 min)**: `cloud-init.yml` automatically installs MySQL, PostgreSQL + `pgvector`, Python virtual environment, Nginx, and systemd units.
3. **Step 3 (5 min)**: Run the restore script:
   ```bash
   ./scripts/restore-from-backup.sh restore <latest-timestamp>
   ```
   This downloads the latest dumps from Vienna and populates both databases.
4. **Step 4 (1 min)**: Systemd services start and traffic resumes immediately. Because the Elastic IP is preserved, **DNS does not need to propagate**.
5. **Total Downtime**: **~15 to 25 minutes** (well within your 1–2 hour tolerance).

---

## 4. 🚀 Step-by-Step Migration Guide

### Step 1: Create a Final Backup of Current DBaaS Data
Before tearing down existing DBaaS and SKS clusters, create a full snapshot to the Vienna DR bucket:
```bash
# From local or worker pod with DBaaS network access:
./scripts/backup-vm.sh
```
Verify the backups exist:
```bash
./scripts/restore-from-backup.sh list
```

### Step 2: Apply the New Terraform Configuration
In `terraform/terraform.tfvars`:
```hcl
sks_enabled        = false
dbaas_enabled      = false
vm_enabled         = true
elastic_ip_enabled = true
instance_type      = "standard.medium"
```
Run Terraform:
```bash
cd terraform
terraform apply
```
*Terraform will allocate the Elastic IP and provision the standalone VM while tearing down the costly SKS node pool, NLB, and DBaaS instances.*

### Step 3: Populate Local Databases on the New VM
SSH into the new instance:
```bash
ssh root@<instance_ip>
```
Run the restore script to import the dumps:
```bash
/opt/foi-archive/scripts/restore-from-backup.sh restore <backup-date>
```

### Step 4: Deploy the Latest Code & Restart Services
From your local development machine:
```bash
./scripts/deploy.sh --env=prod --vm
```
Verify status on the server:
```bash
systemctl status foi-archive
systemctl status foi-archive-worker
systemctl status nginx
```

---

## 5. 🛠️ Daily Operations & Monitoring

- **Service Status**:
  ```bash
  systemctl status foi-archive foi-archive-worker nginx mysql postgresql
  ```
- **Live Logs**:
  ```bash
  journalctl -u foi-archive -f
  journalctl -u foi-archive-worker -f
  ```
- **Manual Backup**:
  ```bash
  /opt/foi-archive/scripts/backup-to-sos.sh
  ```
- **Check Backup Logs**:
  ```bash
  cat /var/log/foi/backup.log
  ```

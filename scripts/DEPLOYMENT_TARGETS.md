# 🚀 Deployment Targets Guide

HaqNow supports two deployment targets:

## 1. SKS (Kubernetes) - Recommended

**Auto-detection**: If `SKS_CLUSTER_ID` is set in `.env`, deployment automatically targets SKS.

**Manual override**:
```bash
./scripts/deploy.sh patch --sks
```

**Requirements**:
- Docker Desktop running
- SKS cluster created via Terraform
- Kubeconfig available at `k8s/.kubeconfig` (gitignored, contains sensitive credentials)

**What it does**:
1. Builds and pushes container images to Docker Hub
2. Updates Kubernetes secrets from `.env`
3. Deploys to SKS cluster
4. Tests deployment

## 2. VM (Legacy)

**Auto-detection**: If no `SKS_CLUSTER_ID` in `.env`, deployment targets VM.

**Manual override**:
```bash
./scripts/deploy.sh patch --vm
```

**Requirements**:
- SSH access to VM
- VM IP or domain in `SERVER_HOST`

**What it does**:
1. Builds frontend locally
2. Copies `.env` and frontend assets to VM
3. Updates code on VM
4. Restarts services

## Usage Examples

```bash
# Auto-detect (recommended)
./scripts/deploy.sh patch

# Explicit SKS deployment
./scripts/deploy.sh minor --sks

# Explicit VM deployment
./scripts/deploy.sh patch --vm

# With custom SERVER_HOST
SERVER_HOST=159.100.246.117 ./scripts/deploy.sh patch --sks
```

## Migration from VM to SKS

1. Create SKS infrastructure:
   ```bash
   ./k8s/scripts/migrate-with-terraform.sh
   ```

2. Add SKS config to `.env`:
   ```
   SKS_CLUSTER_ID=...
   SKS_NLB_IP=159.100.246.117
   ```

3. Deploy to SKS:
   ```bash
   ./scripts/deploy.sh patch
   ```

4. After verification, remove VM IP from `.env` and update DNS.


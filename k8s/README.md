# 🚀 SKS Migration Guide (Terraform-based)

This guide covers migrating HaqNow from VM-based deployment to Exoscale SKS using **Terraform** for infrastructure management.

## 📋 Prerequisites

- Exoscale API credentials in `.env` file
- `terraform` installed
- `kubectl` installed (already installed ✓)
- `docker` installed for building images
- `exo` CLI installed (for database updates)

## 🏗️ Architecture

- **SKS Cluster**: Starter tier (free)
- **Node Pool**: 2 nodes × standard.medium (2 vCPU, 4GB RAM each)
- **Containers**:
  - Backend API: 2 replicas
  - Worker: 2 replicas  
  - Frontend: 1 replica
- **Services**: ClusterIP for internal communication
- **Load Balancer**: Exoscale Network Load Balancer

## 📦 Files Created

### Terraform Configuration
- `terraform/sks.tf` - SKS cluster, node pool, security groups, NLB
- `terraform/sks_variables.tf` - SKS configuration variables
- `terraform/sks_outputs.tf` - Terraform outputs for SKS resources
- `terraform/terraform.tfvars.sks` - Example SKS configuration

### Dockerfiles
- `backend/Dockerfile` - Backend API container
- `backend/Dockerfile.worker` - Worker container
- `frontend/Dockerfile` - Frontend container
- `frontend/nginx.conf` - Nginx configuration

### Kubernetes Manifests
- `k8s/manifests/namespace.yaml` - Kubernetes namespace
- `k8s/manifests/configmap.yaml` - Non-sensitive configuration
- `k8s/manifests/secrets.yaml.template` - Template for secrets
- `k8s/manifests/backend-deployment.yaml` - Backend API deployment
- `k8s/manifests/worker-deployment.yaml` - Worker deployment
- `k8s/manifests/frontend-deployment.yaml` - Frontend deployment
- `k8s/manifests/ingress.yaml` - Ingress configuration

### Scripts
- `k8s/scripts/migrate-with-terraform.sh` - **Main migration script (uses Terraform)**
- `k8s/scripts/build-and-push-images.sh` - Build and push images to CRS
- `k8s/scripts/create-secrets.sh` - Create Kubernetes secrets from .env
- `k8s/scripts/update-database-ips-terraform.sh` - Update database IP filters
- `k8s/scripts/deploy.sh` - Deploy application to SKS
- `k8s/scripts/test-deployment.sh` - Test deployment

## 🚀 Migration Steps

### Step 1: Enable SKS in Terraform

Add SKS configuration to `terraform/terraform.tfvars`:

```hcl
# SKS Configuration
sks_enabled = true
sks_k8s_version = "1.34.2"
sks_service_level = "starter"
sks_cni = "calico"
sks_node_instance_type = "standard.medium"
sks_node_count = 2
sks_anti_affinity = true
sks_auto_upgrade = false
```

### Step 2: Create SKS Infrastructure with Terraform

```bash
cd /Users/salman/Documents/fadih
./k8s/scripts/migrate-with-terraform.sh
```

This will:
- Initialize Terraform
- Plan the deployment
- Create SKS cluster, security group, node pool, and NLB
- Generate kubeconfig
- Save node IPs for database whitelist

**Expected time**: 10-15 minutes

### Step 3: Update Database IP Filters

```bash
./k8s/scripts/update-database-ips-terraform.sh
```

This uses Terraform outputs to get node IPs and updates both MySQL and PostgreSQL database IP filters.

### Step 4: Build and Push Container Images

```bash
./k8s/scripts/build-and-push-images.sh
```

Builds and pushes:
- `backend-api:latest`
- `worker:latest`
- `frontend:latest`

**Expected time**: 5-10 minutes

### Step 5: Create Kubernetes Secrets

```bash
./k8s/scripts/create-secrets.sh
```

Creates Kubernetes secrets from your `.env` file.

### Step 6: Deploy Application

```bash
./k8s/scripts/deploy.sh
```

Deploys all Kubernetes manifests and waits for pods to be ready.

**Expected time**: 2-5 minutes

### Step 7: Test Deployment

```bash
./k8s/scripts/test-deployment.sh
```

Runs basic health checks and shows pod/service status.

### Step 8: Run Playwright E2E Tests

```bash
cd frontend
npm run test:e2e
```

### Step 9: Configure NLB and Update DNS

After deployment is verified:

```bash
# Get NLB IP from Terraform
cd terraform
terraform output sks_nlb_ip

# Update DNS to point www.haqnow.com to NLB IP
```

### Step 10: Create VM Snapshot (Rollback Safety)

```bash
# Via Terraform or Exoscale console
# Get VM ID from Terraform output
terraform output instance_id

# Create snapshot via Exoscale CLI or console
```

### Step 11: Delete Old VM (After Verification)

```bash
# Only after confirming SKS deployment works
# Comment out or remove compute instance in terraform/main.tf
# Then run: terraform apply
```

## 🔍 Verification Checklist

- [ ] Terraform plan shows SKS resources
- [ ] SKS cluster created and running
- [ ] Node pool has 2 nodes in running state
- [ ] Database IP filters updated
- [ ] Container images built and pushed
- [ ] Kubernetes secrets created
- [ ] All pods running (backend-api, worker, frontend)
- [ ] Health endpoint responds: `/health`
- [ ] Backend API accessible
- [ ] Frontend accessible
- [ ] Playwright e2e tests pass
- [ ] NLB configured and DNS updated
- [ ] VM snapshot created
- [ ] Old VM deleted

## 🛠️ Troubleshooting

### Terraform errors

```bash
cd terraform
terraform init -upgrade
terraform validate
terraform plan
```

### Pods not starting

```bash
export KUBECONFIG=$(terraform output -raw sks_kubeconfig_path)  # Points to k8s/.kubeconfig (gitignored)
kubectl describe pod <pod-name> -n haqnow
kubectl logs <pod-name> -n haqnow
```

### Database connection issues

```bash
# Verify database IP filters
terraform output sks_node_ips

# Check database configuration
exo dbaas show foi-archive-mysql-production -z ch-dk-2
exo dbaas show foi-archive-postgres-rag-production -z ch-dk-2
```

## 📊 Resource Allocation

### Per Node (standard.medium: 2 vCPU, 4GB RAM)

- **Backend API** (×2 replicas): 800m CPU, 1.5GB RAM
- **Worker** (×2 replicas): 1000m CPU, 2GB RAM
- **Frontend** (×1 replica): 100m CPU, 256MB RAM
- **System overhead**: ~500MB RAM

**Total per node**: ~2 vCPU, ~4GB RAM (fully utilized)

## 💰 Cost Breakdown

- SKS Cluster (Starter): $0/month
- Node Pool (2 × standard.medium): $56/month
- Network Load Balancer: $15/month
- Container Registry: $5/month
- **Subtotal**: $76/month
- Databases (unchanged): $92/month
- **Total**: ~$168/month

## 🔄 Rollback Procedure

If migration fails:

1. **Quick rollback**: Switch DNS back to VM IP (194.182.164.77)
2. **Terraform rollback**: 
   ```bash
   cd terraform
   # Set sks_enabled = false in terraform.tfvars
   terraform apply
   ```
3. **Full rollback**: Restore VM from snapshot

## 📚 Additional Resources

- [Exoscale SKS Documentation](https://www.exoscale.com/sks/)
- [Exoscale Terraform Provider](https://registry.terraform.io/providers/exoscale/exoscale/latest/docs)
- [Kubernetes Documentation](https://kubernetes.io/docs/)

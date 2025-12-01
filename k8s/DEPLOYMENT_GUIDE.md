# 🚀 SKS Deployment Guide

Complete guide for deploying HaqNow to Exoscale SKS.

## ✅ Pre-Deployment Checklist

- [x] SKS cluster created via Terraform
- [x] Database IP filters updated
- [x] Kubernetes secrets created
- [x] ConfigMap created
- [x] Manifests prepared
- [ ] Docker daemon running
- [ ] Container images built and pushed
- [ ] Application deployed
- [ ] Tests passing

## 📋 Step-by-Step Deployment

### Step 1: Start Docker Desktop

```bash
# On macOS, open Docker Desktop application
open -a Docker
# Wait for Docker to fully start (whale icon in menu bar)
```

### Step 2: Build and Push Container Images

```bash
cd /Users/salman/Documents/fadih

# Set Docker Hub username (or use default: haqnow)
export DOCKER_USER="haqnow"

# Optional: Set Docker Hub password for private images
# export DOCKER_PASSWORD="your_password"

# Build and push all images
./k8s/scripts/build-and-push-images.sh
```

**Expected output:**
- ✅ Backend API image pushed
- ✅ Worker image pushed  
- ✅ Frontend image pushed

**Time:** 5-10 minutes

### Step 3: Deploy Application to SKS

```bash
# Ensure kubeconfig is set (gitignored, contains sensitive credentials)
export KUBECONFIG="$(pwd)/k8s/.kubeconfig"

# Deploy all components
./scripts/deploy.sh --sks
```

**This will:**
1. Create namespace (if not exists)
2. Apply ConfigMap
3. Create/update secrets
4. Deploy backend API (2 replicas)
5. Deploy worker (2 replicas)
6. Deploy frontend (1 replica)
7. Wait for deployments to be ready

**Time:** 2-5 minutes

### Step 4: Verify Deployment

```bash
# Check pod status
kubectl get pods -n haqnow

# Check services
kubectl get services -n haqnow

# Run test script
./k8s/scripts/test-deployment.sh
```

**Expected pod status:** All pods should be `Running` and `Ready`

### Step 5: Test Health Endpoints

```bash
# Port forward to backend
kubectl port-forward -n haqnow service/backend-service 8000:8000 &

# Test health endpoint
curl http://localhost:8000/health

# Stop port forward
kill %1
```

### Step 6: Run Playwright E2E Tests

```bash
cd frontend

# Update test configuration to use SKS endpoints
# Then run tests
npm run test:e2e
```

## 🔧 Configuration

### Environment Variables

All secrets are stored in `.env` and loaded into Kubernetes secrets:

```bash
# View current secrets
kubectl get secret haqnow-secrets -n haqnow -o yaml

# Update secrets (after changing .env)
./k8s/scripts/create-secrets.sh
```

### SKS Configuration (in .env)

```
SKS_CLUSTER_ID=4768d21b-8a7a-495d-8ae0-0ec1b88137d7
SKS_CLUSTER_NAME=foi-archive-sks-production
SKS_NLB_IP=159.100.246.117
SKS_NODE_IPS=194.182.164.188,159.100.254.32
```

## 🌐 Network Load Balancer Setup

The NLB is created via Terraform. To configure services:

```bash
# Get NLB IP
terraform -chdir=terraform output sks_nlb_ip

# Update DNS to point www.haqnow.com to NLB IP: 159.100.246.117
```

**Note:** NLB services need to be configured to point to NodePort services or use Exoscale CCM integration.

## 📊 Resource Allocation

### Per Node (standard.medium: 2 vCPU, 4GB RAM)

- **Backend API** (×2): 800m CPU, 1.5GB RAM
- **Worker** (×2): 1000m CPU, 2GB RAM
- **Frontend** (×1): 100m CPU, 256MB RAM
- **System overhead**: ~500MB RAM

**Total:** ~2 vCPU, ~4GB RAM per node (fully utilized)

## 🐛 Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n haqnow

# Check logs
kubectl logs <pod-name> -n haqnow

# Check events
kubectl get events -n haqnow --sort-by='.lastTimestamp'
```

### Image Pull Errors

```bash
# Verify images exist
docker pull docker.io/haqnow/backend-api:latest
docker pull docker.io/haqnow/worker:latest
docker pull docker.io/haqnow/frontend:latest

# Check image pull secrets
kubectl get secrets -n haqnow
```

### Database Connection Issues

```bash
# Verify database IP filters include SKS node IPs
terraform -chdir=terraform output sks_node_ips

# Update database IP filters
./k8s/scripts/update-database-ips-terraform.sh
```

### Service Not Accessible

```bash
# Check service endpoints
kubectl get endpoints -n haqnow

# Test service from within cluster
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- curl http://backend-service.haqnow.svc.cluster.local:8000/health
```

## 🔄 Rollback Procedure

If deployment fails:

1. **Delete deployments:**
   ```bash
   kubectl delete deployment backend-api worker frontend -n haqnow
   ```

2. **Revert to VM:**
   - Switch DNS back to VM IP: 194.182.164.77
   - VM is still running and accessible

3. **Terraform rollback:**
   ```bash
   cd terraform
   # Set sks_enabled = false in terraform.tfvars
   terraform apply
   ```

## 📈 Scaling

### Manual Scaling

```bash
# Scale backend API
kubectl scale deployment backend-api --replicas=4 -n haqnow

# Scale worker
kubectl scale deployment worker --replicas=4 -n haqnow
```

### Auto-scaling (Future)

Configure Horizontal Pod Autoscaler (HPA) for automatic scaling based on CPU/memory usage.

## 💰 Cost Breakdown

- SKS Cluster (Starter): $0/month
- Node Pool (2 × standard.medium): $56/month
- Network Load Balancer: $15/month
- Container Registry (Docker Hub): $0/month (public)
- **Subtotal**: $71/month
- Databases (unchanged): $92/month
- **Total**: ~$163/month

## 📚 Additional Resources

- [Exoscale SKS Documentation](https://www.exoscale.com/sks/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Terraform Exoscale Provider](https://registry.terraform.io/providers/exoscale/exoscale/latest/docs)


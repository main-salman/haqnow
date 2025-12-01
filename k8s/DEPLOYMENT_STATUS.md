# 🚀 SKS Deployment Status

## ✅ Infrastructure Ready

- **SKS Cluster**: foi-archive-sks-production
- **Nodes**: 2 nodes (standard.medium) - Both Ready
- **Network Load Balancer**: 159.100.246.117
- **Security Groups**: Configured
- **Database IP Filters**: Updated

## ✅ Kubernetes Setup Complete

- **Namespace**: haqnow ✓
- **Secrets**: Created (46 keys) ✓
- **ConfigMap**: Created (8 keys) ✓
- **Manifests**: Prepared ✓

## ✅ Configuration Complete

- **SKS secrets**: Stored in .env ✓
- **DNS IP**: 159.100.246.117 ✓
- **Deployment scripts**: Updated ✓
- **Documentation**: Complete ✓

## ⏸️ Waiting For

- **Docker Desktop**: Must be running to build/push images

## 📋 Deployment Steps (When Docker is Running)

### Option 1: Auto-Deploy (Recommended)

```bash
./scripts/deploy.sh patch
```

This will:
1. Auto-detect SKS deployment (from SKS_CLUSTER_ID in .env)
2. Build and push container images
3. Update Kubernetes secrets
4. Deploy to SKS cluster
5. Test deployment

### Option 2: Manual Steps

```bash
# 1. Build and push images
export DOCKER_USER="haqnow"
./k8s/scripts/build-and-push-images.sh

# 2. Update secrets (if .env changed)
./k8s/scripts/create-secrets.sh

# 3. Deploy application
./scripts/deploy.sh --sks

# 4. Test deployment
./k8s/scripts/test-deployment.sh
```

## 🔍 Verification Commands

```bash
# Check cluster status
export KUBECONFIG="$(pwd)/k8s/.kubeconfig"
kubectl get nodes
kubectl get pods -n haqnow
kubectl get services -n haqnow

# Check logs
kubectl logs -n haqnow -l app=backend-api --tail=50
kubectl logs -n haqnow -l app=worker --tail=50
kubectl logs -n haqnow -l app=frontend --tail=50

# Test health endpoint
kubectl port-forward -n haqnow service/backend-service 8000:8000 &
curl http://localhost:8000/health
```

## 📊 Expected Resources

After deployment:
- **Backend API**: 2 pods
- **Worker**: 2 pods
- **Frontend**: 1 pod
- **Services**: 3 ClusterIP services

## 🌐 DNS Update

Once deployment is verified:
1. Update DNS A records:
   - www.haqnow.com → 159.100.246.117
   - haqnow.com → 159.100.246.117
2. Wait for DNS propagation
3. Test endpoints
4. Run Playwright e2e tests

## 🐛 Troubleshooting

### Images Not Pulling

```bash
# Verify images exist
docker pull docker.io/haqnow/backend-api:latest
docker pull docker.io/haqnow/worker:latest
docker pull docker.io/haqnow/frontend:latest
```

### Pods Not Starting

```bash
# Check pod events
kubectl describe pod <pod-name> -n haqnow

# Check logs
kubectl logs <pod-name> -n haqnow
```

### Database Connection Issues

```bash
# Verify database IP filters
./k8s/scripts/update-database-ips-terraform.sh
```


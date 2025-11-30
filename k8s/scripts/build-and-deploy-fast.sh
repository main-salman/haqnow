#!/bin/bash
# Fast build and deploy - optimized for speed

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

cd "$(dirname "$0")/../.."

# Get credentials
GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" .env | cut -d'=' -f2 | sed 's/#.*$//' | tr -d ' ')
GITHUB_USER="main-salman"

echo -e "${GREEN}🚀 Fast Build & Deploy${NC}"
echo ""

# Login
echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_USER" --password-stdin > /dev/null 2>&1

# Build backend (with progress)
echo -e "${YELLOW}Building backend (linux/amd64)...${NC}"
cd backend
docker buildx build --platform linux/amd64 \
  --load \
  -f Dockerfile \
  -t ghcr.io/main-salman/backend-api:latest . > /tmp/backend-build.log 2>&1 &
BACKEND_PID=$!

# Build worker in parallel
echo -e "${YELLOW}Building worker (linux/amd64)...${NC}"
docker buildx build --platform linux/amd64 \
  --load \
  -f Dockerfile.worker \
  -t ghcr.io/main-salman/worker:latest . > /tmp/worker-build.log 2>&1 &
WORKER_PID=$!

# Wait for builds
echo "Waiting for builds to complete..."
wait $BACKEND_PID && echo -e "${GREEN}✅ Backend built${NC}" || { echo -e "${RED}❌ Backend build failed${NC}"; exit 1; }
wait $WORKER_PID && echo -e "${GREEN}✅ Worker built${NC}" || { echo -e "${RED}❌ Worker build failed${NC}"; exit 1; }

# Push images
echo -e "${YELLOW}Pushing images...${NC}"
docker push ghcr.io/main-salman/backend-api:latest &
docker push ghcr.io/main-salman/worker:latest &
wait
echo -e "${GREEN}✅ Images pushed${NC}"

# Deploy
echo -e "${YELLOW}Deploying to Kubernetes...${NC}"
export KUBECONFIG="$(pwd)/k8s/.kubeconfig"
kubectl delete pods -n haqnow --all --wait=false
sleep 5
kubectl get pods -n haqnow -w



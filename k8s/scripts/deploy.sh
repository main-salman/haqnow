#!/bin/bash
# Deploy application to SKS cluster

set -e

# Set default registry and docker user if not provided
export REGISTRY="${REGISTRY:-docker.io}"
export DOCKER_USER="${DOCKER_USER:-haqnow}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

K8S_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../manifests" && pwd)"

if ! kubectl cluster-info &>/dev/null; then
    echo "Error: kubectl not configured. Please run migrate-to-sks.sh first"
    exit 1
fi

echo -e "${GREEN}🚀 Deploying application to SKS cluster${NC}"
echo ""

# Apply manifests in order
echo -e "${YELLOW}Creating namespace...${NC}"
kubectl apply -f "$K8S_DIR/namespace.yaml"

echo -e "${YELLOW}Creating ConfigMap...${NC}"
kubectl apply -f "$K8S_DIR/configmap.yaml"

echo -e "${YELLOW}Creating Secrets...${NC}"
"$(dirname "$0")/create-secrets.sh"

# Set defaults for registry and docker user if not provided
export REGISTRY="${REGISTRY:-docker.io}"
export DOCKER_USER="${DOCKER_USER:-haqnow}"

echo -e "${YELLOW}Using registry: ${REGISTRY}${NC}"
echo -e "${YELLOW}Using docker user: ${DOCKER_USER}${NC}"
echo ""

# Check if envsubst is available, otherwise use sed
if command -v envsubst &> /dev/null; then
    echo -e "${YELLOW}Deploying backend API...${NC}"
    envsubst < "$K8S_DIR/backend-deployment.yaml" | kubectl apply -f -
    
    echo -e "${YELLOW}Deploying worker...${NC}"
    envsubst < "$K8S_DIR/worker-deployment.yaml" | kubectl apply -f -
    
    echo -e "${YELLOW}Deploying frontend...${NC}"
    envsubst < "$K8S_DIR/frontend-deployment.yaml" | kubectl apply -f -
else
    # Fallback to sed if envsubst not available
    echo -e "${YELLOW}Deploying backend API...${NC}"
    sed "s|\${REGISTRY:-docker.io}|${REGISTRY}|g; s|\${DOCKER_USER:-haqnow}|${DOCKER_USER}|g" "$K8S_DIR/backend-deployment.yaml" | kubectl apply -f -
    
    echo -e "${YELLOW}Deploying worker...${NC}"
    sed "s|\${REGISTRY:-docker.io}|${REGISTRY}|g; s|\${DOCKER_USER:-haqnow}|${DOCKER_USER}|g" "$K8S_DIR/worker-deployment.yaml" | kubectl apply -f -
    
    echo -e "${YELLOW}Deploying frontend...${NC}"
    sed "s|\${REGISTRY:-docker.io}|${REGISTRY}|g; s|\${DOCKER_USER:-haqnow}|${DOCKER_USER}|g" "$K8S_DIR/frontend-deployment.yaml" | kubectl apply -f -
fi

echo -e "${YELLOW}Waiting for deployments to be ready...${NC}"
kubectl wait --for=condition=available --timeout=300s deployment/backend-api -n haqnow || true
kubectl wait --for=condition=available --timeout=300s deployment/worker -n haqnow || true
kubectl wait --for=condition=available --timeout=300s deployment/frontend -n haqnow || true

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "Check status with:"
echo "  kubectl get pods -n haqnow"
echo "  kubectl get services -n haqnow"

